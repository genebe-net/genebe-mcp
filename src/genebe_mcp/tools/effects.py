from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from genebe_mcp import mappers
from genebe_mcp.models import EffectsResult, GenomeName
from genebe_mcp.resolve import resolve_hg38
from genebe_mcp.tools import READ_ONLY, Deps
from genebe_mcp.truncate import take


def register(mcp: MCPServer, deps: Deps) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_variant_effects(
        variant: Annotated[str, Field(description="The variant, in any notation accepted by annotate_variant.")],
        genome: Annotated[GenomeName, Field(description="Genome build of coordinate input.")] = "hg38",
    ) -> EffectsResult:
        """List a variant's predicted molecular consequences on every overlapping transcript.

        Returns per-transcript HGVS (c. and p.), consequence terms (e.g. missense_variant) and impact,
        most severe and MANE Select transcripts first. Lightweight: no frequencies or classification.
        """
        coords = await resolve_hg38(deps.client, variant, genome)
        payload = await deps.client.effects(coords.chr, coords.pos, coords.ref, coords.alt)
        effects = mappers.sort_effects(
            [mappers.effect(e) for e in (payload[0].get("effects") if payload else None) or []]
        )
        shown, truncated = take(effects, deps.settings.max_transcripts)
        return EffectsResult(variant=coords, effects=shown, total_effects=len(effects), truncated=truncated)
