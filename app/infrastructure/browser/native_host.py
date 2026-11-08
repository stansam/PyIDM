"""Native Messaging stdio host communication layer for WebExtensions."""

from __future__ import annotations

import json
import logging
import os
import struct
import sys
import threading
from collections.abc import Mapping
from typing import IO

from app.application.container import Container
from app.domain.downloads.entities.download import Download
from app.domain.downloads.services.filename_resolver import FilenameResolver
from app.domain.downloads.value_objects.headers import HttpHeaders
from app.domain.downloads.value_objects.ids import create_download_id
from app.domain.downloads.value_objects.url import DownloadUrl
from app.engine.media.manifest_parser import ManifestParser
from app.engine.media.models import MediaVariant

logger = logging.getLogger("PyIDM.NativeHost")

# Set binary mode on Windows to prevent \n <-> \r\n translation from corrupting length headers
if sys.platform == "win32":
    import msvcrt

    try:
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    except Exception:
        pass


class NativeMessagingHost:
    """Implements WebExtensions Native Messaging standard protocol over stdin/stdout."""

    def __init__(
        self,
        container: Container,
        in_stream: IO[bytes] | None = None,
        out_stream: IO[bytes] | None = None,
    ) -> None:
        self.container = container
        self.in_stream: IO[bytes] = in_stream or sys.stdin.buffer
        self.out_stream: IO[bytes] = out_stream or sys.stdout.buffer
        self._write_lock = threading.Lock()
        self._stop_event = threading.Event()

    def read_message(self) -> dict[str, object] | None:
        """Read a single length-prefixed JSON message from the input stream."""
        raw_length = self.in_stream.read(4)
        if not raw_length or len(raw_length) < 4:
            return None  # Stream closed / EOF

        message_length = struct.unpack("@I", raw_length)[0]
        if message_length == 0 or message_length > 64 * 1024 * 1024:  # 64 MB guard
            logger.warning("Invalid native messaging payload length: %d", message_length)
            return None

        raw_payload = self.in_stream.read(message_length)
        if len(raw_payload) < message_length:
            return None

        try:
            parsed: object = json.loads(raw_payload.decode("utf-8"))
            if isinstance(parsed, dict):
                return {str(k): v for k, v in parsed.items()}
            return {"raw_content": parsed}
        except Exception as ex:
            logger.error("Failed to parse native message JSON: %s", ex)
            return None

    def send_message(self, message: Mapping[str, object]) -> bool:
        """Send a length-prefixed UTF-8 JSON message to the output stream."""
        try:
            encoded = json.dumps(message, separators=(",", ":")).encode("utf-8")
            length_prefix = struct.pack("@I", len(encoded))
            with self._write_lock:
                self.out_stream.write(length_prefix + encoded)
                self.out_stream.flush()
            return True
        except Exception as ex:
            logger.error("Failed to write native message: %s", ex)
            return False

    def handle_message(self, message: Mapping[str, object]) -> dict[str, object]:
        """Dispatch a single parsed native message to the appropriate handler."""
        msg_type = str(message.get("type", "")).upper()
        request_id = message.get("request_id")

        if msg_type == "GET_STATUS" or msg_type == "PING":
            return {
                "type": "STATUS_RESPONSE",
                "request_id": request_id,
                "status": "ready",
                "app": "PyIDM",
                "version": "0.1.0",
                "active_downloads": self.container.download_manager.get_active_count(),
            }

        elif msg_type in ("ENQUEUE_MEDIA_DOWNLOAD", "ENQUEUE_DOWNLOAD", "DOWNLOAD_REQUEST"):
            return self._handle_enqueue(message)

        elif msg_type == "PARSE_MANIFEST":
            return self._handle_parse_manifest(message)

        else:
            return {
                "type": "ERROR",
                "request_id": request_id,
                "error": f"Unknown message type: {msg_type}",
            }

    def _handle_enqueue(self, message: Mapping[str, object]) -> dict[str, object]:
        request_id = message.get("request_id")
        raw_url = str(message.get("url", "")).strip()

        if not raw_url:
            return {
                "type": "DOWNLOAD_REJECTED",
                "request_id": request_id,
                "reason": "Missing URL parameter",
            }

        try:
            url = DownloadUrl.parse(raw_url)
        except Exception as ex:
            return {
                "type": "DOWNLOAD_REJECTED",
                "request_id": request_id,
                "reason": f"Invalid URL: {ex}",
            }

        # Parse request headers
        raw_headers = message.get("headers")
        custom_headers = (
            HttpHeaders({str(k): str(v) for k, v in raw_headers.items()})
            if isinstance(raw_headers, Mapping)
            else HttpHeaders()
        )

        # Cookie header handling
        cookies = message.get("cookies")
        if isinstance(cookies, str) and cookies.strip():
            custom_headers = custom_headers.with_header("Cookie", cookies.strip())

        # Referer header handling
        page_url = message.get("page_url")
        if isinstance(page_url, str) and page_url.strip() and not custom_headers.get("referer"):
            custom_headers = custom_headers.with_header("Referer", page_url.strip())

        # Resolve filename
        suggested_title = message.get("title")
        container = str(message.get("container", "mp4")).strip().lstrip(".")
        if suggested_title:
            cleaned_title = str(suggested_title).strip()
            if not cleaned_title.lower().endswith(f".{container.lower()}"):
                cleaned_title = f"{cleaned_title}.{container}"
        else:
            cleaned_title = None

        existing_names = {
            d.filename for d in self.container.download_repo.get_all()
        }
        filename = FilenameResolver.resolve(cleaned_title, url, existing_names)

        # 1. Forward to running PyIDM desktop GUI if active
        api_port = self.container.settings.api_port
        api_url = f"http://127.0.0.1:{api_port}/api/v1/downloads"
        secret = self.container.settings.api_secret_key

        try:
            forward_payload = {
                "url": url.raw,
                "filename": filename,
                "headers": custom_headers.to_dict(),
                "page_url": page_url,
                "size_str": str(message.get("quality", "")),
            }
            resp = self.container.http_client._client.post(
                api_url,
                json=forward_payload,
                headers={"X-PyIDM-Key": secret, "Host": f"127.0.0.1:{api_port}"},
                timeout=1.0,
            )
            if resp.status_code == 200:
                resp_json: dict[str, object] = resp.json()
                return {
                    "type": "DOWNLOAD_ACCEPTED",
                    "request_id": request_id,
                    "download_id": str(resp_json.get("download_id", "")),
                    "filename": filename,
                    "status": "PROMPTED" if resp_json.get("status") == "prompted" else "DOWNLOADING",
                }
        except Exception:
            pass

        # 2. Standalone fallback if desktop GUI is not running
        download = Download(
            id=create_download_id(),
            url=url,
            destination_directory=self.container.settings.download_dir,
            filename=filename,
            custom_headers=custom_headers,
            connection_count=self.container.settings.default_connections,
        )

        self.container.download_repo.save(download)
        self.container.download_manager.start_download(download.id)

        return {
            "type": "DOWNLOAD_ACCEPTED",
            "request_id": request_id,
            "download_id": str(download.id),
            "filename": filename,
            "status": "DOWNLOADING",
        }

    def _handle_parse_manifest(self, message: Mapping[str, object]) -> dict[str, object]:
        request_id = message.get("request_id")
        manifest_url = str(message.get("url", "")).strip()
        manifest_content = str(message.get("content", ""))

        if not manifest_url and not manifest_content:
            return {
                "type": "ERROR",
                "request_id": request_id,
                "error": "No manifest URL or content provided",
            }

        # If URL was provided without content, fetch it
        if not manifest_content and manifest_url:
            try:
                headers = HttpHeaders({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                chunks = list(self.container.http_client.stream_full(manifest_url, headers))
                manifest_content = b"".join(chunks).decode("utf-8", errors="replace")
            except Exception as ex:
                logger.warning("Failed to fetch manifest at %s: %s", manifest_url, ex)

        variants: list[MediaVariant] = []
        if ManifestParser.is_hls(manifest_content or manifest_url):
            variants = ManifestParser.parse_hls(manifest_content, base_url=manifest_url)
        elif ManifestParser.is_dash(manifest_content or manifest_url):
            variants = ManifestParser.parse_dash(manifest_content, base_url=manifest_url)

        return {
            "type": "MANIFEST_VARIANTS",
            "request_id": request_id,
            "url": manifest_url,
            "variants": [
                {
                    "id": v.id,
                    "url": v.url,
                    "quality_label": v.quality_label,
                    "container": v.container,
                    "resolution": v.resolution,
                    "bitrate_bps": v.bitrate_bps,
                    "display_title": v.display_title,
                    "is_audio_only": v.is_audio_only,
                    "is_drm_protected": v.is_drm_protected,
                }
                for v in variants
            ],
        }

    def run_loop(self) -> None:
        """Continuous event loop reading from stdin and replying on stdout."""
        while not self._stop_event.is_set():
            message = self.read_message()
            if message is None:
                break  # EOF / parent browser closed connection
            response = self.handle_message(message)
            self.send_message(response)

