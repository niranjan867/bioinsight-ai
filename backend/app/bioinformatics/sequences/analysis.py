"""Sequence composition, nucleotide frequencies, and protein physicochemical property analysis."""

from collections import Counter

from Bio.Seq import Seq
from Bio.SeqUtils.ProtParam import ProteinAnalysis

from app.bioinformatics.sequences.schemas import (
    SequenceAnalysisRequest,
    SequenceAnalysisResponse,
    SequenceRecordAnalysis,
)
from app.bioinformatics.sequences.utils import parse_fasta_records
from app.bioinformatics.sequences.validation import normalize_sequence


def analyze_record(record_id: str, description: str, raw: str, kind: str) -> SequenceRecordAnalysis:
    """Analyze a single biological sequence record."""
    sequence = normalize_sequence(raw, kind)
    counts = Counter(sequence)
    length = len(sequence)
    percentages = {symbol: round(count * 100 / length, 4) for symbol, count in sorted(counts.items())}
    gc_percent = at_percent = None
    dinucleotides: dict[str, int] = {}
    codons: dict[str, int] = {}
    complement = reverse_complement = transcription = None
    protein_props: dict[str, float | None] = {}
    warnings: list[str] = []

    if kind in {"dna", "rna"}:
        gc_symbols = "GC"
        at_symbols = "AT" if kind == "dna" else "AU"
        gc_percent = round(sum(counts.get(base, 0) for base in gc_symbols) * 100 / length, 4)
        at_percent = round(sum(counts.get(base, 0) for base in at_symbols) * 100 / length, 4)
        dinucleotides = dict(sorted(Counter(sequence[i : i + 2] for i in range(length - 1)).items()))

        if kind == "dna":
            complement = str(Seq(sequence).complement())
            reverse_complement = str(Seq(sequence).reverse_complement())
            transcription = str(Seq(sequence).transcribe())
        else:
            complement = str(Seq(sequence).complement_rna())

        if any(base not in "ACGT" if kind == "dna" else base not in "ACGU" for base in sequence):
            warnings.append("Ambiguous IUPAC symbols are included in the denominator; base percentages show only unambiguous bases.")
        if length % 3:
            warnings.append("Sequence length is not divisible by three; trailing bases are omitted by codon counts and translation.")
        codons = dict(sorted(Counter(sequence[i : i + 3] for i in range(0, length - 2, 3)).items()))
    else:
        if set(sequence) <= set("ACDEFGHIKLMNPQRSTVWY"):
            analysis = ProteinAnalysis(sequence)
            protein_props = {
                "molecular_weight_da": round(analysis.molecular_weight(), 4),
                "isoelectric_point": round(analysis.isoelectric_point(), 4),
                "instability_index": round(analysis.instability_index(), 4),
                "gravy": round(analysis.gravy(), 4),
                "aromaticity": round(analysis.aromaticity(), 4),
            }
        else:
            protein_props = {
                key: None
                for key in ("molecular_weight_da", "isoelectric_point", "instability_index", "gravy", "aromaticity")
            }
            warnings.append("Ambiguous or stop symbols prevent standard physicochemical estimates.")

    return SequenceRecordAnalysis(
        id=record_id,
        description=description,
        sequence_type=kind,
        input_sequence=raw,
        normalized_sequence=sequence,
        normalization="Whitespace removed and letters uppercased; submitted sequence is returned unchanged in input_sequence.",
        length=length,
        composition=dict(sorted(counts.items())),
        percentages=percentages,
        gc_percent=gc_percent,
        at_percent=at_percent,
        dinucleotide_frequency=dinucleotides,
        codon_frequency=codons,
        complement=complement,
        reverse_complement=reverse_complement,
        transcription=transcription,
        protein_properties=protein_props,
        warnings=warnings,
    )


def analyze_sequence_request(request: SequenceAnalysisRequest) -> SequenceAnalysisResponse:
    """Analyze all sequence records from an analysis request."""
    records = [analyze_record(*record, request.sequence_type) for record in parse_fasta_records(request.sequence)]
    return SequenceAnalysisResponse(
        records=records,
        method="Biopython sequence parsing and analysis; IUPAC nucleotide composition and explicit normalization.",
    )
