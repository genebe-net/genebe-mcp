"""The end user's IP must reach the backend (it rate-limits anonymous users per IP), and must not be spoofable."""

import httpx
import pytest
import respx
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from genebe_mcp.caller import valid_ip
from genebe_mcp.config import Settings
from genebe_mcp.server import create_app

API = "https://api.example.test/api-public"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Host": "localhost:17843",
}
CALL = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {"name": "convert_variant", "arguments": {"variant": "rs11"}},
}


async def call_tool(peer: str | None, extra_headers: dict[str, str] | None = None, trusted: str = "127.0.0.1") -> None:
    app = create_app(Settings(api_url=API))
    wrapped = ProxyHeadersMiddleware(app, trusted_hosts=trusted)
    transport = httpx.ASGITransport(app=wrapped, client=(peer, 5000) if peer else None)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=transport, base_url="http://localhost:17843") as http,
    ):
        response = await http.post("/v1/mcp", json=CALL, headers=HEADERS | (extra_headers or {}))
    assert response.status_code == 200, response.text


@pytest.fixture
def backend():
    with respx.mock:
        yield respx.post(f"{API}/v1/convert").respond(json=[{"variants": []}])


async def test_forwards_ip_seen_by_trusted_proxy(backend):
    await call_tool("127.0.0.1", {"X-Forwarded-For": "203.0.113.7"})

    assert backend.calls.last.request.headers["x-forwarded-for"] == "203.0.113.7"


async def test_ignores_forwarded_header_from_untrusted_peer(backend):
    await call_tool("198.51.100.20", {"X-Forwarded-For": "1.2.3.4"})

    assert backend.calls.last.request.headers["x-forwarded-for"] == "198.51.100.20"


async def test_client_supplied_header_never_reaches_backend_directly(backend):
    await call_tool("198.51.100.20", {"X-Forwarded-For": "1.2.3.4", "X-Real-IP": "5.6.7.8"})

    request = backend.calls.last.request
    assert request.headers["x-forwarded-for"] == "198.51.100.20"
    assert "x-real-ip" not in request.headers


async def test_no_peer_means_no_header(backend):
    await call_tool(None)

    assert "x-forwarded-for" not in backend.calls.last.request.headers


async def test_ip_is_not_leaked_between_requests(backend):
    await call_tool("203.0.113.1")
    await call_tool("203.0.113.2")

    assert [c.request.headers["x-forwarded-for"] for c in backend.calls] == ["203.0.113.1", "203.0.113.2"]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("203.0.113.7", "203.0.113.7"),
        ("2001:db8::1", "2001:db8::1"),
        ("not-an-ip", None),
        ("1.2.3.4, 5.6.7.8", None),
        ("", None),
        (None, None),
    ],
)
def test_valid_ip(value, expected):
    assert valid_ip(value) == expected
