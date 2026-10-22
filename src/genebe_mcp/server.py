"""Application factory: wires settings, client and tools into an ASGI app."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from genebe_mcp import __version__
from genebe_mcp.caller import ClientIpMiddleware
from genebe_mcp.client import GeneBeClient
from genebe_mcp.config import Settings
from genebe_mcp.models import DISCLAIMER
from genebe_mcp.tools import Deps, register_all

# Kept within the MCP Registry's 100-character limit; server.json must carry the same text.
DESCRIPTION = "Annotate and classify human genetic variants with GeneBe (ACMG, gnomAD, ClinVar). Research use only."

INSTRUCTIONS = f"""{DESCRIPTION}

Read-only, no account required. Verdicts come from GeneBe's transparent, points-based ACMG classification,
shown together with population frequencies, predictor scores, ClinVar and transcript consequences.

Use annotate_variant first for any question about a single variant. Use explain_acmg_decision_path to explain
a classification, convert_variant to translate HGVS/rsID/SPDI into coordinates, get_variant_effects for
transcript-level consequences, get_gene for gene details and liftover_coordinate to move positions between
genome builds. Always cite the GeneBe link from the result.

{DISCLAIMER}"""


def create_server(settings: Settings, client: GeneBeClient | None = None) -> MCPServer:
    http_client = client or GeneBeClient(settings)

    @asynccontextmanager
    async def lifespan(_: MCPServer) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await http_client.aclose()

    mcp = MCPServer(
        "GeneBe",
        title="GeneBe variant annotation",
        description=DESCRIPTION,
        instructions=INSTRUCTIONS,
        website_url="https://genebe.net",
        version=__version__,
        lifespan=lifespan,
    )
    register_all(mcp, Deps(client=http_client, settings=settings))

    @mcp.custom_route("/health", methods=["GET"])  # type: ignore[untyped-decorator]
    async def health(_: Request) -> Response:
        return JSONResponse({"status": "ok", "version": __version__})

    return mcp


def create_app(settings: Settings | None = None, client: GeneBeClient | None = None) -> Starlette:
    settings = settings or Settings()
    mcp = create_server(settings, client)
    app = mcp.streamable_http_app(
        streamable_http_path=settings.mcp_path,
        stateless_http=True,
        json_response=True,
        host=settings.host,
        transport_security=TransportSecuritySettings(
            allowed_hosts=settings.allowed_hosts, allowed_origins=settings.allowed_origins
        ),
    )
    app.add_middleware(ClientIpMiddleware)
    return app
