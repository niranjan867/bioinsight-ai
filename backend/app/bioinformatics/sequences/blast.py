import asyncio
import logging
import re
import time
from datetime import UTC, datetime
from io import StringIO
from uuid import uuid4

import httpx
from Bio.Blast import NCBIXML

logger = logging.getLogger(__name__)
BLAST_URL = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
DATABASES = {"nt", "refseq_rna", "refseq_genomic", "nr", "refseq_protein", "swissprot"}
_jobs: dict[str, dict] = {}
_ncbi_lock = asyncio.Lock()
_last_request_at = 0.0


async def _wait_for_ncbi_slot() -> None:
    global _last_request_at
    async with _ncbi_lock:
        delay = 1.0 - (time.monotonic() - _last_request_at)
        if delay > 0:
            await asyncio.sleep(delay)
        _last_request_at = time.monotonic()


def _prune_old_jobs() -> None:
    cutoff = datetime.now(UTC).timestamp() - 48 * 60 * 60
    for job_id, job in list(_jobs.items()):
        try:
            if datetime.fromisoformat(job["submitted_at"]).timestamp() < cutoff:
                _jobs.pop(job_id, None)
        except (KeyError, ValueError):
            _jobs.pop(job_id, None)


class BlastServiceError(ValueError):
    pass


def _params(email: str, tool: str) -> dict[str, str]:
    return {"EMAIL": email, "TOOL": tool}


async def submit(sequence: str, kind: str, database: str, email: str, tool: str) -> dict:
    if not email:
        raise BlastServiceError("Configure NCBI_EMAIL in backend/.env before using BLAST.")
    if database not in DATABASES:
        raise BlastServiceError(f"Unsupported NCBI BLAST database '{database}'.")
    program = "blastp" if kind == "protein" else "blastn"
    if program == "blastp" and database not in {"nr", "refseq_protein", "swissprot"}:
        raise BlastServiceError("Protein queries require nr, refseq_protein, or swissprot.")
    if program == "blastn" and database not in {"nt", "refseq_rna", "refseq_genomic"}:
        raise BlastServiceError("Nucleotide queries require nt, refseq_rna, or refseq_genomic.")

    _prune_old_jobs()
    if len(_jobs) >= 100:
        raise BlastServiceError("The local BLAST job queue is full. Wait for active searches to finish.")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30, connect=10)) as client:
            await _wait_for_ncbi_slot()
            response = await client.post(
                BLAST_URL,
                data={**_params(email, tool), "CMD": "Put", "PROGRAM": program, "DATABASE": database, "QUERY": sequence},
                headers={"User-Agent": f"{tool} ({email})"},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("NCBI BLAST submission failed: %s", type(exc).__name__)
        raise BlastServiceError("NCBI BLAST could not be reached. Try again later.") from exc

    rid_match = re.search(r"RID\s*=\s*([A-Z0-9-]+)", response.text)
    if not rid_match:
        raise BlastServiceError("NCBI did not return a BLAST request identifier.")
    job_id = str(uuid4())
    submitted_at = datetime.now(UTC).isoformat()
    _jobs[job_id] = {"rid": rid_match.group(1), "database": database, "kind": kind, "submitted_at": submitted_at, "status": "running", "results": None}
    return {"job_id": job_id, "status": "running", "message": "Submitted to NCBI BLAST; poll the job URL for status.", "submitted_at": submitted_at, "results": None}


async def get_job(job_id: str, email: str, tool: str) -> dict | None:
    job = _jobs.get(job_id)
    if not job:
        return None
    if job["status"] != "running":
        return {"job_id": job_id, **{key: value for key, value in job.items() if key != "rid"}}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30, connect=10)) as client:
            await _wait_for_ncbi_slot()
            status_response = await client.get(
                BLAST_URL,
                params={**_params(email, tool), "CMD": "Get", "RID": job["rid"], "FORMAT_OBJECT": "SearchInfo"},
                headers={"User-Agent": f"{tool} ({email})"},
            )
            status_response.raise_for_status()
            body = status_response.text
            if "Status=WAITING" in body:
                return {"job_id": job_id, "status": "running", "message": "NCBI is processing this query.", "submitted_at": job["submitted_at"], "results": None}
            if "Status=FAILED" in body or "Status=UNKNOWN" in body:
                job["status"] = "failed"
                job["message"] = "NCBI reported that this BLAST job failed or expired."
                return {"job_id": job_id, "status": "failed", "message": job["message"], "submitted_at": job["submitted_at"], "results": None}
            if "Status=READY" not in body:
                return {"job_id": job_id, "status": "running", "message": "Waiting for NCBI BLAST status.", "submitted_at": job["submitted_at"], "results": None}
            await _wait_for_ncbi_slot()
            result_response = await client.get(
                BLAST_URL,
                params={**_params(email, tool), "CMD": "Get", "RID": job["rid"], "FORMAT_TYPE": "XML"},
                headers={"User-Agent": f"{tool} ({email})"},
            )
            result_response.raise_for_status()
        parsed = NCBIXML.read(StringIO(result_response.text))
        query_length = max(parsed.query_length or 0, 1)
        hits = []
        for alignment in parsed.alignments[:100]:
            for hsp in alignment.hsps[:5]:
                hits.append({
                    "subject_id": alignment.hit_id,
                    "subject_title": alignment.hit_def,
                    "identity": hsp.identities,
                    "alignment_length": hsp.align_length,
                    "identity_percent": round(hsp.identities * 100 / max(hsp.align_length, 1), 4),
                    "e_value": hsp.expect,
                    "query_coverage_percent": round(abs(hsp.query_end - hsp.query_start + 1) * 100 / query_length, 4),
                    "query_start": hsp.query_start,
                    "query_end": hsp.query_end,
                    "subject_start": hsp.sbjct_start,
                    "subject_end": hsp.sbjct_end,
                    "query_alignment": hsp.query,
                    "subject_alignment": hsp.sbjct,
                })
        job["status"] = "completed"
        job["results"] = hits
        job["message"] = "NCBI BLAST results retrieved."
        return {"job_id": job_id, "status": "completed", "message": job["message"], "submitted_at": job["submitted_at"], "results": hits}
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("NCBI BLAST polling failed: %s", type(exc).__name__)
        raise BlastServiceError("NCBI BLAST status or result retrieval failed. Retry polling later.") from exc
