"""MCP tools. Each module exposes ``register(mcp, deps)`` and stays a thin layer over the client."""

from dataclasses import dataclass

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from genebe_mcp.client import GeneBeClient
from genebe_mcp.config import Settings

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)


@dataclass(frozen=True, slots=True)
class Deps:
    client: GeneBeClient
    settings: Settings


def register_all(mcp: MCPServer, deps: Deps) -> None:
    from genebe_mcp.tools import acmg_path, annotate, convert, effects, gene, liftover

    for module in (annotate, acmg_path, convert, effects, gene, liftover):
        module.register(mcp, deps)
