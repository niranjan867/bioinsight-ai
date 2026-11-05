# Testing and Verification Guide

This document describes the testing strategy, test suites, quality gates, and verified execution results for BioInsight AI across both backend and frontend layers.

---

## 1. Quality Gates and Verification Commands

### Backend Verification (Python 3.12)

Run from `backend/`:

```powershell
# Run all unit and integration tests
.\.venv\Scripts\pytest.exe -v

# Run code style, syntax, and import validation
.\.venv\Scripts\ruff.exe check app tests migrations

# Verify bytecode compilation across all modules
.\.venv\Scripts\python.exe -m compileall app tests migrations

# Verify database schema against SQLAlchemy models
.\.venv\Scripts\alembic.exe check
```

### Frontend Verification (Next.js 16 / TypeScript / React 19)

Run from `frontend/`:

```powershell
# TypeScript strict type checking
npx tsc --noEmit

# ESLint validation (including React 19 hooks and Next.js rules)
npm run lint

# Production build and static page optimization
npm run build
```

---

## 2. Latest Verified Results (2026-11-05)

### Backend Test Suite (Pytest 9.2.0)

- **Total Test Cases**: 40
- **Passed**: 40 (100%)
- **Failed**: 0
- **Execution Time**: ~0.78 seconds
- **Platform**: Windows (win32), Python 3.12.10

#### Breakdown by Test Module:

| Test File | Tests | Status | Scope |
|---|:---:|:---:|---|
| `tests/test_config.py` | 3 | PASSED | Settings validation, default values, env overrides |
| `tests/test_database.py` | 3 | PASSED | SQLite in-memory test DB session, transaction rollback, model binding |
| `tests/test_health.py` | 5 | PASSED | `/health`, `/health/db`, `/api/v1/health`, database error masking |
| `tests/test_genes.py` | 7 | PASSED | MyGene.info mock client, gene search, details, cache retrieval, references |
| `tests/test_proteins.py` | 10 | PASSED | UniProt search, protein details, sequence analysis, structures, PDB/AlphaFold, cache |
| `tests/test_sequences.py` | 12 | PASSED | DNA/RNA/Protein validation, GC/AT content, FASTA parsing, multi-frame translation, pairwise alignment, mock BLAST submit/poll |

### Backend Static Analysis & Bytecode Compilation

- **Ruff Linter**: 0 errors across `app`, `tests`, and `migrations`.
- **Python `compileall`**: 0 syntax or import errors across all modules.
- **Alembic Schema Check**: `alembic check` clean (`No new upgrade operations detected`).

### Frontend Verification (Next.js 16.4.4 / Turbopack)

- **TypeScript (`npx tsc --noEmit`)**: 0 type errors.
- **ESLint (`npm run lint`)**: 0 warnings or errors.
- **Production Build (`npm run build`)**: Succeeded in ~785ms.
- **Generated Routes** (8 static pages):
  - `○ /` (Main scientific dashboard)
  - `○ /_not-found` (Custom 404 handler)
  - `○ /api-test` (API and database diagnostic utility)
  - `○ /genes` (Gene Intelligence module)
  - `○ /proteins` (Protein Intelligence module)
  - `○ /sequences` (Sequence Laboratory workspace)

---

## 3. Scientific Mocking and External Service Testing

External biological databases (MyGene.info, UniProtKB, NCBI BLAST, AlphaFold DB) are mocked during automated unit testing using `unittest.mock` and `respx`/custom mock handlers:
- **MyGene.info**: Mocked response fixtures for BRCA1 and TP53.
- **UniProtKB**: Mocked JSON payloads for P68871 (Hemoglobin subunit beta) and P04637 (P53).
- **NCBI BLAST**: Submissions return mocked request IDs (RIDs); polling responses simulate `WAITING` and `READY` states with sample BLAST XML hits.
- **Biopython**: Tested directly against true biological sequences without mocking to verify algorithmic correctness (pI, molecular weight, instability index, global/local pairwise alignment, 6-frame translation).

---

## 4. Test Environment Isolation

- Unit tests execute against an isolated in-memory SQLite database (`sqlite:///:memory:`) using SQLAlchemy's `StaticPool` to ensure zero state leakage between tests.
- Real PostgreSQL integration tests and migration checks are executed independently against `127.0.0.1:5432/bioinsight_db`.
