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

## 2. Latest Verified Results (2026-11-07)

### Backend Test Suite (Pytest 9.2.0)

- **Total Test Cases**: 94
- **Passed**: 94 (100%)
- **Failed**: 0
- **Execution Time**: ~3.96 seconds
- **Platform**: Windows (win32), Python 3.12.10

#### Breakdown by Test Module:

| Test File | Tests | Status | Scope |
|---|:---:|:---:|---|
| `tests/test_config.py` | 11 | PASSED | Settings validation, cloud PostgreSQL URL normalization (`postgres://`, `postgresql://`, `+psycopg`), SQLite, invalid scheme rejection |
| `tests/test_database.py` | 3 | PASSED | SQLite in-memory test DB session, transaction rollback, model binding |
| `tests/test_databases.py` | 7 | PASSED | 11 core database connectors registry, parallel query execution, partial failure tolerance, categories, API endpoints |
| `tests/test_docking_v2.py` | 10 | PASSED | Receptor cleaning & PDBQT prep, ligand 3D conformer & Meeko PDBQT, pocket bounding boxes, Vina output parsing, contacts classifier, PDF/DOCX reports |
| `tests/test_health.py` | 8 | PASSED | `/health`, `/health/db`, `/api/v1/health`, database error masking, multi-origin CORS parsing, wildcard rejection, dev vs prod isolation |
| `tests/test_auth.py` | 5 | PASSED | User registration, duplicate checks, Argon2 password verification, JWT issuance, profile updates |
| `tests/test_projects.py` | 3 | PASSED | Multi-user research workspace CRUD, cross-entity saving, user data isolation |
| `tests/test_genes.py` | 7 | PASSED | MyGene.info mock client, gene search, details, cache retrieval, references |
| `tests/test_proteins.py` | 10 | PASSED | UniProt search, protein details, sequence analysis, structures, PDB/AlphaFold, cache |
| `tests/test_diseases.py` | 3 | PASSED | Open Targets Platform GraphQL client, disease search, targets, Europe PMC literature |
| `tests/test_compounds.py` | 3 | PASSED | PubChem PUG REST, ChEMBL mechanisms, Lipinski Rule of 5 evaluation, 3D SDF conformer |
| `tests/test_structures.py` | 3 | PASSED | RCSB PDB metadata, atomic PDB coordinate download, AlphaFold DB prediction metadata |
| `tests/test_docking.py` | 2 | PASSED | Biopython 3D PDB parser, ligand extraction, atomic distance contact matrix, pocket geometry, affinity scoring |
| `tests/test_assistant.py` | 3 | PASSED | Evidence-grounded scientific research assistant, MyGene/PubChem grounding, zero hallucination |
| `tests/test_reports.py` | 3 | PASSED | Publication-grade PDF generation via ReportLab, Microsoft Word DOCX via python-docx, project export |
| `tests/test_sequences.py` | 12 | PASSED | DNA/RNA/Protein validation, GC/AT content, FASTA parsing, multi-frame translation, pairwise alignment, mock BLAST submit/poll |

### Backend Static Analysis & Bytecode Compilation

- **Ruff Linter**: 0 errors across `app`, `tests`, and `migrations`.
- **Python `compileall`**: 0 syntax or import errors across all modules.
- **Alembic Schema Check**: `alembic check` clean (`No new upgrade operations detected`).

### Frontend Verification (Next.js 16.4.4 / Turbopack / React 19)

- **TypeScript (`npx tsc --noEmit`)**: 0 type errors.
- **ESLint (`npm run lint`)**: 0 warnings or errors.
- **Production Build (`npm run build`)**: Succeeded cleanly with all 20 routes:
  - `○ /` (Main scientific dashboard)
  - `○ /_not-found` (Custom 404 handler)
  - `○ /api-test` (API and database diagnostic utility)
  - `○ /assistant` (AI Research Assistant)
  - `○ /compounds` (Drug and Small Molecule Explorer)
  - `○ /databases` (Dynamic Scientific Database Hub - 11 Connectors)
  - `○ /diseases` (Disease Intelligence & Targets)
  - `○ /docking` (AutoDock Vina Molecular Docking Workbench)
  - `○ /genes` (Gene Intelligence module)
  - `○ /interactions` (Receptor-Ligand Contact Analysis)
  - `○ /login` (User Authentication)
  - `○ /projects` (Research Project Management)
  - `◐ /projects/[id]` (Project Detail Workspace)
  - `○ /proteins` (Protein Intelligence module)
  - `○ /register` (Account Registration)
  - `○ /reports` (Research Report Generator)
  - `○ /sequences` (Sequence Laboratory workspace)
  - `○ /structures` (Macromolecular Structure Explorer)

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
