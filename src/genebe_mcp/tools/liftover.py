from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from genebe_mcp import mappers
from genebe_mcp.errors import GeneBeError
from genebe_mcp.models import GenomeName, LiftoverResult
from genebe_mcp.tools import READ_ONLY, Deps


def register(mcp: MCPServer, deps: Deps) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def liftover_coordinate(
        query: Annotated[
            str,
            Field(
                description="A position ('chr8:141310715'), an interval ('chr8:141310715-141310716') "
                "or a variant ('chr2-23423-A-C', HGVS, rsID)."
            ),
        ],
        from_genome: Annotated[GenomeName, Field(description="Genome build of the input.")],
        to_genome: Annotated[GenomeName, Field(description="Genome build to convert to.")],
    ) -> LiftoverResult:
        """Convert a genomic position, interval or variant between genome builds (hg19, hg38, t2t).

        Check `status`: RESOLVED means one result, AMBIGUOUS means several candidates, anything else
        means it could not be mapped (see errors). For variants, ref/alt are rebuilt against the target
        reference and warnings such as REF_MISMATCH may apply.
        """
        if from_genome == to_genome:
            raise GeneBeError("from_genome and to_genome are the same; no conversion needed.")
        payload = await deps.client.liftover([query.strip()], from_genome, to_genome)
        results = payload.get("results") or []
        if not results:
            raise GeneBeError("GeneBe returned no liftover result. Check the query format.")
        return mappers.liftover(results[0], from_genome, to_genome)
