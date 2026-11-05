"""Unified Sequence Laboratory service providing analysis, translation, and alignment."""

from app.bioinformatics.sequences.alignment import align_pairwise
from app.bioinformatics.sequences.analysis import (
    analyze_record,
    analyze_sequence_request,
)
from app.bioinformatics.sequences.schemas import (
    AlignmentRequest,
    AlignmentResponse,
    SequenceAnalysisRequest,
    SequenceAnalysisResponse,
    TranslationResponse,
)
from app.bioinformatics.sequences.translation import translate_sequence
from app.bioinformatics.sequences.utils import parse_fasta_records
from app.bioinformatics.sequences.validation import (
    DNA_ALPHABET,
    PROTEIN_ALPHABET,
    RNA_ALPHABET,
    SequenceValidationError,
    normalize_sequence,
    validate_sequence,
)


def analyze(request: SequenceAnalysisRequest) -> SequenceAnalysisResponse:
    """Analyze sequence records from raw text or FASTA format."""
    return analyze_sequence_request(request)


def translate(
    sequence: str,
    kind: str,
    frame: int | str = "six",
    genetic_code: int = 1,
) -> TranslationResponse:
    """Translate nucleotide sequence into protein sequence."""
    return translate_sequence(sequence=sequence, kind=kind, frame=frame, genetic_code=genetic_code)


def align(request: AlignmentRequest) -> AlignmentResponse:
    """Perform pairwise global or local sequence alignment."""
    return align_pairwise(request)


def parse_records(text: str) -> list[tuple[str, str, str]]:
    """Parse FASTA records from text."""
    return parse_fasta_records(text)


__all__ = [
    "DNA_ALPHABET",
    "PROTEIN_ALPHABET",
    "RNA_ALPHABET",
    "SequenceValidationError",
    "align",
    "align_pairwise",
    "analyze",
    "analyze_record",
    "analyze_sequence_request",
    "normalize_sequence",
    "parse_records",
    "translate",
    "translate_sequence",
    "validate_sequence",
]
