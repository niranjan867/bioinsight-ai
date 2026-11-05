# Architecture

## Runtime layout

```text
Browser (localhost:3000)
  └─ Next.js 16 / React 19 ── HTTP JSON and multipart ──> FastAPI (127.0.0.1:8000)
                                                          ├─ MyGene.info / NCBI Entrez
                                                          ├─ UniProt / AlphaFold DB
                                                          ├─ NCBI BLAST
                                                          └─ SQLAlchemy ──> PostgreSQL
```

`frontend/src/app` contains App Router pages. `frontend/src/lib/api.ts` supplies the typed HTTP client. `backend/app/api/v1` registers FastAPI endpoints; `backend/app/bioinformatics` contains source clients and calculation services. SQLAlchemy models are under `backend/app/models`, and Alembic revisions are under `backend/migrations/versions`.

## Persistence

The current schema persists external gene and protein records in `gene_cache` and `protein_cache`. The current Sequence Laboratory computes results per request; BLAST request identifiers and results live only in a bounded in-process map. There is no account, project, notes, analysis history, or report persistence yet.

## Scientific provenance

Gene and protein responses identify their sources, retrieval time, and cache state. Sequence computations identify Biopython and their calculation method. BLAST hits are returned from NCBI and include RID-backed job state, identity, E-value, and query coverage. A cached response is labeled as cached; it is not a claim that the record was retrieved just now.

## Boundaries and known limits

- The app is local-first and does not depend on a hosted backend.
- CORS permits the configured local frontend origin.
- Authentication and authorization are not implemented.
- A BLAST job is lost after a backend restart and is visible to any local caller who knows its UUID.
- Structure metadata is available from protein annotations, but an interactive 3D viewer is not implemented.
- Future private project data must not be added until account/ownership enforcement is in place.
