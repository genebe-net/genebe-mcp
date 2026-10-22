"""Smoke tests against the real GeneBe API. Run with: uv run pytest -m live"""

import pytest

from genebe_mcp import mappers
from genebe_mcp.client import GeneBeClient
from genebe_mcp.config import Settings
from genebe_mcp.errors import GeneBeError

pytestmark = pytest.mark.live


@pytest.fixture
async def client():
    c = GeneBeClient(Settings())
    yield c
    await c.aclose()


@pytest.mark.parametrize(
    ("variant", "expected"),
    [
        ("6-160585140-T-G", "Benign"),
        ("17-7674220-C-T", "Pathogenic"),
        ("NM_005577.4:c.4195A>C", "Benign"),
    ],
)
async def test_known_variants(client, variant, expected):
    result = mappers.annotation(await client.annotate(variant, "hg38", None, None), 8)
    assert result.verdict.classification == expected


async def test_indel_has_multiple_transcripts(client):
    result = mappers.annotation(await client.annotate("NM_007294.4:c.3756_3759del", "hg38", None, None), 5)
    assert result.total_consequences >= 1


async def test_garbage_is_a_clean_error(client):
    with pytest.raises(GeneBeError):
        await client.annotate("garbage", "hg38", None, None)


@pytest.mark.parametrize(
    ("tree", "version"), [("germline", "2019"), ("oncogenicity", "2022"), ("acgs-uk-onco", "2025")]
)
async def test_decision_path_trees_exist(client, tree, version):
    text = await client.decision_path_text("6", 160585140, "T", "G", tree, version)
    assert text.startswith("Applied criteria")
