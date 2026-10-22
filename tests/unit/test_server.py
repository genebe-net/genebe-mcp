"""Drive the whole MCP stack in-process, with the GeneBe REST API mocked."""

import json
from contextlib import asynccontextmanager

import httpx
import pytest
import respx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from genebe_mcp.client import GeneBeClient
from genebe_mcp.config import Settings
from genebe_mcp.server import create_app

API = "https://api.example.test/api-public"


@pytest.fixture
def settings() -> Settings:
    return Settings(api_url=API, api_key="secret-key", allowed_hosts=["test", "mcp.genebe.net"])


@pytest.fixture
def connect(settings):
    """Return a factory for MCP sessions; sessions are context managers because anyio scopes must stay in one task."""

    @asynccontextmanager
    async def _connect():
        app = create_app(settings)
        http = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
        async with (
            app.router.lifespan_context(app),
            streamable_http_client("http://test/v1/mcp", http_client=http) as (read, write, *_),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            yield session

    return _connect


async def call(connect, tool: str, arguments: dict):
    async with connect() as session:
        return await session.call_tool(tool, arguments)


async def test_tools_are_listed_read_only(connect):
    async with connect() as session:
        tools = (await session.list_tools()).tools

    assert {t.name for t in tools} == {
        "annotate_variant",
        "explain_acmg_decision_path",
        "convert_variant",
        "get_variant_effects",
        "get_gene",
        "liftover_coordinate",
    }
    assert all(t.annotations and t.annotations.read_only_hint for t in tools)
    assert all(t.output_schema for t in tools)


@respx.mock
async def test_annotate_returns_structured_content_and_sends_key(connect, load):
    route = respx.get(f"{API}/v1/variant-relaxed").respond(json=load("variant_lpa.json"))

    result = await call(connect, "annotate_variant", {"variant": "NM_005577.4:c.4195A>C"})

    assert not result.is_error
    assert result.structured_content["verdict"]["classification"] == "Benign"
    assert json.loads(result.content[0].text)["variant"]["pos"] == 160585140
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer secret-key"
    assert request.url.params["variant"] == "NM_005577.4:c.4195A>C"
    assert request.url.params["genome"] == "HG38"
    assert "transcript" not in request.url.params


@respx.mock
async def test_backend_400_becomes_actionable_tool_error(connect):
    respx.get(f"{API}/v1/variant-relaxed").respond(400, json={"detail": "An error occurred"})

    result = await call(connect, "annotate_variant", {"variant": "nonsense"})

    assert result.is_error
    assert "chr-pos-ref-alt" in result.content[0].text
    assert "Traceback" not in result.content[0].text


@respx.mock
async def test_decision_path_resolves_then_fetches_text(connect, load):
    respx.post(f"{API}/v1/convert").respond(json=load("convert.json")[:1])
    path = respx.get(f"{API}/v1/acmg/classifications/decision-path/text").respond(
        text="Applied criteria: BA1 (-8)\n" + "x" * 20000
    )

    result = await call(connect, "explain_acmg_decision_path", {"variant": "rs11"})

    assert not result.is_error
    assert result.structured_content["truncated"] is True
    assert result.structured_content["text"].startswith("Applied criteria")
    assert path.calls.last.request.url.params["pos"] == "11324574"
    assert path.calls.last.request.url.params["tree"] == "germline"
    assert path.calls.last.request.url.params["version"] == "2019"


@respx.mock
async def test_unresolvable_variant_gives_hint(connect):
    respx.post(f"{API}/v1/convert").respond(json=[{"error": "Not recognized garbage"}])

    result = await call(connect, "get_variant_effects", {"variant": "garbage"})

    assert result.is_error
    assert "Accepted notations" in result.content[0].text


@respx.mock
async def test_gene_not_found_and_rate_limit_messages(connect):
    respx.get(f"{API}/v1/genes/NOPE").respond(404, json={"message": "x"})
    respx.get(f"{API}/v1/genes/BRCA1").respond(429)

    missing = await call(connect, "get_gene", {"gene": "NOPE"})
    limited = await call(connect, "get_gene", {"gene": "BRCA1"})

    assert "no record" in missing.content[0].text
    assert "rate limit" in limited.content[0].text


async def test_liftover_same_genome_rejected(connect):
    result = await call(connect, "liftover_coordinate", {"query": "chr1:5", "from_genome": "hg38", "to_genome": "hg38"})
    assert result.is_error


async def test_client_reports_timeouts_politely(settings):
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    client = GeneBeClient(settings, transport=httpx.MockTransport(boom))
    with pytest.raises(Exception, match="did not respond in time"):
        await client.gene("BRCA1")
    await client.aclose()


@pytest.mark.parametrize(("host", "status"), [("mcp.genebe.net", 200), ("evil.example", 421)])
async def test_host_header_guard(settings, host, status):
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        http = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=f"http://{host}")
        r = await http.post(
            "/v1/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={"Accept": "application/json, text/event-stream"},
        )
    assert r.status_code == status
