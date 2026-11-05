import re
from typing import Any

from Bio.SeqUtils.ProtParam import ProteinAnalysis

from app.bioinformatics.proteins.schemas import (
    AminoAcidComposition,
    DatabaseReference,
    PhysicochemicalProperties,
    ProteinSequenceAnalysisResponse,
)

# UniProt accession format regex (6 or 10 alphanumeric characters)
UNIPROT_ACCESSION_REGEX = re.compile(
    r"^([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})$",
    re.IGNORECASE,
)

# 20 standard canonical amino acids
CANONICAL_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")

# Common organism taxonomy mappings for UniProt queries
ORGANISM_TAXONOMY_MAP: dict[str, int] = {
    "human": 9606,
    "homo sapiens": 9606,
    "mouse": 10090,
    "mus musculus": 10090,
    "rat": 10116,
    "rattus norvegicus": 10116,
    "zebrafish": 7955,
    "danio rerio": 7955,
    "fruitfly": 7227,
    "drosophila melanogaster": 7227,
    "nematode": 6239,
    "caenorhabditis elegans": 6239,
    "yeast": 4932,
    "saccharomyces cerevisiae": 4932,
}


def validate_uniprot_accession(accession: str) -> str:
    """Validate and sanitize a UniProt protein accession identifier.

    Raises:
        ValueError: If accession does not match standard UniProt accession specifications.
    """
    clean_acc = accession.strip().upper()
    if not clean_acc:
        raise ValueError("UniProt accession cannot be empty")
    if not UNIPROT_ACCESSION_REGEX.match(clean_acc):
        raise ValueError(
            f"Invalid UniProt accession format '{clean_acc}'. "
            "Expected 6 or 10 character standard accession (e.g. P68871, P04637, Q9BYF1)."
        )
    return clean_acc


def is_valid_uniprot_accession(val: str) -> bool:
    """Check whether a given string is a valid UniProt accession format without raising."""
    if not val:
        return False
    return bool(UNIPROT_ACCESSION_REGEX.match(val.strip()))


def normalize_species_for_uniprot(species: str | None) -> int | None:
    """Resolve an organism name or alias to its NCBI Taxonomy ID for UniProtKB queries."""
    if not species:
        return None
    cleaned = species.strip().lower()
    if cleaned in ("all", "*", "any"):
        return None
    if cleaned.isdigit():
        return int(cleaned)
    return ORGANISM_TAXONOMY_MAP.get(cleaned)


def build_protein_fasta(
    accession: str,
    protein_name: str,
    organism: str,
    sequence: str,
    line_width: int = 60,
) -> str:
    """Format an amino acid sequence into standard biological FASTA format."""
    header = f">sp|{accession}|{protein_name} OS={organism}"
    lines = [header]
    clean_seq = sequence.replace(" ", "").replace("\n", "").replace("\r", "")
    for i in range(0, len(clean_seq), line_width):
        lines.append(clean_seq[i : i + line_width])
    return "\n".join(lines)


