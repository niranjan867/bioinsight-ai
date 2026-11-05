"""Nucleotide translation module supporting all reading frames and genetic code tables."""

from Bio.Seq import Seq

from app.bioinformatics.sequences.schemas import TranslationResponse
from app.bioinformatics.sequences.validation import (
    SequenceValidationError,
    normalize_sequence,
)


def translate_sequence(
    sequence: str,
    kind: str,
    frame: int | str = "six",
    genetic_code: int = 1,
) -> TranslationResponse:
    """Translate DNA or RNA nucleotide sequence into amino acid polypeptide."""
    normalized = normalize_sequence(sequence, kind)
    if kind not in {"dna", "rna"}:
        raise SequenceValidationError("Translation requires DNA or RNA input.")

    dna = Seq(normalized.replace("U", "T"))

    if frame == "six":
        frames = {
            "+1": dna,
            "+2": dna[1:],
            "+3": dna[2:],
            "-1": dna.reverse_complement(),
            "-2": dna.reverse_complement()[1:],
            "-3": dna.reverse_complement()[2:],
        }
    elif frame in {1, 2, 3, -1, -2, -3}:
        selected = dna if frame > 0 else dna.reverse_complement()
        frames = {str(frame): selected[abs(frame) - 1 :]}
    else:
        raise SequenceValidationError("Frame must be one of -3, -2, -1, 1, 2, 3, or 'six'.")

    translations = {
        name: str(seq.translate(table=genetic_code, to_stop=False))
        for name, seq in frames.items()
    }

    return TranslationResponse(
        input_sequence=sequence,
        sequence_type=kind,
        frame=frame,
        genetic_code=genetic_code,
        translations=translations,
        warnings=["Ambiguous codons translate to X; stop codons are retained as *."],
    )
