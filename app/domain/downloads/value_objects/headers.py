"""HTTP headers wrapper with case-insensitive lookup and immutability."""

from __future__ import annotations

from collections.abc import Iterable, Mapping


class HttpHeaders:
    """Immutable case-insensitive HTTP headers container."""

    def __init__(self, headers: Mapping[str, str] | None = None) -> None:
        self._store: dict[str, tuple[str, str]] = {}
        if headers:
            for k, v in headers.items():
                self._store[k.lower()] = (k, v)

    def get(self, name: str, default: str | None = None) -> str | None:
        entry = self._store.get(name.lower())
        return entry[1] if entry is not None else default

    def __contains__(self, name: str) -> bool:
        return name.lower() in self._store

    def items(self) -> Iterable[tuple[str, str]]:
        return list(self._store.values())

    def to_dict(self) -> dict[str, str]:
        return {entry[0]: entry[1] for entry in self._store.values()}

    def with_header(self, name: str, value: str) -> HttpHeaders:
        new_dict = self.to_dict()
        new_dict[name] = value
        return HttpHeaders(new_dict)

