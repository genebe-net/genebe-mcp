"""Who is calling the MCP server, so the backend can rate-limit the real user and not this server.

The backend counts anonymous requests per IP. Our own connection to it always comes from this host, so we pass the
end user's address in ``X-Forwarded-For``. The backend only honours that header from its trusted (loopback/private)
peers, which is why production talks to it over ``127.0.0.1`` and not through the public API gateway.
"""

import ipaddress
from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send

client_ip: ContextVar[str | None] = ContextVar("client_ip", default=None)


def valid_ip(value: str | None) -> str | None:
    """Return ``value`` if it is a literal IP address, else ``None`` (never forward arbitrary strings)."""
    if not value:
        return None
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


class ClientIpMiddleware:
    """Remember the peer address of the current HTTP request.

    By then uvicorn's proxy-headers middleware has replaced the TCP peer (our nginx) with the address nginx saw,
    but only for proxies listed in ``GENEBE_TRUSTED_PROXIES``; otherwise client-supplied headers are ignored.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        client = scope.get("client")
        token = client_ip.set(valid_ip(client[0]) if client else None)
        try:
            await self.app(scope, receive, send)
        finally:
            client_ip.reset(token)
