"""Pairwise sequence alignment using Biopython PairwiseAligner."""

from math import isfinite

from Bio.Align import PairwiseAligner

from app.bioinformatics.sequences.schemas import AlignmentRequest, AlignmentResponse
from app.bioinformatics.sequences.validation import (
    PROTEIN_ALPHABET,
    SequenceValidationError,
    normalize_sequence,
)


def align_pairwise(request: AlignmentRequest) -> AlignmentResponse:
    """Execute global (Needleman-Wunsch) or local (Smith-Waterman) pairwise alignment."""
    is_prot_a = set(request.sequence_a.upper()) <= PROTEIN_ALPHABET
    is_prot_b = set(request.sequence_b.upper()) <= PROTEIN_ALPHABET

    seq_a = normalize_sequence(request.sequence_a, "protein" if is_prot_a else "dna")
    seq_b = normalize_sequence(request.sequence_b, "protein" if is_prot_b else "dna")

    if (set(seq_a) <= PROTEIN_ALPHABET) != (set(seq_b) <= PROTEIN_ALPHABET):
        raise SequenceValidationError("Both sequences must use the same alphabet.")

    aligner = PairwiseAligner()
    aligner.mode = request.mode
    aligner.match_score = request.match_score
    aligner.mismatch_score = request.mismatch_score
    aligner.open_gap_score = request.gap_score
    aligner.extend_gap_score = request.gap_score

    alignments = aligner.align(seq_a, seq_b)
    if not alignments:
        raise SequenceValidationError("No valid alignment could be computed.")

    result = alignments[0]
    aligned_a_parts: list[str] = []
    aligned_b_parts: list[str] = []
    coordinates = result.coordinates

    for index in range(coordinates.shape[1] - 1):
        a_start, a_end = int(coordinates[0, index]), int(coordinates[0, index + 1])
        b_start, b_end = int(coordinates[1, index]), int(coordinates[1, index + 1])
        a_size, b_size = abs(a_end - a_start), abs(b_end - b_start)

        if a_size and b_size:
            aligned_a_parts.append(seq_a[min(a_start, a_end) : max(a_start, a_end)])
            aligned_b_parts.append(seq_b[min(b_start, b_end) : max(b_start, b_end)])
        elif a_size:
            aligned_a_parts.append(seq_a[min(a_start, a_end) : max(a_start, a_end)])
            aligned_b_parts.append("-" * a_size)
        elif b_size:
            aligned_a_parts.append("-" * b_size)
            aligned_b_parts.append(seq_b[min(b_start, b_end) : max(b_start, b_end)])

    aligned_a = "".join(aligned_a_parts)
    aligned_b = "".join(aligned_b_parts)
    markers = "".join(
        "|" if a == b and a != "-" else "." if a != "-" and b != "-" else " "
        for a, b in zip(aligned_a, aligned_b)
    )
    aligned_positions = [(a, b) for a, b in zip(aligned_a, aligned_b) if a != "-" or b != "-"]
    identity = sum(a == b and a != "-" for a, b in aligned_positions)

    return AlignmentResponse(
        mode=request.mode,
        sequence_a=seq_a,
        sequence_b=seq_b,
        aligned_a=aligned_a,
        markers=markers,
        aligned_b=aligned_b,
        score=float(result.score) if isfinite(result.score) else 0.0,
        identity_percent=round(identity * 100 / max(len(aligned_positions), 1), 4),
        alignment_length=len(aligned_positions),
    )
