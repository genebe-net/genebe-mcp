import pytest

from genebe_mcp import mappers
from genebe_mcp.errors import GeneBeError


def test_benign_variant_verdict_and_links(load):
    result = mappers.annotation(load("variant_lpa.json"), max_consequences=8)

    assert result.verdict.classification == "Benign"
    assert result.verdict.points == -9
    assert [c.code for c in result.verdict.criteria] == ["BA1", "BP4"]
    assert result.verdict.per_gene[0].gene_symbol == "LPA"
    assert result.variant.key == "6-160585140-T-G"
    assert result.links.variant == "https://genebe.net/variant/hg38/6-160585140-T-G"
    assert result.links.gene == "https://genebe.net/gene/hg38/LPA"
    assert result.summary is None
    assert result.clinvar is None  # blank strings in the backend mean "no ClinVar record"
    assert "research use only" in result.disclaimer.lower()
    assert "research use only" in result.verdict.disclaimer.lower()


def test_frequency_and_scores(load):
    result = mappers.annotation(load("variant_lpa.json"), max_consequences=8)

    assert result.frequency.gnomad_exomes.allele_count == 192617
    assert result.frequency.combined.homozygotes == 14785
    assert result.scores.predictors["revel"].prediction == "Benign"
    assert result.scores.selected_computational_source == "REVEL"
    assert "acmg" not in result.scores.predictors
    assert "phylop100way" in result.conservation
    assert "phylop100way" not in result.scores.predictors


def test_pathogenic_variant_has_clinvar(load):
    result = mappers.annotation(load("variant_tp53.json"), max_consequences=8)

    assert result.verdict.classification == "Pathogenic"
    assert len(result.verdict.criteria) == 6
    assert result.clinvar is not None
    assert result.clinvar.review_status == "reviewed by expert panel"
    assert result.clinvar.conditions
    assert not result.clinvar.conditions.startswith(" ")


def test_consequences_are_capped_and_mane_first(load):
    result = mappers.annotation(load("variant_tp53.json"), max_consequences=5)

    assert len(result.consequences) == 5
    assert result.total_consequences > 5
    assert result.truncated is True
    assert result.consequences[0].mane_select


def test_empty_response_raises_actionable_error():
    with pytest.raises(GeneBeError, match="genome"):
        mappers.annotation({"variants": []}, max_consequences=5)


def test_convert_entries(load):
    ok, err = mappers.convert_entry("rs11", load("convert.json")[0])
    assert (ok[0].chr, ok[0].pos, err) == ("7", 11324574, None)

    bad, err = mappers.convert_entry("garbage", load("convert.json")[2])
    assert bad == []
    assert err == "Not recognized garbage"


def test_effects_sorted_by_impact(load):
    effects = [mappers.effect(e) for e in load("effect.json")[0]["effects"]]
    assert effects[0].hgvs_p == "p.Thr1399Pro"
    assert effects[0].mane_select is True

    low = effects[0].model_copy(update={"impact": "LOW", "transcript": "X"})
    assert mappers.sort_effects([low, effects[0]])[0].impact == "MODERATE"


def test_gene_is_deduplicated_and_transcripts_capped(load):
    result = mappers.gene(load("gene.json"), load("transcripts.json"), max_transcripts=5)

    assert result.symbol == "BRCA1"
    assert result.mane_select_refseq == "NM_007294.4"
    assert result.transcripts[0].mane_select
    assert len(result.transcripts) == 5
    assert result.total_transcripts == 447
    assert result.truncated
    keys = [(d.disease, d.classification) for d in result.gene_disease_validity]
    assert len(keys) == len(set(keys))


def test_liftover_keeps_structured_warnings(load):
    entry = {
        "input": "chr6-160585140-T-G",
        "status": "RESOLVED",
        "candidates": [{"chr": "chr6", "start": 1, "end": 1, "ref": "C", "alt": "G", "percentMapped": 1.0}],
        "warnings": [{"code": "REF_MISMATCH", "message": "differs"}],
    }
    result = mappers.liftover(entry, "hg38", "hg19")
    assert result.warnings[0].code == "REF_MISMATCH"
    assert result.candidates[0].ref == "C"
    assert result.errors == []

    plain = mappers.liftover(load("liftover.json")["results"][0], "hg38", "hg19")
    assert plain.status == "RESOLVED"
