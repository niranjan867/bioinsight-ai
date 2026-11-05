from typing import Literal

from pydantic import BaseModel, Field

SequenceKind = Literal["dna", "rna", "protein"]


class SequenceAnalysisRequest(BaseModel):
    sequence: str = Field(min_length=1, max_length=1_000_000)
    sequence_type: SequenceKind
    genetic_code: int = Field(default=1, ge=1, le=33)


class SequenceRecordAnalysis(BaseModel):
    id: str
    description: str
    sequence_type: SequenceKind
    input_sequence: str
    normalized_sequence: str
    normalization: str
    length: int
    composition: dict[str, int]
    percentages: dict[str, float]
    gc_percent: float | None = None
    at_percent: float | None = None
    dinucleotide_frequency: dict[str, int] = Field(default_factory=dict)
    codon_frequency: dict[str, int] = Field(default_factory=dict)
    complement: str | None = None
    reverse_complement: str | None = None
    transcription: str | None = None
    protein_properties: dict[str, float | None] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class SequenceAnalysisResponse(BaseModel):
    records: list[SequenceRecordAnalysis]
    source: str = "Biopython"
    method: str


class TranslationResponse(BaseModel):
    input_sequence: str
    sequence_type: Literal["dna", "rna"]
    frame: int | Literal["six"]
    genetic_code: int
    translations: dict[str, str]
    warnings: list[str] = Field(default_factory=list)


class AlignmentRequest(BaseModel):
    sequence_a: str = Field(min_length=1, max_length=100_000)
    sequence_b: str = Field(min_length=1, max_length=100_000)
    mode: Literal["global", "local"] = "global"
    match_score: float = Field(default=2, ge=-10, le=10)
    mismatch_score: float = Field(default=-1, ge=-10, le=10)
    gap_score: float = Field(default=-2, ge=-10, le=0)


class AlignmentResponse(BaseModel):
    mode: Literal["global", "local"]
    sequence_a: str
    sequence_b: str
    aligned_a: str
    markers: str
    aligned_b: str
    score: float
    identity_percent: float
    alignment_length: int
    source: str = "Biopython PairwiseAligner"


class BlastSubmitRequest(BaseModel):
    sequence: str = Field(min_length=1, max_length=100_000)
    sequence_type: Literal["dna", "protein"]
    database: str = Field(default="nt", min_length=2, max_length=30)


class BlastJobResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    message: str
    submitted_at: str
    results: list[dict] | None = None
