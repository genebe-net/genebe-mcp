"""Pure functions turning GeneBe REST JSON into the models served over MCP."""

from collections.abc import Mapping
from typing import Any

from genebe_mcp.errors import GeneBeError
from genebe_mcp.models import (
    AnnotationResult,
    ClinVar,
    Consequence,
    Criterion,
    Effect,
    Frequency,
    GeneDisease,
    GeneRef,
    GeneResult,
    GeneVerdict,
    Issue,
    LiftoverCandidate,
    LiftoverResult,
    Links,
    PopulationCounts,
    Score,
    Scores,
    TranscriptSummary,
    VariantCoordinates,
    Verdict,
)
from genebe_mcp.truncate import take

type Raw = Mapping[str, Any]

WEB_URL = "https://genebe.net"
MAX_GENE_DISEASES = 10
IMPACT_ORDER = {"HIGH": 0, "MODERATE": 1, "LOW": 2, "MODIFIER": 3}

# '<name>_score' fields that are not per-predictor scores.
_NOT_PREDICTORS = {"acmg"}


def _blank_to_none(value: Any) -> Any:
    return None if value in ("", [], {}) else value


def _split_criteria(raw: str | None) -> list[str]:
    return [c.strip() for c in (raw or "").split(",") if c.strip()]


def coordinates(raw: Raw, genome: str | None = None) -> VariantCoordinates:
    return VariantCoordinates(
        genome=raw.get("genome") or genome or "hg38",
        chr=str(raw["chr"]),
        pos=int(raw["pos"]),
        ref=raw.get("ref") or "",
        alt=raw.get("alt") or "",
    )


def first_variant(payload: Raw) -> Raw:
    variants: list[Raw] = payload.get("variants") or []
    if not variants:
        raise GeneBeError(
            "GeneBe returned no annotation for this variant. Check that it exists on the chosen genome (hg19/hg38)."
        )
    return variants[0]


def _counts(raw: Raw, prefix: str) -> PopulationCounts:
    return PopulationCounts(
        allele_count=raw.get(f"{prefix}_ac"),
        allele_frequency=raw.get(f"{prefix}_af"),
        homozygotes=raw.get(f"{prefix}_homalt"),
    )


def _frequency(raw: Raw) -> Frequency:
    return Frequency(
        combined=PopulationCounts(
            allele_count=raw.get("allele_count_reference_population"),
            allele_frequency=raw.get("frequency_reference_population"),
            homozygotes=raw.get("hom_count_reference_population"),
        ),
        gnomad_exomes=_counts(raw, "gnomad_exomes"),
        gnomad_genomes=_counts(raw, "gnomad_genomes"),
    )


def _score(raw: Raw, name: str) -> Score | None:
    score, prediction = raw.get(f"{name}_score"), _blank_to_none(raw.get(f"{name}_prediction"))
    return None if score is None and prediction is None else Score(score=score, prediction=prediction)


def _predictor_names(raw: Raw) -> list[str]:
    return sorted(
        key.removesuffix("_score")
        for key in raw
        if key.endswith("_score") and key.removesuffix("_score") not in _NOT_PREDICTORS
    )


def _scores(raw: Raw) -> tuple[Scores, dict[str, Score]]:
    predictors: dict[str, Score] = {}
    conservation: dict[str, Score] = {}
    for name in _predictor_names(raw):
        if (score := _score(raw, name)) is None:
            continue
        (conservation if name.startswith(("phylop", "phastcons", "gerp")) else predictors)[name] = score
    return (
        Scores(
            selected_computational=_score(raw, "computational"),
            selected_computational_source=_blank_to_none(raw.get("computational_source_selected")),
            selected_splice=_score(raw, "splice"),
            selected_splice_source=_blank_to_none(raw.get("splice_source_selected")),
            predictors=predictors,
        ),
        conservation,
    )


def _clinvar(raw: Raw) -> ClinVar | None:
    classification = _blank_to_none(raw.get("clinvar_classification"))
    if classification is None:
        return None
    return ClinVar(
        classification=classification,
        review_status=_blank_to_none(raw.get("clinvar_review_status")),
        conditions=(_blank_to_none((raw.get("clinvar_disease") or "").strip(" ,"))),
    )


def _consequence(raw: Raw) -> Consequence:
    return Consequence(
        transcript=raw.get("transcript") or raw.get("feature"),
        gene_symbol=raw.get("gene_symbol"),
        consequences=raw.get("consequences") or [],
        hgvs_c=raw.get("hgvs_c"),
        hgvs_p=raw.get("hgvs_p"),
        mane_select=bool(raw.get("mane_select")),
        canonical=bool(raw.get("canonical")),
        exon_rank=raw.get("exon_rank"),
        exon_count=raw.get("exon_count"),
    )


def _transcript_priority(c: Consequence) -> tuple[bool, bool, bool]:
    # MANE first, then canonical, then RefSeq before Ensembl; sorted() is stable for the rest.
    return (not c.mane_select, not c.canonical, not (c.transcript or "").startswith("NM_"))


def _verdict(raw: Raw) -> Verdict:
    return Verdict(
        classification=raw.get("acmg_classification"),
        points=raw.get("acmg_score"),
        criteria=[Criterion(code=c) for c in _split_criteria(raw.get("acmg_criteria"))],
        per_gene=[
            GeneVerdict(
                gene_symbol=g.get("gene_symbol"),
                transcript=g.get("transcript"),
                hgvs_c=g.get("hgvs_c"),
                hgvs_p=g.get("hgvs_p"),
                classification=g.get("verdict"),
                points=g.get("score"),
                criteria=g.get("criteria") or [],
            )
            for g in raw.get("acmg_by_gene") or []
        ],
    )


