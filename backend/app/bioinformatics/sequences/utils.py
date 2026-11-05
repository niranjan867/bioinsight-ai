"""Sequence utility functions including FASTA parsing and formatting."""

from io import StringIO

from Bio import SeqIO

from app.bioinformatics.sequences.validation import SequenceValidationError


def parse_fasta_records(text: str) -> list[tuple[str, str, str]]:
    """Parse single or multi-record FASTA string into (id, description, sequence) tuples."""
    stripped = text.strip()
    if not stripped:
        raise SequenceValidationError("Sequence input cannot be empty.")

    if stripped.startswith(">"):
        try:
            records = [(r.id, r.description, str(r.seq)) for r in SeqIO.parse(StringIO(stripped), "fasta")]
        except Exception as exc:
            raise SequenceValidationError("FASTA could not be parsed.") from exc

        if not records:
            raise SequenceValidationError("FASTA contains no valid records.")
        if len(records) > 100:
            raise SequenceValidationError("A maximum of 100 FASTA records can be analysed at once.")

        seen_ids: set[str] = set()
        duplicates: list[str] = []
        for r_id, _, _ in records:
            if r_id in seen_ids:
                duplicates.append(r_id)
            seen_ids.add(r_id)

        return records

    return [("sequence-1", "Submitted sequence", text)]


def format_fasta(record_id: str, description: str, sequence: str, line_length: int = 60) -> str:
    """Format sequence and header into standard FASTA format."""
    clean_seq = "".join(sequence.split())
    lines = [f">{record_id} {description}".strip()]
    for i in range(0, len(clean_seq), line_length):
        lines.append(clean_seq[i : i + line_length])
    return "\n".join(lines)

