"""Integration tests for the local FastAPI browser extension loopback API."""

from pathlib import Path

import httpx
import pytest

from app.application.container import Container
from app.infrastructure.browser.server import create_browser_api_app
from app.infrastructure.configuration.app_settings import AppSettings
from app.shared.constants import API_KEY_HEADER_NAME


@pytest.mark.asyncio
async def test_browser_api_health_and_enqueue(tmp_path: Path) -> None:
    settings = AppSettings(
        download_dir=tmp_path / "downloads",
        temp_dir=tmp_path / "temp",
        db_path=tmp_path / "api_test.db",
        api_port=8743,
        api_secret_key="secret-token-test",
    )
    container = Container(settings)
    app = create_browser_api_app(container)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8743") as client:
        # 1. Health endpoint
        health_resp = await client.get("/api/v1/health")
        assert health_resp.status_code == 200
        assert health_resp.json() == {"status": "ok", "app": "PyIDM"}

        # 2. Unauthorized request (missing token)
        unauth_resp = await client.post(
            "/api/v1/downloads",
            json={"url": "https://example.com/file.zip"},
            headers={"Host": "127.0.0.1:8743"},
        )
        assert unauth_resp.status_code == 401

        # 3. DNS Rebinding simulation (invalid host header)
        bad_host_resp = await client.post(
            "/api/v1/downloads",
            json={"url": "https://example.com/file.zip"},
            headers={"Host": "malicious-site.com", API_KEY_HEADER_NAME: "secret-token-test"},
        )
        assert bad_host_resp.status_code == 400

        # 4. Valid Prompt request when show_browser_download_dialog=True
        valid_resp = await client.post(
            "/api/v1/downloads",
            json={"url": "https://example.com/file.zip", "filename": "downloaded.zip"},
            headers={"Host": "127.0.0.1:8743", API_KEY_HEADER_NAME: "secret-token-test"},
        )
        assert valid_resp.status_code == 200
        data = valid_resp.json()
        assert data["status"] == "prompted"

        # 5. When confirmation dialog is disabled, it directly enqueues
        settings.show_browser_download_dialog = False
        direct_resp = await client.post(
            "/api/v1/downloads",
            json={"url": "https://example.com/file2.zip", "filename": "direct.zip"},
            headers={"Host": "127.0.0.1:8743", API_KEY_HEADER_NAME: "secret-token-test"},
        )
        assert direct_resp.status_code == 200
        direct_data = direct_resp.json()
        assert direct_data["status"] == "enqueued"
        assert "download_id" in direct_data

    # Verify direct download exists in repository
    all_dl = container.download_repo.get_all()
    assert len(all_dl) == 1
    assert all_dl[0].filename == "direct.zip"
