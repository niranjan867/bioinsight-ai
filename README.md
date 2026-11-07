# BioInsight AI — AI-Powered Bioinformatics Research Platform

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162-teal.svg)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16.4-black.svg)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-19.3-blue.svg)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18.6-blue.svg)](https://www.postgresql.org/)
[![Biopython](https://img.shields.io/badge/Biopython-1.88-green.svg)](https://biopython.org/)
[![Tests](https://img.shields.io/badge/tests-65%20passed-brightgreen.svg)](docs/TESTING.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

BioInsight AI is a modern, local-first bioinformatics research platform built for life scientists, computational biologists, and researchers. It integrates gene exploration, protein characterization, and sequence analysis into a unified, high-performance workspace with explicit scientific provenance.

---

## Table of Contents

1. [Project Overview & Mission](#1-project-overview--mission)
2. [The Problem BioInsight Solves](#2-the-problem-bioinsight-solves)
3. [The Solution & Value Proposition](#3-the-solution--value-proposition)
4. [Core Features & Capabilities](#4-core-features--capabilities)
5. [Technology Stack](#5-technology-stack)
6. [Architecture & System Design](#6-architecture--system-design)
7. [Prerequisites & System Requirements](#7-prerequisites--system-requirements)
8. [Git Cloning & Workspace Setup](#8-git-cloning--workspace-setup)
9. [PostgreSQL Database Installation & Configuration](#9-postgresql-database-installation--configuration)
10. [Environment Variables Configuration](#10-environment-variables-configuration)
11. [Backend Startup & Operation](#11-backend-startup--operation)
12. [Frontend Startup & Operation](#12-frontend-startup--operation)
13. [Testing & Verification Guide](#13-testing--verification-guide)
14. [Scientific Data Sources & Methodology](#14-scientific-data-sources--methodology)
15. [Honest Status & Known Limitations](#15-honest-status--known-limitations)

---

## 1. Project Overview & Mission

BioInsight AI addresses the fragmentation of modern biological data science by providing a centralized, local-first platform that connects directly to authoritative scientific databases while running algorithms locally.

### Key Tenets
- **Data Provenance First**: Every retrieved biological record, structure reference, and computational result clearly identifies its source (e.g., UniProtKB, AlphaFold DB, NCBI Entrez, or local Biopython execution).
- **Local-First & Privacy Conscious**: Runs entirely on your local machine using standard Python and Node.js runtimes with a local PostgreSQL database. No mandatory cloud accounts, third-party tracking, or GPU hardware are required.
- **Scientific Rigor**: No synthesized or "hallucinated" biological facts. When an upstream service is unavailable or a sequence contains ambiguous residues, the platform reports the exact constraints rather than guessing.

---

## 2. The Problem BioInsight Solves

Life science researchers face several daily operational friction points:
1. **Tool and Database Fragmentation**: Investigating a single target typically requires toggling between NCBI Entrez, UniProtKB, RCSB PDB, AlphaFold DB, and command-line BLAST tools.
2. **Ambiguity in Structural Confidence**: Predictions from deep learning models (e.g., AlphaFold) are frequently confused with experimentally solved structures from X-ray crystallography or cryo-EM.
3. **Complex Local Environments**: Setting up traditional bioinformatics toolchains often involves brittle dependencies, incompatible Biopython wrappers, and inconsistent database drivers.
4. **Data Privacy**: Researchers working on proprietary or sensitive sequences often cannot upload unreleased genetic data to opaque public cloud web tools.

---

## 3. The Solution & Value Proposition

BioInsight AI solves these issues through a clean, unified architecture:
- **Centralized Workflows**: Search genes, inspect UniProt proteins, calculate sequence metrics, perform translations across 6 reading frames, align pairs, and query NCBI BLAST from a single interface.
- **Explicit Evidence Categorization**: Structural data explicitly separates experimental PDB coordinates (resolution, deposition method) from computational AlphaFold predictions (pLDDT confidence scores).
- **One-Command Local Setup**: Robust PowerShell and Python setup automation provisions isolated virtual environments, configures PostgreSQL databases safely, and runs migrations without manual friction.
- **Local Computational Pipeline**: Sequence transformations, composition analyses, and alignments execute locally in-memory using Biopython and NumPy.

---

## 4. Core Features & Capabilities

### A. Gene Intelligence (`/genes`)
- **Multi-Source Gene Search**: Search by official symbol (e.g., `BRCA1`, `TP53`, `EGFR`), full gene name, or alias using MyGene.info and NCBI Entrez.
- **Comprehensive Annotation**: View chromosomal coordinates, genomic locations, Ensembl identifiers, Entrez Gene IDs, and curated summaries.
- **Smart Database Caching**: High-throughput queries are cached in PostgreSQL (`gene_cache` table) with retrieval timestamps and transparent cache-hit indicators.

### B. Protein Intelligence (`/proteins`)
- **UniProtKB Accession & Keyword Search**: Query UniProtKB with organism filtering (e.g., `Homo sapiens`).
- **Functional Annotation**: Access recommended protein names, gene associations, biological functions, subcellular localizations, and external database cross-references.
- **Physicochemical Properties**: Real-time computational analysis via Biopython:
  - Molecular weight ($Da$)
  - Theoretical Isoelectric Point ($pI$)
  - Instability Index (in vivo stability classification)
  - Grand Average of Hydropathicity (GRAVY)
  - Aromaticity score
- **Dual Structural Perspective**:
  - **Experimental Structures**: RCSB PDB cross-references with experimental determination methods (X-ray, NMR, Cryo-EM) and resolutions.
  - **Computational Predictions**: AlphaFold DB accessions with prediction confidence scores.
- **Local Caching**: Responses are stored in PostgreSQL (`protein_cache` table) with explicit bypass support (`force_refresh=true`).

### C. Sequence Laboratory (`/sequences`)
- **Multi-Type Sequence Validation**: Validates DNA, RNA, and amino acid sequences with full support for IUPAC ambiguity characters.
- **Physicochemical Metrics**: Calculates length, nucleotide composition, GC content, AT content, and CpG dinucleotide counts.
- **Biological Transformations**:
  - Reverse complement
  - Transcription (DNA $\rightarrow$ RNA)
  - Back-transcription (RNA $\rightarrow$ DNA)
- **Multi-Frame Translation**: Translates sequences across reading frames (+1, +2, +3, -1, -2, -3, or all six simultaneously) with configurable standard and vertebrate mitochondrial genetic codes.
- **Pairwise Alignment**:
  - Global alignment (Needleman-Wunsch algorithm)
  - Local alignment (Smith-Waterman algorithm)
  - Customizable match score, mismatch penalty, and open/extend gap costs.
- **NCBI BLAST Integration**:
  - Asynchronous submission to NCBI QBlast server (`blastn`, `blastp`).
  - Safe background status polling (`WAITING`, `READY`, `FAILED`).
  - Structured extraction of top hits: accession, title, E-value, bit score, and query coverage.
- **FASTA File Ingestion**: Upload multi-record FASTA files (up to 2 MiB) with automatic header and sequence parsing.

### D. Disease Intelligence (`/diseases`)
- **Open Targets Platform**: Query disease targets, therapeutic areas, and clinical phenotype associations.
- **Europe PMC Literature**: Search peer-reviewed biomedical literature and PubMed identifiers directly associated with the disease.
- **PostgreSQL Caching**: Search results and entity details cached in `disease_cache` table.

### E. Drug & Compound Intelligence (`/compounds`)
- **PubChem PUG REST API**: Query chemical compounds by name, CID, or SMILES.
- **Physicochemical Properties**: Molecular weight, canonical SMILES, InChIKey, XLogP, TPSA, H-bond donors/acceptors, rotatable bonds.
- **Lipinski's Rule of 5**: Evaluates small-molecule oral druglikeness (MW $\le 500$, LogP $\le 5.0$, H-donors $\le 5$, H-acceptors $\le 10$).
- **ChEMBL Cross-References**: Pharmacological mechanisms of action, clinical indications, and biological targets.
- **3D Conformer Download**: Export standard 3D SDF coordinate files and 2D chemical structure diagrams.

### F. Macromolecular Structure Explorer (`/structures`)
- **Experimental Structures (RCSB PDB)**: Resolution, experimental determination method (X-ray, cryo-EM, NMR), polymer chains, and bound ligands.
- **Computational Predictions (AlphaFold DB)**: Whole-organism deep-learning structure predictions with per-residue pLDDT confidence categories.
- **3D WebGL Visualization**: Embedded 3Dmol.js viewer supporting cartoon, stick, sphere, and solvent-accessible surface representations with spectrum and chain coloring.
- **Atomic Coordinate Export**: Download raw `.pdb` files for molecular modeling.

### G. Protein-Ligand Interaction & Docking Laboratory (`/interactions`)
- **Hetero-Residue Ligand Extraction**: Automatically isolates non-water bound co-factors, drugs, and prosthetic groups (e.g. HEM, STI, ATP).
- **3D Atomic Distance Matrix**: Biopython Euclidean distance calculations between ligand and macromolecular binding residues within a configurable radius ($2.5 - 7.0\,\text{Å}$).
- **Contact Classification**: Identifies hydrogen bonds, hydrophobic interactions, salt bridges, and van der Waals contacts.
- **Binding Pocket Geometry**: Pocket centroid coordinates ($X, Y, Z$), radius, and estimated cavity volume ($\text{Å}^3$).
- **Empirical Affinity Scoring**: Estimated binding free energy ($\Delta G$ in $\text{kcal/mol}$) and interaction quality index.

### H. Research Project Management (`/projects`)
- **Multi-Project Workspace**: Create and organize multi-omics research projects.
- **Cross-Entity Bookmarking**: Save genes, proteins, compounds, diseases, 3D structures, and custom notes directly into projects.
- **Audit Logging**: Comprehensive activity stream recording every bookmark, note, and update.

### I. Multi-User Authentication & Security (`/login`, `/register`)
- **Secure Registration & Login**: User identity management with Argon2 password hashing (`argon2-cffi` + `pwdlib`).
- **Stateless JWT Authorization**: Signed tokens (HS256) propagated via `Authorization: Bearer` headers.
- **Tenant Data Isolation**: Research projects and saved datasets are strictly isolated per authenticated user.

### J. Grounded AI Research Assistant (`/assistant`)
- **Evidence-Grounded Intelligence**: Synthesizes real biological facts from local PostgreSQL caches and authoritative APIs (MyGene, UniProt, PubChem, Open Targets).
- **Verifiable Citations**: Every generated finding includes database sources, accession identifiers, and outbound links.
- **Zero Hallucination Policy**: Refuses to speculate or invent biological targets or sequences.

### K. Publication-Grade Research Report Generator (`/reports`)
- **PDF Generation via ReportLab**: Generates clean, publication-grade research reports with executive summaries, structured tables, and references.
- **Microsoft Word DOCX via python-docx**: Generates editable Word documents for collaboration and grant applications.
- **Project Dataset Export**: One-click complete project dossier exports.

### L. System Diagnostics & Dashboard (`/`, `/api-test`)
- **Operational Monitoring**: Real-time round-trip latency checks for both FastAPI backend and PostgreSQL database.
- **Diagnostic Inspector**: Direct JSON inspection of API health endpoints.

---

## 5. Technology Stack

### Backend
- **Language**: Python 3.12
- **Framework**: FastAPI 0.162 (Asynchronous ASGI)
- **Validation**: Pydantic 2.x
- **Database ORM**: SQLAlchemy 2.x
- **Database Driver**: `psycopg` (Version 3)
- **Database Migrations**: Alembic 1.20
- **Scientific Computing**: Biopython 1.88, NumPy 2.x
- **Authentication**: Argon2 (`pwdlib`, `argon2-cffi`), PyJWT
- **Report Generation**: ReportLab 5.1 (PDF), python-docx 1.2 (DOCX)
- **HTTP Client**: HTTPX 0.28 (Async connection pooling)
- **ASGI Server**: Uvicorn 0.54

### Frontend
- **Framework**: Next.js 16.4.4 (App Router, Turbopack)
- **Library**: React 19.3.0
- **Language**: TypeScript 5.x (Strict mode)
- **Styling**: Tailwind CSS 4, Lucide React icons
- **3D Molecular Viewing**: 3Dmol.js (WebGL)
- **Components**: Radix UI / shadcn design system patterns

### Database & Storage
- **Database**: PostgreSQL 18.6
- **Cache Persistence**: Relational JSONB & text storage in PostgreSQL

---

## 6. Architecture & System Design

### Architecture Diagram

```mermaid
flowchart TD
    User["Researcher / Client Browser\nhttp://localhost:3000"]
    
    subgraph Frontend["Next.js 16 App Router (Port 3000)"]
        Dashboard["Dashboard (/)"]
        GeneUI["Gene Intel (/genes)"]
        ProteinUI["Protein Intel (/proteins)"]
        SeqUI["Sequence Lab (/sequences)"]
        ApiClient["Typed API Client\n(src/lib/api.ts)"]
        Dashboard --> ApiClient
        GeneUI --> ApiClient
        ProteinUI --> ApiClient
        SeqUI --> ApiClient
    end

    subgraph Backend["FastAPI REST Backend (Port 8000)"]
        RouterHealth["/health & /health/db"]
        RouterGenes["/api/v1/genes"]
        RouterProteins["/api/v1/proteins"]
        RouterSequences["/api/v1/sequences"]
        
        subgraph BioinformaticsCore["Bioinformatics Core"]
            BioSeq["Biopython Sequence Engine\n(Metrics, Translation, Alignment)"]
            ClientGenes["MyGene.info / NCBI Client"]
            ClientProteins["UniProt / AlphaFold Client"]
            ClientBlast["NCBI QBlast Handler"]
        end
        
        RouterGenes --> ClientGenes
        RouterProteins --> ClientProteins
        RouterProteins --> BioSeq
        RouterSequences --> BioSeq
        RouterSequences --> ClientBlast
    end

    subgraph StorageLayer["Data & Persistence"]
        PG[("PostgreSQL 18\n(gene_cache, protein_cache)")]
    end

    subgraph ExternalAPIs["Official Biological APIs"]
        MyGene["MyGene.info REST"]
        NCBI["NCBI Entrez & BLAST"]
        UniProt["UniProtKB REST"]
        AlphaFold["AlphaFold DB"]
    end

    User <--> Frontend
    ApiClient <-->|HTTP / JSON| Backend
    ClientGenes <-->|HTTPS| MyGene
    ClientGenes <-->|HTTPS| NCBI
    ClientProteins <-->|HTTPS| UniProt
    ClientProteins <-->|HTTPS| AlphaFold
    ClientBlast <-->|HTTPS| NCBI
    Backend <-->|SQLAlchemy + psycopg| PG
```

### Repository Structure

```text
bioinsight-ai/
├── .env.example              # Monorepo environment documentation template
├── .gitignore                # Git exclusions (secrets, .venv, .next, node_modules)
├── README.md                 # Master project documentation
├── backend/
│   ├── alembic.ini           # Alembic migration configuration
│   ├── pytest.ini            # Pytest execution settings
│   ├── requirements.txt      # Direct Python runtime and dev dependencies
│   ├── app/
│   │   ├── main.py           # FastAPI application entrypoint & CORS
│   │   ├── api/v1/           # API version 1 route definitions
│   │   │   ├── genes.py      # Gene intelligence endpoints
│   │   │   ├── health.py     # Health and diagnostic checks
│   │   │   ├── proteins.py   # Protein intelligence endpoints
│   │   │   └── sequences.py  # Sequence laboratory endpoints
│   │   ├── bioinformatics/   # Scientific computational modules
│   │   │   ├── genes/        # MyGene / NCBI services, schemas, and cache
│   │   │   ├── proteins/     # UniProt / AlphaFold clients & Biopython analyzers
│   │   │   └── sequences/    # Validation, translation, alignment, BLAST services
│   │   ├── core/             # Application configuration & Pydantic settings
│   │   ├── database/         # Database engine, session maker, base model
│   │   └── models/           # SQLAlchemy ORM models (gene_cache, protein_cache)
│   ├── migrations/           # Alembic versions and migration environment
│   └── tests/                # 40 Pytest unit and integration tests
├── frontend/
│   ├── package.json          # Node dependencies and build scripts
│   ├── tsconfig.json         # TypeScript compiler configuration
│   └── src/
│       ├── app/              # Next.js 16 App Router pages
│       │   ├── page.tsx      # Main research dashboard
│       │   ├── api-test/     # Backend connectivity diagnostic page
│       │   ├── genes/        # Gene Intelligence UI
│       │   ├── proteins/     # Protein Intelligence UI
│       │   └── sequences/    # Sequence Laboratory UI
│       ├── components/       # UI components (app shell, sidebar, widgets)
│       └── lib/              # Frontend API client and utility functions
├── docs/                     # Comprehensive architecture and operation manuals
├── scripts/                  # Automated PowerShell and Python setup scripts
└── storage/                  # Local storage placeholders (cache, uploads, reports)
```

---

## 7. Prerequisites & System Requirements

BioInsight AI is developed and validated for **Windows 11** (also compatible with Linux / macOS).

### Required Software
1. **Operating System**: Windows 11 (64-bit) with PowerShell 5.1 or PowerShell 7+
2. **Python**: Python 3.12.x with the Python Launcher (`py`) installed and added to `PATH`
3. **Node.js**: Node.js 20.9.x LTS or higher (with `npm`)
4. **PostgreSQL**: PostgreSQL 18.x (or 16+) running locally on port 5432
5. **Git**: Git for Windows

You can verify your environment prerequisites automatically by running:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_environment.ps1
```

---

## 8. Git Cloning & Workspace Setup

Clone the repository to your local drive:

```powershell
# Clone the repository
git clone https://github.com/niranjan867/bioinsight-ai.git

# Navigate into the project root
Set-Location .\bioinsight-ai
```

---

## 9. PostgreSQL Database Installation & Configuration

BioInsight AI requires a local PostgreSQL instance.

### Step 1: Start PostgreSQL
Ensure your PostgreSQL Windows service is running (e.g., via Windows Services `services.msc` or `pg_ctl`).

### Step 2: Create Application User and Database
Open `psql` as the `postgres` superuser:

```powershell
psql -U postgres
```

Execute the following SQL statements:

```sql
-- Create a dedicated application role
CREATE USER bioinsight_app WITH PASSWORD 'your_secure_password';

-- Create the application database owned by the application role
CREATE DATABASE bioinsight_db OWNER bioinsight_app;

-- Grant schema privileges
GRANT ALL PRIVILEGES ON DATABASE bioinsight_db TO bioinsight_app;
\connect bioinsight_db
GRANT ALL ON SCHEMA public TO bioinsight_app;
\q
```

### Step 3: Interactive Database Configuration Helper
You can also use the included Python helper to test and verify your database credentials:

```powershell
cd backend
.\.venv\Scripts\python.exe ..\scripts\configure_db.py
cd ..
```

---

## 10. Environment Variables Configuration

The project uses decoupled configuration files that are strictly excluded from source control:

### Backend Configuration (`backend/.env`)
Create `backend/.env` from the provided template:

```powershell
Copy-Item backend\.env.example backend\.env
```

Edit `backend/.env`:
```ini
APP_NAME=BioInsight AI
APP_ENV=development
DEBUG=true

# Database connection string (PostgreSQL with psycopg3 driver)
DATABASE_URL=postgresql+psycopg://bioinsight_app:your_secure_password@127.0.0.1:5432/bioinsight_db

# Security & Tokens
JWT_SECRET_KEY=generate_a_random_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage Limits
STORAGE_PATH=../storage
MAX_UPLOAD_SIZE_MB=25

# Allowed CORS Origin
FRONTEND_URL=http://localhost:3000

# NCBI Contact (Required for NCBI BLAST queries)
NCBI_EMAIL=your-email@example.org
NCBI_TOOL=BioInsightAI
```

### Frontend Configuration (`frontend/.env.local`)
Create `frontend/.env.local` from the provided template:

```powershell
Copy-Item frontend\.env.example frontend/.env.local
```

Edit `frontend/.env.local`:
```ini
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

## 11. Backend Startup & Operation

### Automated Setup
To automatically create the Python virtual environment, install dependencies, and run database migrations:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

### Manual Startup
To run the backend independently:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_backend.ps1
```

Or from the command line:
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend exposes:
- **Health Check**: `http://127.0.0.1:8000/health`
- **Database Diagnostic**: `http://127.0.0.1:8000/api/v1/health/db`
- **Interactive OpenAPI Documentation**: `http://127.0.0.1:8000/docs`

---

## 12. Frontend Startup & Operation

### Manual Startup
To run the Next.js development server:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend.ps1
```

Or from the command line:
```powershell
cd frontend
npm run dev
```

Visit the application at:
- **Main Dashboard**: `http://localhost:3000`
- **Gene Intelligence**: `http://localhost:3000/genes`
- **Protein Intelligence**: `http://localhost:3000/proteins`
- **Sequence Laboratory**: `http://localhost:3000/sequences`
- **API Diagnostics**: `http://localhost:3000/api-test`

### Start Both Services Simultaneously
To launch both backend and frontend servers in independent PowerShell windows:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_all.ps1
```

---

## 13. Testing & Verification Guide

BioInsight AI includes an extensive automated test suite with full coverage across all implemented features.

### Run All Backend Tests (Pytest)
```powershell
cd backend
.\.venv\Scripts\pytest.exe -v
```
*Current status*: **40 passed** in ~0.78s across 6 test modules:
- `test_config.py` (3 tests)
- `test_database.py` (3 tests)
- `test_health.py` (5 tests)
- `test_genes.py` (7 tests)
- `test_proteins.py` (10 tests)
- `test_sequences.py` (12 tests)

### Run Code Linter (Ruff)
```powershell
cd backend
.\.venv\Scripts\ruff.exe check app tests migrations
```
*Current status*: **0 errors**.

### Run Database Migration Verification (Alembic)
```powershell
cd backend
.\.venv\Scripts\alembic.exe check
```
*Current status*: `No new upgrade operations detected`.

### Run Frontend Static Type Checking & Linting
```powershell
cd frontend
npx tsc --noEmit
npm run lint
```
*Current status*: **0 errors / 0 warnings**.

### Production Frontend Build
```powershell
cd frontend
npm run build
```
*Current status*: Compiled successfully; all 8 static routes generated cleanly.

---

## 14. Scientific Data Sources & Methodology

| Biological Source / Method | Role in BioInsight AI | Provenance Policy |
|---|---|---|
| **MyGene.info REST API** | Gene search, symbol lookup, genomic coordinates | Database annotation; records timestamped and cached. |
| **NCBI Entrez E-Utilities** | Cross-referencing and gene summaries | Official NCBI Gene IDs and curated summaries. |
| **UniProtKB REST API** | Protein sequences, functional descriptions, subcellular locations | Primary reference for protein sequence and ontology annotations. |
| **Biopython `ProtParam`** | Physicochemical properties (MW, pI, instability, GRAVY) | Deterministic local computation using standard biological formulas. |
| **Biopython `PairwiseAligner`** | Global and local sequence alignment | Deterministic local algorithm (Needleman-Wunsch & Smith-Waterman). |
| **RCSB PDB** | Experimental 3D structural references | Categorized explicitly as **experimental evidence** with resolution and technique. |
| **AlphaFold DB** | Predicted 3D structural models | Categorized explicitly as **computational prediction** with model confidence. |
| **NCBI QBlast** | Remote sequence similarity search (`blastn`, `blastp`) | Remote NCBI asynchronous computation. |

---

## 15. Honest Status & Known Limitations

To maintain scientific integrity, BioInsight AI distinguishes between implemented, working capabilities and planned future work:

### Currently Operational
- Full Gene Intelligence workflow (Search, details, coordinates, caching).
- Full Protein Intelligence workflow (UniProt search, details, Biopython metrics, PDB & AlphaFold metadata, caching).
- Full Sequence Laboratory (Validation, composition, reverse complement, transcription, 6-frame translation, pairwise alignment, FASTA upload, NCBI BLAST).
- Real-time diagnostic dashboard and API latency monitoring.
- Windows automation scripts and PostgreSQL migration pipeline.

### Incomplete / Planned for Future Milestones
- **Disease Intelligence**: Open Targets and Europe PMC integrations are planned (Milestone 18).
- **Compound & Drug Intelligence**: PubChem and ChEMBL integrations are planned (Milestone 19).
- **Interactive 3D Molecular Viewer**: Embedded Mol* / 3Dmol.js viewer is planned (Milestone 20).
- **Protein-Ligand Analysis**: Docking and binding pocket predictions are planned (Milestone 21).
- **User Authentication & RBAC**: Multi-user registration, logins, and project access controls are not yet active.
- **Project Workspaces & Notebooks**: Persistent user notebook storage is planned for a subsequent milestone.
- **Report Generation**: Export to PDF / DOCX is planned for a subsequent milestone.

---

## Documentation Links

For further architectural and operational details, consult the `docs/` directory:
- [Windows Setup for New Developers](docs/FRIEND_SETUP_GUIDE.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Scientific Data Sources](docs/SCIENTIFIC_DATA_SOURCES.md)
- [Testing & Quality Gates](docs/TESTING.md)
- [Security & Privacy Guide](docs/SECURITY.md)
- [Troubleshooting Manual](docs/TROUBLESHOOTING.md)
- [Current Repository Audit](docs/PROJECT_AUDIT.md)
- [Development Progress](docs/DEVELOPMENT_PROGRESS.md)
- [Final Project Report](docs/FINAL_PROJECT_REPORT.md)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
