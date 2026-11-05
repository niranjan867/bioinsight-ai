from app.bioinformatics.genes.schemas import DatabaseReference

# Common research organisms and taxonomy identifiers
TAXONOMY_MAP: dict[str, int] = {
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

SPECIES_ENSEMBL_URL: dict[str, str] = {
    "human": "Homo_sapiens",
    "mouse": "Mus_musculus",
    "rat": "Rattus_norvegicus",
    "zebrafish": "Danio_rerio",
    "fruitfly": "Drosophila_melanogaster",
    "yeast": "Saccharomyces_cerevisiae",
}

SPECIES_ALIASES: dict[str, str] = {
    "homo sapiens": "human",
    "mus musculus": "mouse",
    "rattus norvegicus": "rat",
    "danio rerio": "zebrafish",
    "drosophila melanogaster": "fruitfly",
    "caenorhabditis elegans": "nematode",
    "saccharomyces cerevisiae": "yeast",
}


def normalize_gene_query(q: str) -> str:
    """Validate and normalize gene search query."""
    cleaned = q.strip()
    if not cleaned:
        raise ValueError("Gene search query cannot be empty")
    if len(cleaned) > 100:
        raise ValueError("Gene search query exceeds maximum length of 100 characters")
    return cleaned


def normalize_species(species: str | None) -> str:
    """Normalize organism parameter for external database APIs."""
    if not species or species.strip().lower() in ("all", "*"):
        return "all"
    cleaned = species.strip().lower()
    return SPECIES_ALIASES.get(cleaned, cleaned)


def build_external_references(
    symbol: str,
    entrez_id: str | None = None,
    ensembl_id: str | None = None,
    species: str = "human",
    taxid: int | None = None,
) -> list[DatabaseReference]:
    """Construct verified external database references and outbound URLs."""
    refs: list[DatabaseReference] = []
    clean_species = species.strip().lower()
    is_human = clean_species in ("human", "homo sapiens") or taxid == 9606

    # NCBI Entrez Gene
    if entrez_id:
        refs.append(
            DatabaseReference(
                database="NCBI Gene",
                identifier=entrez_id,
                url=f"https://www.ncbi.nlm.nih.gov/gene/{entrez_id}",
                description="NCBI Entrez Gene Record",
            )
        )

    # Ensembl
    if ensembl_id:
        species_part = SPECIES_ENSEMBL_URL.get(clean_species, "Homo_sapiens")
        refs.append(
            DatabaseReference(
                database="Ensembl",
                identifier=ensembl_id,
                url=f"https://www.ensembl.org/{species_part}/Gene/Summary?g={ensembl_id}",
                description="Ensembl Genome Browser Record",
            )
        )

    # Human-specific trusted resources
    if is_human and symbol:
        # HGNC (HUGO Gene Nomenclature Committee)
        refs.append(
            DatabaseReference(
                database="HGNC",
                identifier=symbol,
                url=f"https://www.genenames.org/data/gene-symbol-report/#!/symbol/{symbol}",
                description="HUGO Gene Nomenclature Authority",
            )
        )

        # GeneCards
        refs.append(
            DatabaseReference(
                database="GeneCards",
                identifier=symbol,
                url=f"https://www.genecards.org/cgi-bin/carddisp.pl?gene={symbol}",
                description="Human Gene Compendium",
            )
        )

        # OMIM (Online Mendelian Inheritance in Man)
        refs.append(
            DatabaseReference(
                database="OMIM",
                identifier=symbol,
                url=f"https://www.omim.org/search?search={symbol}",
                description="Mendelian Inheritance and Clinical Phenotypes",
            )
        )

    # MyGene.info API Record Link
    target_id = entrez_id or ensembl_id or symbol
    if target_id:
        refs.append(
            DatabaseReference(
                database="MyGene.info",
                identifier=str(target_id),
                url=f"https://mygene.info/v3/gene/{target_id}",
                description="Biothings Gene Record",
            )
        )

    return refs
