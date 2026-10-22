"""Turn any supported variant notation into hg38 coordinates."""

from genebe_mcp.client import GeneBeClient
from genebe_mcp.errors import GeneBeError
from genebe_mcp.mappers import convert_entry
from genebe_mcp.models import VariantCoordinates

UNRESOLVED_HINT = (
    "Could not resolve '{variant}' to a variant. Accepted notations: 'chr-pos-ref-alt' (e.g. '6-160585140-T-G'), "
    "HGVS with transcript (e.g. 'NM_005577.4:c.4195A>C'), rsID (e.g. 'rs41272110'), SPDI, "
    "or 'GENE p.Xxx123Yyy'. If using coordinates, check the genome."
)


async def resolve_hg38(client: GeneBeClient, variant: str, input_genome: str = "hg38") -> VariantCoordinates:
    """Resolve ``variant`` to exactly one hg38 variant, or raise a :class:`GeneBeError` with advice."""
    entries = await client.convert([variant.strip()], input_genome)
    variants, error = convert_entry(variant, entries[0]) if entries else ([], None)
    if not variants:
        raise GeneBeError(UNRESOLVED_HINT.format(variant=variant) + (f" Details: {error}" if error else ""))
    return variants[0]
