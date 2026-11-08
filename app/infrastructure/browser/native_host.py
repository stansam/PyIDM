"""Native Messaging stdio host communication layer for WebExtensions."""

from __future__ import annotations

import json
import logging
import os
import struct
import sys
import threading
from typing import IO, Any

from app.application.container import Container
from app.domain.downloads.entities.download import Download
from app.domain.downloads.services.filename_resolver import FilenameResolver
from app.domain.downloads.value_objects.headers import HttpHeaders
from app.domain.downloads.value_objects.ids import create_download_id
from app.domain.downloads.value_objects.url import DownloadUrl
from app.engine.media.manifest_parser import ManifestParser

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

    def read_message(self) -> dict[str, Any] | None:
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
                return parsed
            return {"raw_content": parsed}
        except Exception as ex:
            logger.error("Failed to parse native message JSON: %s", ex)
            return None

    def send_message(self, message: dict[str, Any]) -> bool:
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

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any]:
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

    def _handle_enqueue(self, message: dict[str, Any]) -> dict[str, Any]:
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
            HttpHeaders(raw_headers)
            if isinstance(raw_headers, dict)
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

    def _handle_parse_manifest(self, message: dict[str, Any]) -> dict[str, Any]:
        request_id = message.get("request_id")
        manifest_url = str(message.get("url", "")).strip()
        manifest_content = str(message.get("content", ""))

        if not manifest_url and not manifest_content:
            return {
                "type": "ERROR",
                "request_id": request_id,
                "error": "No manifest URL or content provided",
            }

        variants = []
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

