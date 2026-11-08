"""Browser integration layer supporting Native Messaging and local loopback APIs."""

from app.infrastructure.browser.native_host import NativeMessagingHost
from app.infrastructure.browser.registration import (
    get_browser_status,
    register_all_browsers,
    unregister_all_browsers,
)
from app.infrastructure.browser.server import LocalApiServer, create_browser_api_app

__all__ = [
    "NativeMessagingHost",
    "LocalApiServer",
    "create_browser_api_app",
    "register_all_browsers",
    "unregister_all_browsers",
    "get_browser_status",
]

