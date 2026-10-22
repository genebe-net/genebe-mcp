from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from genebe_mcp.models import DecisionPath, GenomeName
from genebe_mcp.resolve import resolve_hg38
from genebe_mcp.tools import READ_ONLY, Deps
from genebe_mcp.truncate import truncate_text


def register(mcp: MCPServer, deps: Deps) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def explain_acmg_decision_path(
        variant: Annotated[str, Field(description="The variant, in any notation accepted by annotate_variant.")],
        genome: Annotated[GenomeName, Field(description="Genome build of coordinate input.")] = "hg38",
        tree: Annotated[
            str,
            Field(description="Decision tree: 'germline' (default), 'oncogenicity' or 'acgs-uk-onco'."),
        ] = "germline",
        version: Annotated[
            str,
            Field(description="Tree version: germline 2019 (default), oncogenicity 2022, acgs-uk-onco 2025."),
        ] = "2019",
    ) -> DecisionPath:
        """Explain step by step why each classification criterion did or did not apply to a variant.

        Use after annotate_variant when the user asks "why was this classified that way?". Returns an
        ASCII rendering of the decision tree with the evaluated conditions. By default it explains the
        germline ACMG verdict that annotate_variant returns; the somatic trees 'oncogenicity' (2022) and
        'acgs-uk-onco' (2025) can be requested explicitly. Research use only.
        """
        coords = await resolve_hg38(deps.client, variant, genome)
        text = await deps.client.decision_path_text(coords.chr, coords.pos, coords.ref, coords.alt, tree, version)
        text, truncated = truncate_text(text, deps.settings.max_text_chars)
        return DecisionPath(variant=coords, tree=tree, version=version, text=text, truncated=truncated)
