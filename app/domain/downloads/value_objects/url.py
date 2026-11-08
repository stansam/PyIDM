"""Download URL value object with validation and normalization."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from app.domain.exceptions.domain_errors import InvalidUrlError


@dataclass(frozen=True, slots=True)
class DownloadUrl:
    """Validated HTTP or HTTPS URL."""

    raw: str
    scheme: str
    host: str
    path: str

    @classmethod
    def parse(cls, raw_url: str) -> DownloadUrl:
        cleaned = raw_url.strip()
        if not cleaned:
            raise InvalidUrlError(raw_url, "URL cannot be empty")

        parsed = urlparse(cleaned)
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            raise InvalidUrlError(
                raw_url, f"Unsupported scheme '{scheme}'. Only HTTP and HTTPS are permitted."
            )

        if not parsed.netloc:
            raise InvalidUrlError(raw_url, "Missing host component")

        return cls(
            raw=cleaned,
            scheme=scheme,
            host=parsed.netloc,
            path=parsed.path,
        )