def annotation(payload: Raw, max_consequences: int) -> AnnotationResult:
    raw = first_variant(payload)
    coords = coordinates(raw, "hg38")
    scores, conservation = _scores(raw)
    consequences = sorted((_consequence(c) for c in raw.get("consequences") or []), key=_transcript_priority)
    shown, truncated = take(consequences, max_consequences)
    symbol = raw.get("gene_symbol")
    return AnnotationResult(
        summary=_blank_to_none(raw.get("summary") or payload.get("summary")),
        variant=coords,
        dbsnp=_blank_to_none(raw.get("dbsnp")),
        verdict=_verdict(raw),
        frequency=_frequency(raw),
        consequences=shown,
        total_consequences=len(consequences),
        scores=scores,
        clinvar=_clinvar(raw),
        conservation=conservation,
        gene=GeneRef(symbol=symbol, hgnc_id=raw.get("gene_hgnc_id"), transcript=raw.get("transcript")),
        links=Links(
            variant=f"{WEB_URL}/variant/hg38/{coords.key}",
            gene=f"{WEB_URL}/gene/hg38/{symbol}" if symbol else None,
        ),
        warning=_blank_to_none(raw.get("warning") or payload.get("message")),
        truncated=truncated,
    )


def convert_entry(query: str, entry: Raw) -> tuple[list[VariantCoordinates], str | None]:
    if (error := entry.get("error")) is not None:
        return [], str(error)
    return [coordinates(v) for v in entry.get("variants") or []], None


def effect(raw: Raw) -> Effect:
    return Effect(
        transcript=raw.get("transcript") or raw.get("feature"),
        source=raw.get("source"),
        gene_symbol=raw.get("geneSymbol"),
        impact=raw.get("impact"),
        effects=raw.get("effectTypes") or [],
        hgvs_c=raw.get("hgvsCoding"),
        hgvs_p=raw.get("hgvsProtein"),
        mane_select=bool(raw.get("maneSelect")),
        canonical=bool(raw.get("canonical")),
        exon_rank=raw.get("exonRank"),
        protein_id=raw.get("proteinId"),
    )


def sort_effects(effects: list[Effect]) -> list[Effect]:
    return sorted(
        effects,
        key=lambda e: (IMPACT_ORDER.get(e.impact or "", 9), not e.mane_select, not e.canonical),
    )


def gene(payload: Raw, transcripts: list[Raw], max_transcripts: int) -> GeneResult:
    raw = payload["gene"]
    shown, truncated = take(
        sorted(transcripts, key=lambda t: (not t.get("maneSelect"), not t.get("manePlusClinical"))),
        max_transcripts,
    )
    symbol = raw["symbol"]
    diseases = list(
        dict.fromkeys(
            GeneDisease(disease=d.get("disease_title"), classification=d.get("classification_title"))
            for d in raw.get("geneCcData") or []
        )
    )
    return GeneResult(
        symbol=symbol,
        name=raw.get("name"),
        hgnc_id=raw.get("hgncId"),
        ncbi_id=raw.get("ncbiId"),
        ensembl_id=raw.get("ensemblId"),
        omim_id=raw.get("omimId"),
        uniprot_id=raw.get("uniprotId"),
        chr=raw.get("chr"),
        start=raw.get("start"),
        end=raw.get("end"),
        mane_select_refseq=raw.get("maneSelectRefSeqId"),
        mane_select_ensembl=raw.get("maneSelectEnsemblId"),
        gene_disease_validity=diseases[:MAX_GENE_DISEASES],
        total_gene_disease_entries=len(diseases),
        message=payload.get("message"),
        alternative_hgnc_ids=payload.get("alternativeHgncIds") or [],
        transcripts=[
            TranscriptSummary(
                id=t["id"],
                protein_id=t.get("proteinId"),
                mane_select=bool(t.get("maneSelect")),
                mane_plus_clinical=bool(t.get("manePlusClinical")),
                coding_exons=t.get("numCodingExons"),
            )
            for t in shown
        ],
        total_transcripts=len(transcripts),
        truncated=truncated or len(diseases) > MAX_GENE_DISEASES,
        link=f"{WEB_URL}/gene/hg38/{symbol}",
    )


def _issues(items: list[Raw] | None) -> list[Issue]:
    return [Issue(code=i.get("code", "UNKNOWN"), message=i.get("message")) for i in items or []]


def liftover(entry: Raw, from_genome: str, to_genome: str) -> LiftoverResult:
    return LiftoverResult(
        input=entry.get("input", ""),
        from_genome=from_genome,
        to_genome=to_genome,
        status=entry.get("status", "UNKNOWN"),
        candidates=[
            LiftoverCandidate(
                chr=c.get("chr"),
                start=c.get("start"),
                end=c.get("end"),
                genome=c.get("genome"),
                strand=c.get("strand"),
                ref=c.get("ref"),
                alt=c.get("alt"),
                percent_mapped=c.get("percentMapped"),
            )
            for c in entry.get("candidates") or []
        ],
        warnings=_issues(entry.get("warnings")),
        errors=_issues(entry.get("errors")),
    )
