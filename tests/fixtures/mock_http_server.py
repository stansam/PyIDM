"""Controllable HTTP test server fixture simulating range requests and errors."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar


class MockHttpHandler(BaseHTTPRequestHandler):
    """Custom request handler supporting byte-ranges, delays, and error simulation."""

    payload: ClassVar[bytes] = b"0123456789" * 100000  # 1 MB test payload
    support_ranges: ClassVar[bool] = True
    etag: ClassVar[str] = '"mock-etag-v1"'

    def do_HEAD(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(self.payload)))
        self.send_header("ETag", self.etag)
        if self.support_ranges:
            self.send_header("Accept-Ranges", "bytes")
        else:
            self.send_header("Accept-Ranges", "none")
        self.end_headers()

    def do_GET(self) -> None:
        range_header = self.headers.get("Range")

        if not self.support_ranges or not range_header:
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(self.payload)))
            self.send_header("ETag", self.etag)
            self.end_headers()
            self.wfile.write(self.payload)
            return

        # Parse "bytes=START-END"
        try:
            val = range_header.replace("bytes=", "").strip()
            parts = val.split("-")
            start = int(parts[0])
            end = int(parts[1]) if parts[1] else len(self.payload) - 1

            if start >= len(self.payload) or start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{len(self.payload)}")
                self.end_headers()
                return

            slice_data = self.payload[start : end + 1]
            self.send_response(206)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(slice_data)))
            self.send_header(
                "Content-Range", f"bytes {start}-{end}/{len(self.payload)}"
            )
            self.send_header("ETag", self.etag)
            self.end_headers()
            self.wfile.write(slice_data)
        except Exception:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        # Suppress standard logging in test suite
        pass


class MockHttpServer:
    """Convenience wrapper running MockHttpHandler in a background thread."""

    def __init__(self, port: int = 0) -> None:
        self._server = HTTPServer(("127.0.0.1", port), MockHttpHandler)
        self.port: int = self._server.server_port
        self.url: str = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()

