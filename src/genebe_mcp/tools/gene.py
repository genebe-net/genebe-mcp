from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from genebe_mcp import mappers
from genebe_mcp.models import GeneResult
from genebe_mcp.tools import READ_ONLY, Deps


def register(mcp: MCPServer, deps: Deps) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_gene(
        gene: Annotated[
            str,
            Field(description="Gene symbol (BRCA1), alias, HGNC id (HGNC:1100), 'entrez:672' or Ensembl id (ENSG...)."),
        ],
        include_transcripts: Annotated[bool, Field(description="Also list the gene's transcripts.")] = True,
    ) -> GeneResult:
        """Look up a human gene: identifiers, location, MANE Select transcript, ClinGen gene-disease validity.

        Use for questions about a gene rather than a specific variant. Transcripts are listed with
        MANE Select first and capped; check total_transcripts.
        """
        payload = await deps.client.gene(gene)
        transcripts = await deps.client.transcripts(gene) if include_transcripts else []
        return mappers.gene(payload, transcripts, deps.settings.max_transcripts)
