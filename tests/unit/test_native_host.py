"""Unit tests for Native Messaging Host protocol framing and dispatch."""

import io
import json
from collections.abc import Mapping
from pathlib import Path
import struct
from collections.abc import Mapping

from app.application.container import Container
from app.infrastructure.browser.native_host import NativeMessagingHost
from app.infrastructure.configuration.app_settings import AppSettings


def _frame_message(payload: Mapping[str, object]) -> bytes:
    encoded = json.dumps(payload).encode("utf-8")
    return struct.pack("@I", len(encoded)) + encoded


def _unframe_message(raw_bytes: bytes) -> tuple[dict[str, object], bytes]:
    length = struct.unpack("@I", raw_bytes[:4])[0]
    payload = json.loads(raw_bytes[4 : 4 + length].decode("utf-8"))
    remaining = raw_bytes[4 + length :]
    return payload, remaining


def test_native_host_read_write(tmp_path: Path) -> None:
    settings = AppSettings(
        download_dir=tmp_path / "downloads",
        temp_dir=tmp_path / "temp",
        db_path=tmp_path / "test.db",
    )
    container = Container(settings)

    # Prepare input stream with 2 framed messages
    msg1 = {"type": "PING", "request_id": "1"}
    msg2 = {"type": "GET_STATUS", "request_id": "2"}
    in_buffer = io.BytesIO(_frame_message(msg1) + _frame_message(msg2))
    out_buffer = io.BytesIO()

    host = NativeMessagingHost(container, in_stream=in_buffer, out_stream=out_buffer)

    # 1. Read first message
    read1 = host.read_message()
    assert read1 is not None
    assert read1["type"] == "PING"

    resp1 = host.handle_message(read1)
    host.send_message(resp1)

    # 2. Read second message
    read2 = host.read_message()
    assert read2 is not None
    assert read2["type"] == "GET_STATUS"

    resp2 = host.handle_message(read2)
    host.send_message(resp2)

    # Verify output stream
    out_bytes = out_buffer.getvalue()
    out1, rem1 = _unframe_message(out_bytes)
    assert out1["type"] == "STATUS_RESPONSE"
    assert out1["request_id"] == "1"

    out2, _ = _unframe_message(rem1)
    assert out2["type"] == "STATUS_RESPONSE"
    assert out2["request_id"] == "2"
    assert out2["app"] == "PyIDM"


def test_native_host_enqueue_media(tmp_path: Path) -> None:
    settings = AppSettings(
        download_dir=tmp_path / "downloads",
        temp_dir=tmp_path / "temp",
        db_path=tmp_path / "test.db",
    )
    container = Container(settings)

    in_buffer = io.BytesIO()
    out_buffer = io.BytesIO()
    host = NativeMessagingHost(container, in_stream=in_buffer, out_stream=out_buffer)

    enqueue_msg = {
        "type": "ENQUEUE_MEDIA_DOWNLOAD",
        "request_id": "req-101",
        "url": "https://example.com/video/sample.mp4",
        "title": "My Vacation Video",
        "container": "mp4",
        "page_url": "https://example.com/watch",
        "headers": {"User-Agent": "Mozilla/5.0 Test"},
    }

    resp = host.handle_message(enqueue_msg)
    assert resp["type"] == "DOWNLOAD_ACCEPTED"
    assert resp["request_id"] == "req-101"
    assert resp["filename"] == "My Vacation Video.mp4"
    assert "download_id" in resp

    # Check that download was created in repo
    downloads = container.download_repo.get_all()
    assert len(downloads) == 1
    assert downloads[0].filename == "My Vacation Video.mp4"
    assert downloads[0].url.raw == "https://example.com/video/sample.mp4"
    assert downloads[0].custom_headers.get("referer") == "https://example.com/watch"


def test_native_host_invalid_url(tmp_path: Path) -> None:
    settings = AppSettings(
        download_dir=tmp_path / "downloads",
        temp_dir=tmp_path / "temp",
        db_path=tmp_path / "test.db",
    )
    container = Container(settings)
    host = NativeMessagingHost(container, in_stream=io.BytesIO(), out_stream=io.BytesIO())

    resp = host.handle_message({"type": "ENQUEUE_MEDIA_DOWNLOAD", "url": "not-a-valid-url"})
    assert resp["type"] == "DOWNLOAD_REJECTED"
    assert "Invalid URL" in resp["reason"]
