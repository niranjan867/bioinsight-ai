"""Biological sequence transformations for DNA and RNA."""

from Bio.Seq import Seq

from app.bioinformatics.sequences.validation import normalize_sequence


def dna_complement(sequence: str) -> str:
    """Return the complementary DNA sequence (5' -> 3')."""
    clean = normalize_sequence(sequence, "dna")
    return str(Seq(clean).complement())


def dna_reverse_complement(sequence: str) -> str:
    """Return the reverse complement of a DNA sequence (5' -> 3')."""
    clean = normalize_sequence(sequence, "dna")
    return str(Seq(clean).reverse_complement())


def dna_transcribe(sequence: str) -> str:
    """Transcribe DNA coding strand to mRNA (T -> U)."""
    clean = normalize_sequence(sequence, "dna")
    return str(Seq(clean).transcribe())


def rna_complement(sequence: str) -> str:
    """Return the complementary RNA sequence."""
    clean = normalize_sequence(sequence, "rna")
    return str(Seq(clean).complement_rna())


def rna_reverse_transcribe(sequence: str) -> str:
    """Reverse transcribe RNA to cDNA (U -> T)."""
    clean = normalize_sequence(sequence, "rna")
    return str(Seq(clean).back_transcribe())

