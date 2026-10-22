"""Typed tool outputs. Their JSON schemas are published as the tools' ``outputSchema``."""

from typing import Literal

from pydantic import BaseModel, Field

DISCLAIMER = (
    "For research use only. Not a diagnosis; results must be reviewed by a qualified "
    "specialist before any clinical use."
)

GenomeName = Literal["hg19", "hg38", "t2t"]


class VariantCoordinates(BaseModel):
    genome: str
    chr: str
    pos: int = Field(description="1-based VCF position")
    ref: str
    alt: str

    @property
    def key(self) -> str:
        return f"{self.chr}-{self.pos}-{self.ref}-{self.alt}"


class Criterion(BaseModel):
    code: str = Field(description="Criterion with strength, e.g. 'BA1' or 'PP3_Strong'")
    reason: str | None = Field(None, description="Why the criterion fired, when the backend provides it")


class GeneVerdict(BaseModel):
    gene_symbol: str | None
    transcript: str | None
    hgvs_c: str | None
    hgvs_p: str | None
    classification: str | None
    points: int | None
    criteria: list[str]


class Verdict(BaseModel):
    classification: str | None = Field(description="e.g. Pathogenic, Likely_benign, Uncertain_significance")
    points: int | None = Field(description="Total ACMG points; positive favours pathogenic, negative benign")
    criteria: list[Criterion]
    guideline: str | None = None
    per_gene: list[GeneVerdict] = Field(description="Verdict for every overlapping gene, when more than one")
    disclaimer: str = DISCLAIMER


class PopulationCounts(BaseModel):
    allele_count: int | None
    allele_frequency: float | None
    homozygotes: int | None


class Frequency(BaseModel):
    combined: PopulationCounts
    gnomad_exomes: PopulationCounts
    gnomad_genomes: PopulationCounts


class Score(BaseModel):
    score: float | None
    prediction: str | None


class Scores(BaseModel):
    selected_computational: Score | None = Field(description="Predictor GeneBe picked for the ACMG call")
    selected_computational_source: str | None
    selected_splice: Score | None
    selected_splice_source: str | None
    predictors: dict[str, Score] = Field(description="Every available predictor, keyed by name")


class ClinVar(BaseModel):
    classification: str | None
    review_status: str | None
    conditions: str | None


class Consequence(BaseModel):
    transcript: str | None
    gene_symbol: str | None
    consequences: list[str]
    hgvs_c: str | None
    hgvs_p: str | None
    mane_select: bool
    canonical: bool
    exon_rank: int | None
    exon_count: int | None


class GeneRef(BaseModel):
    symbol: str | None
    hgnc_id: int | None
    transcript: str | None = Field(description="Transcript used for the classification")


class Links(BaseModel):
    variant: str
    gene: str | None


class AnnotationResult(BaseModel):
    summary: str | None = Field(
        None, description="Human-readable variant summary from GeneBe, when the backend provides one"
    )
    variant: VariantCoordinates
    dbsnp: str | None
    verdict: Verdict
    frequency: Frequency
    consequences: list[Consequence]
    total_consequences: int
    scores: Scores
    clinvar: ClinVar | None
    conservation: dict[str, Score]
    gene: GeneRef
    links: Links
    warning: str | None = None
    truncated: bool = False
    disclaimer: str = DISCLAIMER


class ConvertResult(BaseModel):
    input: str
    variants: list[VariantCoordinates] = Field(description="Resolved hg38 coordinates (usually exactly one)")
    error: str | None = None


class DecisionPath(BaseModel):
    variant: VariantCoordinates
    tree: str
    version: str
    text: str = Field(description="ASCII rendering of how each criterion was evaluated")
    truncated: bool = False
    disclaimer: str = DISCLAIMER


class Effect(BaseModel):
    transcript: str | None
    source: str | None
    gene_symbol: str | None
    impact: str | None
    effects: list[str]
    hgvs_c: str | None
    hgvs_p: str | None
    mane_select: bool
    canonical: bool
    exon_rank: int | None
    protein_id: str | None


class EffectsResult(BaseModel):
    variant: VariantCoordinates
    effects: list[Effect]
    total_effects: int
    truncated: bool = False


class TranscriptSummary(BaseModel):
    id: str
    protein_id: str | None
    mane_select: bool
    mane_plus_clinical: bool
    coding_exons: int | None


class GeneDisease(BaseModel, frozen=True):
    disease: str | None
    classification: str | None = Field(description="ClinGen gene-disease validity")


class GeneResult(BaseModel):
    symbol: str
    name: str | None
    hgnc_id: int | None
    ncbi_id: int | None
    ensembl_id: str | None
    omim_id: str | None
    uniprot_id: str | None
    chr: str | None
    start: int | None
    end: int | None
    mane_select_refseq: str | None
    mane_select_ensembl: str | None
    gene_disease_validity: list[GeneDisease]
    total_gene_disease_entries: int
    message: str | None = Field(None, description="Set when an alias matched several genes")
    alternative_hgnc_ids: list[str] = Field(default_factory=list)
    transcripts: list[TranscriptSummary]
    total_transcripts: int
    truncated: bool = False
    link: str


class LiftoverCandidate(BaseModel):
    chr: str | None
    start: int | None
    end: int | None
    genome: str | None
    strand: str | None
    ref: str | None = None
    alt: str | None = None
    percent_mapped: float | None


class Issue(BaseModel):
    code: str
    message: str | None


class LiftoverResult(BaseModel):
    input: str
    from_genome: str
    to_genome: str
    status: str = Field(description="RESOLVED, AMBIGUOUS, UNRESOLVED, INVALID, NOT_RECOGNIZED or UNSUPPORTED")
    candidates: list[LiftoverCandidate]
    warnings: list[Issue]
    errors: list[Issue]
