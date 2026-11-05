"""Sequence validation module for DNA, RNA, and protein alphabets."""

DNA_ALPHABET = frozenset("ACGTRYSWKMBDHVN")
RNA_ALPHABET = frozenset("ACGURYSWKMBDHVN")
PROTEIN_ALPHABET = frozenset("ACDEFGHIKLMNPQRSTVWYBXZJUO*")


class SequenceValidationError(ValueError):
    """Raised when biological sequence fails validation."""


def validate_sequence(sequence: str, kind: str) -> str:
    """Validate sequence characters against the target biological alphabet."""
    normalized = "".join(sequence.split()).upper()
    if not normalized:
        raise SequenceValidationError("Sequence contains no biological symbols.")

    if kind not in {"dna", "rna", "protein"}:
        raise SequenceValidationError(f"Unsupported sequence type '{kind}'. Must be 'dna', 'rna', or 'protein'.")

    alphabet = {"dna": DNA_ALPHABET, "rna": RNA_ALPHABET, "protein": PROTEIN_ALPHABET}[kind]
    invalid = sorted(set(normalized) - alphabet)
    if invalid:
        shown = ", ".join(repr(char) for char in invalid[:12])
        raise SequenceValidationError(f"Invalid {kind.upper()} character(s): {shown}.")

    if kind == "dna" and "U" in normalized:
        raise SequenceValidationError("DNA input contains U. Choose RNA or correct the sequence type.")
    if kind == "rna" and "T" in normalized:
        raise SequenceValidationError("RNA input contains T. Choose DNA or correct the sequence type.")

    return normalized


def normalize_sequence(sequence: str, kind: str) -> str:
    """Convenience alias for validate_sequence removing FASTA whitespace and uppercasing."""
    return validate_sequence(sequence, kind)

