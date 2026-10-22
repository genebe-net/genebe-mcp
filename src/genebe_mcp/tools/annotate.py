from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from genebe_mcp import mappers
from genebe_mcp.models import AnnotationResult, GenomeName
from genebe_mcp.tools import READ_ONLY, Deps


def register(mcp: MCPServer, deps: Deps) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def annotate_variant(
        variant: Annotated[
            str,
            Field(
                description="The variant. Accepts 'chr-pos-ref-alt' (6-160585140-T-G), HGVS with transcript "
                "(NM_005577.4:c.4195A>C), rsID (rs41272110), SPDI, or 'GENE p.Thr1399Pro'."
            ),
        ],
        genome: Annotated[
            GenomeName, Field(description="Genome build of coordinate input. Ignored for HGVS/rsID.")
        ] = "hg38",
        transcript: Annotated[
            str | None, Field(description="Force this transcript for the classification, e.g. NM_000546.6")
        ] = None,
        gene_symbol: Annotated[
            str | None, Field(description="Force this gene for the classification, e.g. TP53")
        ] = None,
    ) -> AnnotationResult:
        """Annotate and classify one human genetic variant using GeneBe.

        Start here for any question about a variant (what is it, is it pathogenic/benign, how common is it).
        Returns the ACMG verdict with points and criteria, population frequency (gnomAD), predictor scores
        (REVEL, AlphaMissense, SpliceAI, ...), ClinVar status, transcript consequences, and links to the
        GeneBe page to cite. Research use only; not a diagnosis.
        """
        payload = await deps.client.annotate(variant.strip(), genome, transcript, gene_symbol)
        return mappers.annotation(payload, deps.settings.max_consequences)