def analyze_protein_sequence(
    accession: str,
    protein_name: str,
    sequence: str,
    organism: str = "Homo sapiens",
) -> ProteinSequenceAnalysisResponse:
    """Perform genuine computational sequence analysis using Biopython.

    Calculates:
      - Canonical vs non-canonical residue distribution
      - Amino acid composition and relative percentages
      - Theoretical molecular weight (in Daltons)
      - Theoretical isoelectric point (pI)
      - Aromaticity, instability index, GRAVY score, and charge at pH 7.0
    """
    clean_seq = "".join(sequence.split()).upper()
    seq_length = len(clean_seq)

    if seq_length == 0:
        raise ValueError("Cannot analyze an empty protein sequence")

    # Composition analysis
    counts: dict[str, int] = {}
    non_canonical: dict[str, int] = {}

    for char in clean_seq:
        counts[char] = counts.get(char, 0) + 1
        if char not in CANONICAL_AMINO_ACIDS:
            non_canonical[char] = non_canonical.get(char, 0) + 1

    percentages = {aa: round((count / seq_length) * 100.0, 2) for aa, count in counts.items()}
    is_canonical = len(non_canonical) == 0

    notes: list[str] = [
        (
            "Theoretical molecular weight is estimated from standard isotopic average amino acid masses. "
            "It does not account for post-translational modifications (PTMs), glycosylation, prosthetic groups, "
            "or cleaved signal peptides. Do not confuse with experimentally measured mass spectroscopy data."
        ),
        (
            "Isoelectric point (pI) is estimated using standard pKa values (Bjellqvist et al.). "
            "Local dielectric microenvironments in folded tertiary structures can alter actual pI."
        ),
        "Instability index (Guruprasad et al.): values < 40 predict in vitro stability; values >= 40 predict potential instability.",
        "GRAVY (Grand Average of Hydropathy, Kyte-Doolittle): positive scores denote hydrophobic overall character; negative scores denote hydrophilic character.",
    ]

    mw: float | None = None
    pi: float | None = None
    arom: float | None = None
    instab: float | None = None
    stable: bool | None = None
    gravy: float | None = None
    charge7: float | None = None

    if is_canonical:
        pa = ProteinAnalysis(clean_seq)
        mw = round(pa.molecular_weight(), 2)
        pi = round(pa.isoelectric_point(), 2)
        arom = round(pa.aromaticity(), 4)
        instab = round(pa.instability_index(), 2)
        stable = instab < 40.0
        gravy = round(pa.gravy(), 3)
        charge7 = round(pa.charge_at_pH(7.0), 2)
    else:
        ambig_chars = ", ".join(sorted(non_canonical.keys()))
        notes.insert(
            0,
            f"Sequence contains non-canonical / ambiguous residues ({ambig_chars}). "
            "Biopython theoretical physicochemical property estimation requires an unambiguous canonical sequence "
            "and was omitted to preserve scientific accuracy.",
        )

    fasta_str = build_protein_fasta(
        accession=accession,
        protein_name=protein_name,
        organism=organism,
        sequence=clean_seq,
    )

    return ProteinSequenceAnalysisResponse(
        accession=accession,
        protein_name=protein_name,
        length=seq_length,
        sequence=clean_seq,
        fasta=fasta_str,
        composition=AminoAcidComposition(
            counts=counts,
            percentages=percentages,
            non_canonical=non_canonical,
        ),
        properties=PhysicochemicalProperties(
            theoretical_molecular_weight_da=mw,
            isoelectric_point=pi,
            aromaticity=arom,
            instability_index=instab,
            is_stable=stable,
            gravy_score=gravy,
            charge_at_ph7=charge7,
            computational_notes=notes,
        ),
        is_canonical_only=is_canonical,
        source="UniProtKB / Biopython Computational Analysis",
    )


def build_protein_references(
    accession: str,
    gene_name: str | None = None,
    organism: str = "Homo sapiens",
    pdb_ids: list[str] | None = None,
    cross_refs: list[dict[str, Any]] | None = None,
) -> list[DatabaseReference]:
    """Construct verified external database references and outbound URLs for a protein record."""
    refs: list[DatabaseReference] = [
        DatabaseReference(
            database="UniProtKB",
            identifier=accession,
            url=f"https://www.uniprot.org/uniprotkb/{accession}",
            description="Primary comprehensive protein knowledgebase entry",
        ),
        DatabaseReference(
            database="AlphaFold DB",
            identifier=accession,
            url=f"https://alphafold.ebi.ac.uk/entry/{accession}",
            description="Artificial intelligence 3D protein structure prediction",
        ),
    ]

    # GeneCards link for human proteins
    is_human = "homo sapiens" in organism.lower() or "human" in organism.lower()
    if is_human and gene_name:
        refs.append(
            DatabaseReference(
                database="GeneCards",
                identifier=gene_name,
                url=f"https://www.genecards.org/cgi-bin/carddisp.pl?gene={gene_name}",
                description="Human genomics and functional proteomics portal",
            )
        )

    # RCSB PDB structure links (first 5)
    pdb_list = pdb_ids or []
    for pdb_id in pdb_list[:5]:
        refs.append(
            DatabaseReference(
                database="RCSB PDB",
                identifier=pdb_id,
                url=f"https://www.rcsb.org/structure/{pdb_id}",
                description=f"Experimentally determined 3D atomic structure ({pdb_id})",
            )
        )

    # Additional cross-references from UniProt
    if cross_refs:
        for cr in cross_refs:
            db_name = cr.get("database")
            cr_id = cr.get("id")
            if not db_name or not cr_id or db_name in ("PDB", "AlphaFoldDB"):
                continue

            url = None
            if db_name == "RefSeq":
                url = f"https://www.ncbi.nlm.nih.gov/protein/{cr_id}"
            elif db_name == "Ensembl":
                url = f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?g={cr_id}"
            elif db_name == "HGNC":
                clean_hgnc = cr_id.replace("HGNC:", "")
                url = f"https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:{clean_hgnc}"
            elif db_name == "PubMed":
                url = f"https://pubmed.ncbi.nlm.nih.gov/{cr_id}/"

            if url:
                refs.append(
                    DatabaseReference(
                        database=db_name,
                        identifier=cr_id,
                        url=url,
                        description=f"Cross-reference in {db_name}",
                    )
                )

    return refs
