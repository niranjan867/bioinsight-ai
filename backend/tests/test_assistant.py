from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.bioinformatics.compounds.schemas import (
    CompoundDetailResponse,
    LipinskiRuleOfFive,
)
from app.bioinformatics.genes.schemas import GeneDetailResponse, GenomicLocation


def test_get_assistant_suggestions(client: TestClient) -> None:
    response = client.get("/api/v1/assistant/suggestions")
    assert response.status_code == 200
    suggestions = response.json()
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0
    assert any("BRCA1" in s for s in suggestions)


def test_query_assistant_gene_grounded(client: TestClient) -> None:
    mock_gene = GeneDetailResponse(
        id="672",
        symbol="BRCA1",
        name="BRCA1 DNA repair associated",
        species="Homo sapiens",
        taxid=9606,
        chromosome="17",
        genomic_location=GenomicLocation(chromosome="17", start=43044295, end=43170245, strand=-1),
        ensembl_id="ENSG00000012048",
        entrez_id="672",
        type_of_gene="protein-coding",
        summary="Encodes a nuclear phosphoprotein maintaining genomic stability.",
        aliases=["BRCAI", "BRCC1"],
        references=[],
        source="MyGene.info",
        retrieved_at="2026-11-07T00:00:00Z",
        cached=False,
    )

    with patch(
        "app.bioinformatics.genes.service.GeneService.get_gene",
        new_callable=AsyncMock,
        return_value=mock_gene,
    ):
        response = client.post(
            "/api/v1/assistant/chat",
            json={"query": "What are the genomic coordinates and functional summary for human BRCA1?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "BRCA1" in data["answer"]
        assert "Chromosome 17" in data["answer"]
        assert len(data["citations"]) > 0
        assert "Gene Intelligence" in data["source_modules"]
        assert data["confidence"] >= 0.8


def test_query_assistant_compound_grounded(client: TestClient) -> None:
    mock_compound = CompoundDetailResponse(
        cid=2244,
        name="Aspirin",
        molecular_formula="C9H8O4",
        molecular_weight=180.16,
        canonical_smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
        inchi_key="BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
        xlogp=1.2,
        tpsa=63.6,
        h_bond_donor_count=1,
        h_bond_acceptor_count=4,
        rotatable_bond_count=3,
        image_url="https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/PNG",
        lipinski=LipinskiRuleOfFive(
            is_druglike=True,
            violations_count=0,
            molecular_weight_pass=True,
            logp_pass=True,
            h_bond_donors_pass=True,
            h_bond_acceptors_pass=True,
        ),
        retrieved_at=datetime.now(UTC),
    )

    with patch(
        "app.bioinformatics.compounds.service.CompoundService.get_compound",
        new_callable=AsyncMock,
        return_value=mock_compound,
    ):
        response = client.post(
            "/api/v1/assistant/chat",
            json={"query": "Tell me about the molecular properties and Lipinski compliance of Aspirin"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Aspirin" in data["answer"]
        assert "Lipinski" in data["answer"]
        assert "Compound Intelligence" in data["source_modules"]
