from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from genebe_mcp import mappers
from genebe_mcp.models import ConvertResult, GenomeName
from genebe_mcp.tools import READ_ONLY, Deps


def register(mcp: MCPServer, deps: Deps) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def convert_variant(
        variant: Annotated[
            str,
            Field(
                description="HGVS (NM_007294.4:c.3756_3759del), rsID (rs429358), SPDI "
                "(NC_000007.14:11324573:C:T), 'chr-pos-ref-alt', or 'GENE p.Thr1700Ile'."
            ),
        ],
        input_genome: Annotated[
            GenomeName, Field(description="Genome build of positional input (hg19 input is lifted to hg38).")
        ] = "hg38",
    ) -> ConvertResult:
        """Convert a variant written in any notation into normalized hg38 genomic coordinates.

        Use when you only need the chr/pos/ref/alt of a variant (for example to translate HGVS or an rsID),
        without annotation. Does not classify the variant; use annotate_variant for that.
        """
        entries = await deps.client.convert([variant.strip()], input_genome)
        variants, error = mappers.convert_entry(variant, entries[0]) if entries else ([], "No result")
        return ConvertResult(input=variant, variants=variants, error=error)
