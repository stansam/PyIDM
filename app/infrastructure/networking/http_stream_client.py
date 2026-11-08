"""HTTP streaming network client using HTTPX."""

from __future__ import annotations

from collections.abc import Iterator

import httpx

from app.domain.downloads.value_objects.headers import HttpHeaders
from app.infrastructure.networking.response_metadata import HttpResponseMetadata
from app.shared.constants import (
    DEFAULT_CHUNK_SIZE_BYTES,
    DEFAULT_CONNECT_TIMEOUT_SEC,
    DEFAULT_READ_TIMEOUT_SEC,
    DEFAULT_USER_AGENT,
    MAX_REDIRECTS,
)


class HttpStreamClient:
    """Thread-safe HTTP client providing streaming responses and capability inspection."""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT_SEC,
        read_timeout: float = DEFAULT_READ_TIMEOUT_SEC,
        max_connections: int = 100,
        max_keepalive: int = 20,
    ) -> None:
        self._timeout = httpx.Timeout(
            connect=connect_timeout,
            read=read_timeout,
            write=15.0,
            pool=10.0,
        )
        self._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive,
            keepalive_expiry=10.0,
        )
        self._client = httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=self._timeout,
            limits=self._limits,
            follow_redirects=True,
            max_redirects=MAX_REDIRECTS,
        )

    def inspect(self, url: str, custom_headers: HttpHeaders | None = None) -> HttpResponseMetadata:
        """Send HEAD or probe GET request to determine resource metadata."""
        headers = custom_headers.to_dict() if custom_headers else {}
        try:
            resp = self._client.head(url, headers=headers)
            if resp.status_code in (200, 206) and "content-length" in resp.headers:
                return HttpResponseMetadata.from_headers(
                    resp.status_code, dict(resp.headers), str(resp.url)
                )
        except Exception:
            pass

        # Fallback to a single-byte probe range request
        probe_headers = dict(headers)
        probe_headers["Range"] = "bytes=0-0"
        with self._client.stream("GET", url, headers=probe_headers) as probe_resp:
            meta = HttpResponseMetadata.from_headers(
                probe_resp.status_code, dict(probe_resp.headers), str(probe_resp.url)
            )
            # If server returned 206 with Content-Range "bytes 0-0/TOTAL"
            cr = probe_resp.headers.get("content-range")
            if cr and "/" in cr:
                total_part = cr.split("/")[1]
                if total_part.isdigit():
                    return HttpResponseMetadata(
                        status_code=probe_resp.status_code,
                        headers=meta.headers,
                        final_url=meta.final_url,
                        content_length=int(total_part),
                        accept_ranges=True,
                        etag=meta.etag,
                        last_modified=meta.last_modified,
                        content_type=meta.content_type,
                        content_disposition=meta.content_disposition,
                    )
            return meta

    def stream_range(
        self,
        url: str,
        start_byte: int,
        end_byte: int,
        custom_headers: HttpHeaders | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE_BYTES,
    ) -> Iterator[bytes]:
        """Stream chunks for an inclusive byte range [start_byte, end_byte]."""
        headers = custom_headers.to_dict() if custom_headers else {}
        headers["Range"] = f"bytes={start_byte}-{end_byte}"

        with self._client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()
            for chunk in response.iter_bytes(chunk_size=chunk_size):
                if chunk:
                    yield chunk

    def stream_full(
        self,
        url: str,
        custom_headers: HttpHeaders | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE_BYTES,
    ) -> Iterator[bytes]:
        """Stream chunks for a single-connection full resource download."""
        headers = custom_headers.to_dict() if custom_headers else {}
        with self._client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()
            for chunk in response.iter_bytes(chunk_size=chunk_size):
                if chunk:
                    yield chunk

    def close(self) -> None:
        """Close connection pool and release resources."""
        self._client.close()

