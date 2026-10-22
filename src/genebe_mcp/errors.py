"""Errors whose messages are written for the model that will read them."""

from mcp.server.mcpserver.exceptions import ToolError


class GeneBeError(ToolError):
    """A failure the model can act on. The message must say what to try next."""
