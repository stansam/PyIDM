"""Integration tests for HTTPX streaming client against mock test server."""

from app.infrastructure.networking.http_stream_client import HttpStreamClient
from tests.fixtures.mock_http_server import MockHttpHandler, MockHttpServer


def test_http_stream_client_range_inspection() -> None:
    server = MockHttpServer()
    server.start()
    try:
        client = HttpStreamClient()
        meta = client.inspect(server.url)
        assert meta.status_code == 200
        assert meta.content_length == len(MockHttpHandler.payload)
        assert meta.accept_ranges is True
        assert meta.etag == MockHttpHandler.etag

        # Stream partial byte range [0, 999]
        chunks = list(client.stream_range(server.url, start_byte=0, end_byte=999))
        data = b"".join(chunks)
        assert len(data) == 1000
        assert data == MockHttpHandler.payload[0:1000]

        # Stream second byte range [1000, 1999]
        chunks2 = list(client.stream_range(server.url, start_byte=1000, end_byte=1999))
        data2 = b"".join(chunks2)
        assert len(data2) == 1000
        assert data2 == MockHttpHandler.payload[1000:2000]

        client.close()
    finally:
        server.stop()

