from unittest.mock import AsyncMock

import pytest
from app.bioinformatics.sequences import blast as blast_service
from app.bioinformatics.sequences.schemas import (
    AlignmentRequest,
    SequenceAnalysisRequest,
)
from app.bioinformatics.sequences.service import (
    SequenceValidationError,
    align,
    analyze,
    translate,
)
from fastapi.testclient import TestClient


def test_dna_analysis_preserves_input_and_computes_metrics() -> None:
    result = analyze(SequenceAnalysisRequest(sequence=" atg cgn ", sequence_type="dna"))
    record = result.records[0]
    assert record.input_sequence == " atg cgn "
    assert record.normalized_sequence == "ATGCGN"
    assert record.length == 6
    assert record.gc_percent == 50.0
    assert record.reverse_complement is not None
    assert "Ambiguous IUPAC" in record.warnings[0]


def test_fasta_multiple_records_and_protein_properties() -> None:
    dna = analyze(SequenceAnalysisRequest(sequence=">a\nACGT\n>b\nTTTT", sequence_type="dna"))
    assert [record.id for record in dna.records] == ["a", "b"]
    protein = analyze(SequenceAnalysisRequest(sequence="MKWVTFISLL", sequence_type="protein"))
    assert protein.records[0].protein_properties["molecular_weight_da"] is not None
    assert protein.records[0].protein_properties["gravy"] is not None


@pytest.mark.parametrize(
    ("sequence", "kind"),
    [("ACTU", "dna"), ("ACGT", "rna"), ("ACGT?", "dna"), ("", "protein")],
)
def test_invalid_sequence_symbols_are_rejected(sequence: str, kind: str) -> None:
    with pytest.raises(SequenceValidationError):
        analyze(SequenceAnalysisRequest(sequence=sequence or " ", sequence_type=kind))


def test_translation_supports_six_frames_and_stop_codons() -> None:
    result = translate("ATGGCC TAA", "dna", "six", 1)
    assert set(result.translations) == {"+1", "+2", "+3", "-1", "-2", "-3"}
    assert result.translations["+1"] == "MA*"


def test_pairwise_alignment_reports_identity_and_gaps() -> None:
    result = align(AlignmentRequest(sequence_a="ACGT", sequence_b="AGT", mode="global"))
    assert result.alignment_length == len(result.aligned_a) == len(result.aligned_b)
    assert "-" in result.aligned_a + result.aligned_b
    assert result.identity_percent < 100


def test_sequence_api_analyze_validation_and_upload(client: TestClient) -> None:
    valid = client.post("/api/v1/sequences/analyze", json={"sequence": "ACGT", "sequence_type": "dna"})
    assert valid.status_code == 200
    assert valid.json()["records"][0]["gc_percent"] == 50

    invalid = client.post("/api/v1/sequences/analyze", json={"sequence": "ACUT", "sequence_type": "dna"})
    assert invalid.status_code == 422

    upload = client.post(
        "/api/v1/sequences/upload?sequence_type=dna",
        files={"file": ("sample.fasta", b">sample\nACGT", "text/plain")},
    )
    assert upload.status_code == 200
    assert upload.json()["records"][0]["id"] == "sample"


def test_sequence_api_translation_and_alignment(client: TestClient) -> None:
    translated = client.post(
        "/api/v1/sequences/translate?frame=six",
        json={"sequence": "ATGGCC", "sequence_type": "dna"},
    )
    assert translated.status_code == 200
    assert len(translated.json()["translations"]) == 6

    alignment = client.post(
        "/api/v1/sequences/align",
        json={"sequence_a": "ACGT", "sequence_b": "AGT", "mode": "global"},
    )
    assert alignment.status_code == 200
    assert alignment.json()["identity_percent"] < 100


@pytest.mark.asyncio
async def test_blast_submission_and_waiting_status_are_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __init__(self, text: str) -> None:
            self.text = text

        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, *_args, **_kwargs):
            return FakeResponse("QBlastInfoBegin\n    RID = TEST-RID\nQBlastInfoEnd")

        async def get(self, *_args, **_kwargs):
            return FakeResponse("Status=WAITING")

    monkeypatch.setattr(blast_service.httpx, "AsyncClient", lambda **_kwargs: FakeClient())
    monkeypatch.setattr(blast_service, "_wait_for_ncbi_slot", AsyncMock())
    blast_service._jobs.clear()

    submitted = await blast_service.submit("ACGT", "dna", "nt", "research@example.org", "BioInsightAI")
    assert submitted["status"] == "running"
    waiting = await blast_service.get_job(submitted["job_id"], "research@example.org", "BioInsightAI")
    assert waiting is not None
    assert waiting["status"] == "running"
    assert "processing" in waiting["message"].lower()


def test_blast_rejects_unconfigured_contact_and_incompatible_database() -> None:
    import asyncio

    with pytest.raises(blast_service.BlastServiceError, match="NCBI_EMAIL"):
        asyncio.run(blast_service.submit("ACGT", "dna", "nt", "", "BioInsightAI"))
    with pytest.raises(blast_service.BlastServiceError, match="Unsupported"):
        asyncio.run(blast_service.submit("ACGT", "dna", "unknown", "research@example.org", "BioInsightAI"))
