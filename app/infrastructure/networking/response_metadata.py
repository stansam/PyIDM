"""HTTP response representation returned by stream clients."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.downloads.value_objects.headers import HttpHeaders


@dataclass(frozen=True, slots=True)
class HttpResponseMetadata:
    """Parsed HTTP response headers and status attributes."""

    status_code: int
    headers: HttpHeaders
    final_url: str
    content_length: int | None = None
    accept_ranges: bool = False
    etag: str | None = None
    last_modified: str | None = None
    content_type: str | None = None
    content_disposition: str | None = None

    @classmethod
    def from_headers(cls, status_code: int, headers: dict[str, str], final_url: str) -> HttpResponseMetadata:
        h = HttpHeaders(headers)
        cl_str = h.get("content-length")
        content_len = int(cl_str) if cl_str and cl_str.isdigit() else None

        ar_raw = h.get("accept-ranges")
        ar_str = ar_raw.lower() if ar_raw else ""
        accept_ranges = "bytes" in ar_str

        return cls(
            status_code=status_code,
            headers=h,
            final_url=final_url,
            content_length=content_len,
            accept_ranges=accept_ranges,
            etag=h.get("etag"),
            last_modified=h.get("last-modified"),
            content_type=h.get("content-type"),
            content_disposition=h.get("content-disposition"),
        )

