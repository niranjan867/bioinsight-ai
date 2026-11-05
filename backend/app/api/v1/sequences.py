from typing import Annotated, Literal

from fastapi import APIRouter, File, HTTPException, Path, Query, UploadFile, status

from app.bioinformatics.sequences import blast as blast_service
from app.bioinformatics.sequences.schemas import (
    AlignmentRequest,
    AlignmentResponse,
    BlastJobResponse,
    BlastSubmitRequest,
    SequenceAnalysisRequest,
    SequenceAnalysisResponse,
    TranslationResponse,
)
from app.bioinformatics.sequences.service import (
    SequenceValidationError,
    align,
    analyze,
    normalize_sequence,
    parse_records,
    translate,
)
from app.core.config import settings

router = APIRouter(prefix="/sequences", tags=["Sequence Laboratory"])


@router.post("/analyze", response_model=SequenceAnalysisResponse, summary="Analyze one sequence or multi-record FASTA")
def analyze_sequence(request: SequenceAnalysisRequest) -> SequenceAnalysisResponse:
    try:
        return analyze(request)
    except SequenceValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/upload", response_model=SequenceAnalysisResponse, summary="Analyze uploaded FASTA")
async def upload_fasta(
    file: Annotated[UploadFile, File(description="FASTA file; maximum size 2 MiB")],
    sequence_type: Annotated[Literal["dna", "rna", "protein"], Query()],
) -> SequenceAnalysisResponse:
    if file.size is not None and file.size > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="FASTA upload exceeds the 2 MiB limit.")
    content = await file.read(2 * 1024 * 1024 + 1)
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="FASTA upload exceeds the 2 MiB limit.")
    try:
        text = content.decode("utf-8-sig")
        if not text.lstrip().startswith(">"):
            raise SequenceValidationError("Uploaded file must use FASTA format beginning with '>'.")
        return analyze(SequenceAnalysisRequest(sequence=text, sequence_type=sequence_type))
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="FASTA file must be UTF-8 encoded.") from exc
    except SequenceValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/translate", response_model=TranslationResponse, summary="Translate selected reading frame or all six frames")
def translate_sequence(
    request: SequenceAnalysisRequest,
    frame: Annotated[int | Literal["six"], Query()] = 1,
) -> TranslationResponse:
    try:
        return translate(request.sequence, request.sequence_type, frame, request.genetic_code)
    except SequenceValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Unsupported genetic code or invalid translation input.") from exc


@router.post("/align", response_model=AlignmentResponse, summary="Pairwise global or local sequence alignment")
def align_sequences(request: AlignmentRequest) -> AlignmentResponse:
    try:
        return align(request)
    except SequenceValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/blast", response_model=BlastJobResponse, status_code=status.HTTP_202_ACCEPTED, summary="Submit an asynchronous NCBI BLAST search")
async def submit_blast(request: BlastSubmitRequest) -> BlastJobResponse:
    try:
        records = parse_records(request.sequence)
        if len(records) != 1:
            raise SequenceValidationError("Submit one FASTA record per BLAST job.")
        record = records[0][2]
        normalized = normalize_sequence(record, request.sequence_type)
        result = await blast_service.submit(normalized, request.sequence_type, request.database, settings.NCBI_EMAIL, settings.NCBI_TOOL)
        return BlastJobResponse(**result)
    except (SequenceValidationError, blast_service.BlastServiceError) as exc:
        raise HTTPException(status_code=422 if isinstance(exc, SequenceValidationError) else 503, detail=str(exc)) from exc


@router.get("/blast/{job_id}", response_model=BlastJobResponse, summary="Poll NCBI BLAST job status and results")
async def get_blast_job(job_id: Annotated[str, Path(min_length=36, max_length=36)]) -> BlastJobResponse:
    try:
        result = await blast_service.get_job(job_id, settings.NCBI_EMAIL, settings.NCBI_TOOL)
    except blast_service.BlastServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="BLAST job not found or expired after application restart.")
    return BlastJobResponse(**result)
