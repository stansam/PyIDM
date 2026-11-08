"""Embedded FastAPI loopback server providing REST API for browser extensions."""

from __future__ import annotations

import secrets
import threading
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from app.application.container import Container
from app.domain.downloads.entities.download import Download
from app.domain.downloads.value_objects.headers import HttpHeaders
from app.domain.downloads.value_objects.ids import create_download_id
from app.domain.downloads.value_objects.url import DownloadUrl
from app.shared.constants import API_KEY_HEADER_NAME


class AddDownloadPayload(BaseModel):
    url: str
    filename: str | None = None
    headers: dict[str, str] | None = None


def create_browser_api_app(container: Container) -> FastAPI:
    """Create a secured FastAPI app for local browser extension communication."""
    app = FastAPI(title="PyIDM Local API", version="1.0.0")

    # Anti-CSRF: Restrict CORS strictly to extension origins
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^(chrome-extension|moz-extension)://.*$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)

    async def verify_loopback_and_token(
        request: Request,
        token: str | None = Security(api_key_header),
    ) -> None:
        # Anti-DNS Rebinding: Ensure Host header matches allowed loopback host
        host = request.headers.get("host", "")
        expected_port = container.settings.api_port
        valid_hosts = (
            f"127.0.0.1:{expected_port}",
            f"localhost:{expected_port}",
        )
        if host not in valid_hosts:
            raise HTTPException(status_code=400, detail="Invalid Host header")

        if not token or not secrets.compare_digest(token, container.settings.api_secret_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

    @app.get("/api/v1/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "app": "PyIDM"}

    @app.post("/api/v1/downloads", dependencies=[Depends(verify_loopback_and_token)])
    async def enqueue_download(payload: AddDownloadPayload) -> dict[str, str]:
        try:
            url = DownloadUrl.parse(payload.url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        custom_h = HttpHeaders(payload.headers) if payload.headers else HttpHeaders()
        filename = payload.filename or Path(url.path).name or "download.bin"

        download = Download(
            id=create_download_id(),
            url=url,
            destination_directory=container.settings.download_dir,
            filename=filename,
            custom_headers=custom_h,
            connection_count=container.settings.default_connections,
        )

        container.download_repo.save(download)
        container.download_manager.start_download(download.id)

        return {"status": "enqueued", "download_id": str(download.id)}

    return app


class LocalApiServer:
    """Wrapper managing the background uvicorn/FastAPI server thread."""

    def __init__(self, container: Container) -> None:
        self.container = container
        self.app = create_browser_api_app(container)
        self.server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        config = uvicorn.Config(
            app=self.app,
            host=self.container.settings.api_host,
            port=self.container.settings.api_port,
            log_level="warning",
            loop="asyncio",
        )
        self.server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self.server.run, daemon=True, name="PyIDM-LocalAPI")
        self._thread.start()

    def stop(self) -> None:
        if self.server:
            self.server.should_exit = True
