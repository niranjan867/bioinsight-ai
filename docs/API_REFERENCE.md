# API reference

Interactive OpenAPI documentation is served at `http://127.0.0.1:8000/docs` in local development.

## Health

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Backend process health |
| GET | `/health/db` | Execute `SELECT 1` against configured database |
| GET | `/api/v1/health` | API version health |
| GET | `/api/v1/health/db` | Versioned database health |

## Genes

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/genes/search?q=BRCA1&species=human` | Search MyGene.info/NCBI-backed gene records |
| GET | `/api/v1/genes/{gene_id}` | Retrieve details; `force_refresh=true` bypasses the cache |
| GET | `/api/v1/genes/{gene_id}/references` | Retrieve database references |

## Proteins

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/proteins/search?q=hemoglobin&species=human` | Search UniProtKB |
| GET | `/api/v1/proteins/{accession}` | Protein detail; optional `force_refresh=true` |
| GET | `/api/v1/proteins/{accession}/sequence` | FASTA and Biopython properties |
| GET | `/api/v1/proteins/{accession}/structures` | Experimental PDB references and AlphaFold metadata |
| GET | `/api/v1/proteins/{accession}/references` | Protein cross references |

## Sequence Laboratory

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/sequences/analyze` | Analyze raw sequence or multi-record FASTA; JSON fields: `sequence`, `sequence_type`, optional `genetic_code` |
| POST | `/api/v1/sequences/upload?sequence_type=dna` | Analyze a UTF-8 FASTA file (2 MiB maximum) |
| POST | `/api/v1/sequences/translate?frame=six` | Translate DNA/RNA using the chosen genetic code; frame can be 1, 2, 3, -1, -2, -3, or `six` |
| POST | `/api/v1/sequences/align` | Global or local pairwise alignment with configurable match/mismatch/gap scores |
| POST | `/api/v1/sequences/blast` | Submit a one-record DNA/protein search to NCBI; returns HTTP 202 and a local `job_id` |
| GET | `/api/v1/sequences/blast/{job_id}` | Poll NCBI status and parsed hits |

Sequence analysis supports DNA/RNA IUPAC ambiguity codes. Submitted direct text is returned as `input_sequence`; `normalized_sequence` removes whitespace and uppercases letters. Protein physicochemical values are omitted for ambiguous/stop-containing sequences. BLAST requires `NCBI_EMAIL` and an internet connection.

Disease, compounds, projects, auth, reports, and AI routes are not implemented.
