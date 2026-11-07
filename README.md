# BioInsight AI 2.0 — AI-Powered Bioinformatics & Molecular Discovery Platform

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162-teal.svg)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16.4-black.svg)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-19.3-blue.svg)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18.6-blue.svg)](https://www.postgresql.org/)
[![AutoDock Vina](https://img.shields.io/badge/AutoDock%20Vina-1.2.5-orange.svg)](https://vina.scripps.edu/)
[![RDKit](https://img.shields.io/badge/RDKit-2026.9-brightgreen.svg)](https://www.rdkit.org/)
[![Biopython](https://img.shields.io/badge/Biopython-1.88-green.svg)](https://biopython.org/)
[![Tests](https://img.shields.io/badge/tests-94%20passed-brightgreen.svg)](docs/TESTING.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

BioInsight AI 2.0 is an enterprise-grade, local-first bioinformatics research and molecular discovery platform built for life scientists, medicinal chemists, and computational biologists. It integrates multi-omics intelligence, an extensible 11-database federated query hub, a turnkey AutoDock Vina molecular docking workbench with interactive 3D WebGL visualization, and automated publication-grade PDF/DOCX research reporting.

---

## Table of Contents

1. [Project Overview & Problem Statement](#1-project-overview--problem-statement)
2. [Target Audience & Key Benefits](#2-target-audience--key-benefits)
3. [Core Platform Features](#3-core-platform-features)
4. [System Architecture](#4-system-architecture)
5. [Technology Stack](#5-technology-stack)
6. [Prerequisites & System Requirements](#6-prerequisites--system-requirements)
7. [Step-by-Step Installation & Setup](#7-step-by-step-installation--setup)
8. [AutoDock Vina Configuration & Docking Walkthrough](#8-autodock-vina-configuration--docking-walkthrough)
9. [Environment Variable Configuration](#9-environment-variable-configuration)
10. [Running Automated Tests](#10-running-automated-tests)
11. [Supported Production Deployment Architecture](#11-supported-production-deployment-architecture)
12. [Scientific Reproducibility & Responsibility](#12-scientific-reproducibility--responsibility)
13. [Scientific Attribution & Third-Party Licenses](#13-scientific-attribution--third-party-licenses)
14. [Documentation Links](#14-documentation-links)

---

## 1. Project Overview & Problem Statement

Modern biomedical research is severely hindered by **tool and database fragmentation**:

- **Siloed Resources**: Investigating a single biological target requires juggling between NCBI Entrez, UniProtKB, RCSB PDB, AlphaFold DB, PubChem, and command-line BLAST tools.
- **Structural Ambiguity**: Deep-learning predictions (AlphaFold pLDDT scores) are frequently conflated with experimentally determined crystallographic coordinates (X-ray resolution, cryo-EM).
- **Environment Fragility**: Computational chemistry environments often suffer from conflicting C++ binaries, brittle Biopython wrappers, and heavy Docker virtualization overhead.
- **Data Privacy & IP Risks**: Researchers handling proprietary candidate sequences or unreleased chemical scaffolds cannot upload sensitive intellectual property to opaque cloud web services.

### The BioInsight AI 2.0 Solution

BioInsight AI 2.0 unifies these disparate workflows into a single, high-performance platform running natively on local workstations or private institutional servers. It combines:
1. **Parallel Federated Querying**: Concurrently queries 11 authoritative biological databases in parallel with partial failure tolerance.
2. **Deterministic Local Computing**: Sequence translations, alignments, physicochemical metrics, and Lipinski rule evaluations execute locally using Biopython, RDKit, and NumPy.
3. **Native AutoDock Vina Molecular Docking**: Real in silico protein–ligand docking executed via native C++ binaries with RDKit conformer minimization, Meeko torsion trees, and 3D WebGL contact visualization.
4. **Data Isolation & Traceability**: Clear evidence provenance tagging, PostgreSQL persistent job tracking, and publication-ready PDF/DOCX reporting.

---

## 2. Target Audience & Key Benefits

| User Group | Primary Use Cases | Key Benefits in BioInsight AI 2.0 |
|---|---|---|
| **Medicinal Chemists** | Small-molecule screening, Lipinski druglikeness, protein–ligand docking | Real AutoDock Vina docking scores ($\Delta G$), 3D pose cycling, and interaction contact profiling. |
| **Computational Biologists** | Sequence analysis, 6-frame translation, pairwise alignment, BLAST | Local Biopython algorithms; no rate limits or data leakage for proprietary sequences. |
| **Genomics & Proteomics Researchers** | Target discovery, functional annotations, genomic coordinate mapping | Federated search across UniProtKB, NCBI, Ensembl, and Open Targets in a single view. |
| **Structural Biologists** | PDB structures, AlphaFold models, binding cavity geometry | 3D WebGL rendering with 3Dmol.js; transparent separation between experimental PDB and predicted AlphaFold data. |
| **Academic Educators & Students** | Teaching structural bioinformatics and drug design | Turnkey setup without Docker; interactive visual feedback for chemical and macromolecular principles. |

---

## 3. Core Platform Features

### A. Dynamic Scientific Database Hub (`/databases`)
- **Federated Parallel Querying**: Concurrently queries **11 authoritative biological databases**: RCSB PDB, UniProtKB, PubChem, NCBI Entrez, PDBe, AlphaFold DB, ChEMBL, Europe PMC, Open Targets, Ensembl, and Reactome.
- **Resilient Execution**: Non-blocking `asyncio.gather` with partial failure tolerance—unresponsive external services do not interrupt healthy connectors.
- **Domain Categorization**: Results grouped into Macromolecules, Sequences, Chemistry & Drugs, Diseases & Literature, and Pathways & Targets.
- **Raw Inspection**: Normalized search metadata, external outbound links, and raw JSON modal inspection.

### B. AutoDock Vina Molecular Docking Platform (`/docking`)
- **Native Scripps AutoDock Vina v1.2.5**: High-performance local docking execution natively on Windows, Linux, and macOS without Docker.
- **Cheminformatics Preparation Pipeline**:
  - **Receptor**: Biopython parsing, crystallographic water removal, heteroatom filtering, and AutoDock PDBQT formatting.
  - **Ligand**: RDKit ETKDGv3 3D conformer generation from canonical SMILES, Universal Force Field (UFF) energy minimization, Gasteiger partial charges, and Meeko torsion tree conversion.
- **Three Search Space Modes**:
  - Bound ligand centroid with adjustable bounding padding ($4.0 - 10.0\,\text{\AA}$).
  - Catalytic/active residue selection with automated bounding box calculation.
  - Full manual coordinate specification ($X, Y, Z$ center and box dimensions).
- **Interatomic Contact Classification**: Euclidean distance geometric profiling identifying hydrogen bonds ($\le 3.5\,\text{\AA}$), hydrophobic interactions ($\le 4.0\,\text{\AA}$), and electrostatic salt bridges ($\le 4.0\,\text{\AA}$).
- **Interactive 3D WebGL Visualization**: Embedded 3Dmol.js viewer rendering secondary structure cartoons, ligand stick conformers, wireframe bounding box, and colored 3D interatomic contact lines.
- **Background Worker & Resilience**: Jobs processed in a background thread pool with automatic startup reconciliation for interrupted jobs.
- **Publication-Ready Docking Reports**: One-click PDF and DOCX export with parameters, ranked binding poses table, active site contact profile, methodology, and citations.

### C. Gene Intelligence (`/genes`)
- **Multi-Source Gene Search**: Search by official symbol (e.g., `BRCA1`, `TP53`, `EGFR`), full name, or alias using MyGene.info and NCBI Entrez.
- **Comprehensive Annotation**: View chromosomal coordinates, genomic locations, Ensembl identifiers, Entrez Gene IDs, and curated summaries.
- **Database Caching**: High-throughput queries are cached in PostgreSQL (`gene_cache` table) with retrieval timestamps.

### D. Protein Intelligence (`/proteins`)
- **UniProtKB Accession & Keyword Search**: Query UniProtKB with organism filtering (*Homo sapiens*).
- **Functional Annotation**: Access recommended protein names, gene associations, biological functions, subcellular localizations, and external database cross-references.
- **Physicochemical Properties**: Real-time computational analysis via Biopython `ProtParam`:
  - Molecular weight ($Da$)
  - Theoretical Isoelectric Point ($pI$)
  - Instability Index (in vivo stability classification)
  - Grand Average of Hydropathicity (GRAVY)
  - Aromaticity score
- **Dual Structural Perspective**:
  - **Experimental Structures**: RCSB PDB cross-references with experimental determination methods (X-ray, NMR, Cryo-EM) and resolutions.
  - **Computational Predictions**: AlphaFold DB accessions with prediction confidence scores.

### E. Sequence Laboratory (`/sequences`)
- **Multi-Type Sequence Validation**: Validates DNA, RNA, and amino acid sequences with full support for IUPAC ambiguity characters.
- **Physicochemical Metrics**: Calculates length, nucleotide composition, GC content, AT content, and CpG dinucleotide counts.
- **Biological Transformations**: Reverse complement, transcription (DNA $\rightarrow$ RNA), and back-transcription (RNA $\rightarrow$ DNA).
- **Multi-Frame Translation**: Translates sequences across reading frames (+1, +2, +3, -1, -2, -3, or all six simultaneously) with configurable standard and vertebrate mitochondrial genetic codes.
- **Pairwise Alignment**:
  - Global alignment (Needleman-Wunsch algorithm)
  - Local alignment (Smith-Waterman algorithm)
  - Customizable match score, mismatch penalty, and open/extend gap costs.
- **NCBI BLAST Integration**: Asynchronous submission to NCBI QBlast server (`blastn`, `blastp`) with structured hit extraction.
- **FASTA File Ingestion**: Upload multi-record FASTA files (up to 25 MiB) with automatic header and sequence parsing.

### F. Disease Intelligence (`/diseases`)
- **Open Targets Platform**: Query disease targets, therapeutic areas, and clinical phenotype associations.
- **Europe PMC Literature**: Search peer-reviewed biomedical literature and PubMed identifiers directly associated with the disease.
- **PostgreSQL Caching**: Search results and entity details cached in `disease_cache` table.

### G. Drug & Compound Intelligence (`/compounds`)
- **PubChem PUG REST API**: Query chemical compounds by name, CID, or SMILES.
- **Physicochemical Properties**: Molecular weight, canonical SMILES, InChIKey, XLogP, TPSA, H-bond donors/acceptors, rotatable bonds.
- **Lipinski's Rule of 5**: Evaluates small-molecule oral druglikeness (MW $\le 500$, LogP $\le 5.0$, H-donors $\le 5$, H-acceptors $\le 10$).
- **ChEMBL Cross-References**: Pharmacological mechanisms of action, clinical indications, and biological targets.
- **3D Conformer Download**: Export standard 3D SDF coordinate files and 2D chemical structure diagrams.

### H. Macromolecular Structure Explorer (`/structures`)
- **Experimental Structures (RCSB PDB)**: Resolution, experimental determination method (X-ray, cryo-EM, NMR), polymer chains, and bound ligands.
- **Computational Predictions (AlphaFold DB)**: Whole-organism deep-learning structure predictions with per-residue pLDDT confidence categories.
- **3D WebGL Visualization**: Embedded 3Dmol.js viewer supporting cartoon, stick, sphere, and solvent-accessible surface representations with spectrum and chain coloring.
- **Atomic Coordinate Export**: Download raw `.pdb` files for molecular modeling.

### I. Binding Interaction Analysis (`/interactions`)
- **Hetero-Residue Ligand Extraction**: Automatically isolates non-water bound co-factors, drugs, and prosthetic groups (e.g. HEM, STI, ATP).
- **3D Atomic Distance Matrix**: Biopython Euclidean distance calculations between ligand and macromolecular binding residues within a configurable radius ($2.5 - 7.0\,\text{\AA}$).
- **Contact Classification**: Identifies hydrogen bonds, hydrophobic interactions, salt bridges, and van der Waals contacts.
- **Binding Pocket Geometry**: Pocket centroid coordinates ($X, Y, Z$), radius, and estimated cavity volume ($\text{\AA}^3$).

### J. Multi-User Authentication & Research Workspaces (`/login`, `/register`, `/projects`)
- **Identity Management**: User registration and login with Argon2 password hashing (`argon2-cffi` + `pwdlib`).
- **Stateless JWT Authorization**: Signed tokens (HS256) propagated via `Authorization: Bearer` headers.
- **Research Project Workspaces**: Organize findings, bookmark entities (genes, proteins, compounds, structures), and record activity streams with strict per-user data isolation.

### K. Publication-Grade Research Reports (`/reports` & `/docking`)
- **PDF Generation via ReportLab**: Clean, publication-grade research reports with executive summaries, structured tables, and references.
- **Microsoft Word DOCX via python-docx**: Editable Word documents for collaboration and grant applications.
- **Project Dossier Export**: One-click complete project dataset exports.

---

## 4. System Architecture

```mermaid
flowchart TD
    User["Researcher / Client Browser\nhttp://localhost:3000"]
    
    subgraph Frontend["Next.js 16 Web Application (Port 3000)"]
        UI_Dashboard["Dashboard (/)"]
        UI_Hub["Database Hub (/databases)"]
        UI_Docking["Molecular Docking (/docking)"]
        UI_Genes["Gene Intelligence (/genes)"]
        UI_Proteins["Protein Intelligence (/proteins)"]
        UI_Sequences["Sequence Lab (/sequences)"]
        UI_Compounds["Compound Explorer (/compounds)"]
        UI_Structures["3D Structures (/structures)"]
        UI_Viewer["3Dmol.js WebGL Viewer\n(Ribbons, Sticks, Pockets, Contacts)"]
        ApiClient["Typed API Client\n(frontend/src/lib/api.ts)"]

        UI_Dashboard --> ApiClient
        UI_Hub --> ApiClient
        UI_Docking --> ApiClient
        UI_Docking --> UI_Viewer
        UI_Genes --> ApiClient
        UI_Proteins --> ApiClient
        UI_Sequences --> ApiClient
        UI_Compounds --> ApiClient
        UI_Structures --> ApiClient
        UI_Structures --> UI_Viewer
    end

    subgraph Backend["FastAPI REST Application (Port 8000)"]
        RouterAuth["Auth & Users (/api/v1/auth)"]
        RouterHub["Database Hub (/api/v1/databases)"]
        RouterDocking["Molecular Docking (/api/v1/docking)"]
        RouterGenes["Gene Intelligence (/api/v1/genes)"]
        RouterProteins["Protein Intelligence (/api/v1/proteins)"]
        RouterSequences["Sequence Lab (/api/v1/sequences)"]
        RouterReports["Reports Generator (/api/v1/reports)"]
        
        subgraph BackgroundWorkers["Background Job & Execution Layer"]
            JobPool["ThreadPoolExecutor (Workers=3)"]
            Reconciler["Startup Job Reconciler\n(Lifespan Manager)"]
        end

        subgraph ScientificEngines["Scientific & Computational Core"]
            VinaExe["Scripps AutoDock Vina v1.2.5\n(Native C++ Binary)"]
            RDKitMeeko["RDKit ETKDGv3 + Meeko\n(3D Conformer & PDBQT Generator)"]
            ContactClassifier["Interatomic Contact Classifier\n(H-bonds, Salt bridges, Hydrophobic)"]
            BiopythonEngine["Biopython 1.88 Engine\n(ProtParam, PDB parser, Aligners)"]
            ReportLabEngine["ReportLab & python-docx Engine"]
        end

        subgraph ConnectorHub["11-Database Connector Registry"]
            ConnRCSB["RCSB PDB"]
            ConnUniProt["UniProtKB"]
            ConnPubChem["PubChem"]
            ConnNCBI["NCBI Entrez"]
            ConnPDBe["PDBe"]
            ConnAF["AlphaFold DB"]
            ConnChEMBL["ChEMBL"]
            ConnEPMC["Europe PMC"]
            ConnOT["Open Targets"]
            ConnEnsembl["Ensembl"]
            ConnReactome["Reactome"]
        end
    end

    subgraph DatabaseLayer["Relational Database (PostgreSQL 18)"]
        PG_DB[("PostgreSQL 18\n• docking_jobs & docking_poses\n• gene_cache & protein_cache\n• disease_cache & compound_cache\n• blast_jobs\n• users & projects")]
    end

    User <-->|HTTP / WebGL| Frontend
    ApiClient <-->|REST JSON / JWT| Backend
    RouterDocking --> JobPool
    JobPool --> RDKitMeeko
    JobPool --> VinaExe
    JobPool --> ContactClassifier
    RouterDocking --> ReportLabEngine
    RouterSequences --> BiopythonEngine
    RouterHub --> ConnectorHub
    ConnectorHub <-->|HTTPS Async Pools| ConnRCSB & ConnUniProt & ConnPubChem & ConnNCBI & ConnAF & ConnChEMBL & ConnEPMC & ConnOT & ConnEnsembl & ConnReactome & ConnPDBe
    Backend <-->|SQLAlchemy 2.x + psycopg3| DatabaseLayer
    Reconciler -->|Crash / Interruption Recovery| DatabaseLayer
```

---

## 5. Technology Stack

### Backend Engine
- **Language**: Python 3.12 (Strict typing)
- **Web Framework**: FastAPI 0.162.0 (ASGI)
- **Docking Engine**: Scripps AutoDock Vina v1.2.5 (Native binary execution)
- **Cheminformatics**: RDKit 2026.9.1, Meeko 0.8.0, Gemmi 0.7.5
- **Bioinformatics**: Biopython 1.88, NumPy 2.5.4, SciPy 1.18.1
- **Database ORM**: SQLAlchemy 2.1.6 with PostgreSQL 3 adapter (`psycopg 3.3.7`)
- **Database Migrations**: Alembic 1.20.1
- **Security & Cryptography**: Argon2 (`pwdlib`, `argon2-cffi`), PyJWT
- **Reporting**: ReportLab 5.1.0 (PDF), python-docx 1.2.0 (Word DOCX)
- **HTTP Client**: HTTPX 0.28.1 (Asynchronous connection pooling)
- **Server**: Uvicorn 0.54.0

### Frontend Web Client
- **Framework**: Next.js 16.4.4 (App Router, Turbopack)
- **UI Runtime**: React 19.3.0
- **Language**: TypeScript 5.x (Strict mode)
- **Styling**: Tailwind CSS 4, Lucide React icons
- **3D Molecular Graphics**: 3Dmol.js 2.4.2 (WebGL hardware-accelerated rendering)
- **Components**: Radix UI / Base UI design patterns

### Database & Persistence
- **Relational Store**: PostgreSQL 18.6 (Port 5432)
- **Persistent Tables**: `docking_jobs`, `docking_poses`, `gene_cache`, `protein_cache`, `compound_cache`, `disease_cache`, `blast_jobs`, `users`, `projects`

---

## 6. Prerequisites & System Requirements

- **Operating System**: Windows 11 (64-bit), Ubuntu 22.04/24.04 LTS, or macOS 14+
- **Python**: Python 3.12.x (with `pip` and virtual environment support)
- **Node.js**: Node.js 20.9.x LTS or higher (with `npm`)
- **PostgreSQL**: PostgreSQL 16.x or 18.x running locally or remotely on port 5432
- **Git**: Git 2.40+

---

## 7. Step-by-Step Installation & Setup

Follow these exact steps to clone, configure, and execute BioInsight AI 2.0 locally:

### Step 1: Clone the Repository
```bash
git clone https://github.com/niranjan867/bioinsight-ai.git
cd bioinsight-ai
```

### Step 2: Configure Environment Variables
Copy the template configuration files:
```bash
# Backend configuration
cp backend/.env.example backend/.env

# Frontend configuration
cp frontend/.env.example frontend/.env.local
```

Edit `backend/.env` to configure your PostgreSQL credentials:
```ini
APP_NAME=BioInsight AI
APP_ENV=development
DEBUG=true

# Database connection URL (PostgreSQL with psycopg3 driver)
DATABASE_URL=postgresql+psycopg://bioinsight_app:your_password@127.0.0.1:5432/bioinsight_db

# Security
JWT_SECRET_KEY=replace_with_a_secure_random_key_min_32_chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# File Storage
STORAGE_PATH=../storage
MAX_UPLOAD_SIZE_MB=25

# CORS Allowed Origin
FRONTEND_URL=http://localhost:3000

# NCBI Contact (Required for NCBI BLAST queries)
NCBI_EMAIL=your-email@example.org
NCBI_TOOL=BioInsightAI
```

### Step 3: Set Up PostgreSQL Database
Open `psql` as administrator:
```sql
CREATE USER bioinsight_app WITH PASSWORD 'your_password';
CREATE DATABASE bioinsight_db OWNER bioinsight_app;
GRANT ALL PRIVILEGES ON DATABASE bioinsight_db TO bioinsight_app;
\connect bioinsight_db
GRANT ALL ON SCHEMA public TO bioinsight_app;
\q
```

### Step 4: Set Up Backend Python Environment
```bash
cd backend

# Create Python 3.12 virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# Install required backend dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Apply Alembic database migrations
alembic upgrade head

cd ..
```

### Step 5: Set Up Frontend Node Environment
```bash
cd frontend

# Install Node.js dependencies
npm install

cd ..
```

### Step 6: Start the Application

**Option A — Automated Launch (Windows PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_all.ps1
```

**Option B — Independent Manual Terminals:**

*Terminal 1 (Backend):*
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

*Terminal 2 (Frontend):*
```powershell
cd frontend
npm run dev
```

Open your browser at **`http://localhost:3000`**.
Interactive OpenAPI documentation is available at **`http://127.0.0.1:8000/docs`**.

---

## 8. AutoDock Vina Configuration & Docking Walkthrough

### Vina Binary Setup
BioInsight AI bundles the official Scripps AutoDock Vina v1.2.5 Windows binary at `backend/bin/vina.exe`.

- **Windows**: Ready out of the box (bundled binary).
- **Linux**: Download the Scripps binary and mark executable:
  ```bash
  curl -L -o backend/bin/vina https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_linux_x86_64
  chmod +x backend/bin/vina
  ```
- **macOS**: Install via Homebrew:
  ```bash
  brew install vina
  ```

### End-to-End Docking Example (Reference Complex 1HSG)

You can run an end-to-end molecular docking experiment in the `/docking` module:

1. **Step 1: Select Target Protein**
   - Source: `RCSB PDB`
   - Identifier: `1HSG` (HIV-1 Protease with bound inhibitor Amprenavir)
   - Click **Prepare Receptor**. BioInsight AI strips crystallographic waters, checks peptide chains A & B (198 residues), and formats polar hydrogens.
2. **Step 2: Define Small-Molecule Ligand**
   - Source: `SMILES`
   - SMILES Input: `CC(C)CN(CC(O)C(Cc1ccccc1)NC(=O)OC1CCOC1)S(=O)(=O)c1ccc(N)cc1` (Amprenavir)
   - Click **Prepare Ligand**. RDKit generates a 3D conformer with UFF minimization and Meeko exports 13 active rotatable torsions.
3. **Step 3: Define Binding Pocket**
   - Mode: `Bound Ligand` (Selects co-crystallized ligand `MK1`)
   - Centroid calculated: $X=11.63, Y=22.47, Z=5.86\,\text{\AA}$
   - Dimensions: $24.9 \times 20.2 \times 18.6\,\text{\AA}$
4. **Step 4: Launch AutoDock Vina**
   - Exhaustiveness: `8` | Number of Modes: `5`
   - Click **Launch Molecular Docking**.
   - AutoDock Vina computes poses (~30–35s).
5. **Step 5: Inspect Results & 3D Visualization**
   - Mode 1: **$-8.21\,\text{kcal/mol}$** binding affinity.
   - 3D Viewer renders cartoon receptor, stick pose, wireframe pocket, and dashed interatomic contact lines (H-bonds to `GLY27:B` at $3.46\,\text{\AA}$, flap contacts to `ILE50:B` at $3.54\,\text{\AA}$).
   - Click **Export Report (PDF)** or **Export Report (DOCX)** for publication-grade dossiers.

---

## 9. Environment Variable Configuration

Decoupled environment templates prevent secret leaks:

### Backend Variables (`backend/.env`)

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `APP_NAME` | No | `BioInsight AI` | Display name of the application |
| `APP_ENV` | No | `development` | Environment mode (`development`, `production`) |
| `DEBUG` | No | `true` | Enables FastAPI debug logs and diagnostics |
| `DATABASE_URL` | **Yes** | — | PostgreSQL connection string (`postgresql+psycopg://...`) |
| `JWT_SECRET_KEY` | **Yes** | — | Secret key used for signing JWT tokens |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| No | `30` | JWT token lifespan in minutes |
| `FRONTEND_URL` | No | `http://localhost:3000` | Allowed CORS origins (comma-separated for multiple) |
| `STORAGE_PATH` | No | `../storage` | Path for temporary files and report generation |
| `NCBI_EMAIL` | Optional | `your-email@example.org`| Contact email for NCBI QBlast queries |
| `NCBI_TOOL` | Optional | `BioInsightAI` | Tool identifier for NCBI QBlast |

### Frontend Variables (`frontend/.env.local`)

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `NEXT_PUBLIC_API_URL` | **Yes** | `http://127.0.0.1:8000` | Primary URL of the FastAPI backend |
| `NEXT_PUBLIC_API_BASE_URL`| No | `http://127.0.0.1:8000` | Compatibility fallback for backend URL |
| `NEXT_PUBLIC_APP_URL` | No | `http://localhost:3000` | Public client web address |

---

## 10. Running Automated Tests

BioInsight AI 2.0 maintains a comprehensive automated testing suite:

```bash
# 1. Python Syntax & Bytecode Compilation
cd backend
python -m compileall app tests migrations

# 2. Python Code Quality & Linting
ruff check app tests migrations

# 3. Database Migration Integrity
alembic check

# 4. Run Pytest Suite (94 Unit & Integration Tests)
pytest -v

# 5. Frontend TypeScript Verification
cd ../frontend
npx tsc --noEmit

# 6. Frontend Code Linting
npm run lint

# 7. Frontend Production Build (Turbopack)
npm run build
```

---

## 11. Supported Production Deployment Architecture

> [!NOTE]
> **No Docker & No Vercel Required**: BioInsight AI 2.0 is designed to run natively on dedicated physical servers or Linux/Windows virtual machines without container overhead or serverless timeout limitations.

### Recommended Production Deployment Model

```
┌────────────────────────────────────────────────────────────────────────┐
│                        INTERNET / CLIENTS                              │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ HTTPS (:443)
┌──────────────────────────────────▼─────────────────────────────────────┐
│                       NGINX REVERSE PROXY                              │
│  • Terminates SSL / TLS                                                │
│  • Routes /api/*, /docs, /health ─────────► FastAPI (:8000)            │
│  • Routes /* (HTML, CSS, JS)   ─────────► Next.js Standalone (:3000)   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         │                                                   │
┌────────▼────────────────────────┐ ┌────────────────────────▼───────────┐
│     FASTAPI BACKEND SERVICE     │ │        NEXT.JS FRONTEND SERVICE    │
│  • Systemd service (Linux) or   │ │  • Managed via PM2 or Systemd      │
│    Windows Service              │ │  • Node.js 20 LTS runtime          │
│  • Uvicorn ASGI with 4 workers  │ │  • Port 3000                       │
│  • Native AutoDock Vina binary  │ └────────────────────────────────────┘
│  • Local ThreadPoolExecutor     │
└────────┬────────────────────────┘
         │
┌────────▼────────────────────────┐
│      POSTGRESQL 18 DATABASE     │
│  • Local or dedicated cluster   │
│  • Port 5432                    │
│  • Connection pool: psycopg3    │
└─────────────────────────────────┘
```

1. **Frontend Hosting**: Next.js production build (`npm run build && npm run start` or `node .next/standalone/server.js`) managed by **PM2** or **systemd** on Node.js 20 LTS.
2. **Backend Hosting**: FastAPI running under **Uvicorn** with multi-worker concurrency (`uvicorn app.main:app --workers 4 --host 127.0.0.1 --port 8000`) managed by **systemd** or Windows Services.
3. **Database Hosting**: PostgreSQL 16 or 18 instance with persistent storage, automated backups, and indexed caching tables.
4. **Docking Background Workers**: Handled natively within the FastAPI backend via Python `ThreadPoolExecutor` and isolated temporary disk directories (`tempfile.TemporaryDirectory`). Interrupted jobs are automatically recovered on service restart.
5. **Reverse Proxy & TLS**: **Nginx** handles SSL termination, static file compression, and reverse proxies requests to Next.js (`:3000`) and FastAPI (`:8000`).

---

## 12. Scientific Reproducibility & Responsibility

To guarantee scientific rigor, BioInsight AI 2.0 maintains transparent separation between empirical data and computational predictions:

1. **Direct Authoritative Data**: Retrieved live from official REST APIs (UniProt sequences, RCSB crystal structures, NCBI genomic loci, PubChem SMILES).
2. **Deterministic Computations**: Calculated locally using standard peer-reviewed formulas (Biopython ProtParam MW/pI/GRAVY, Needleman-Wunsch sequence alignments, Lipinski Rule of 5).
3. **Computational Predictions**: In silico estimates subject to force-field and modeling approximations (AlphaFold pLDDT scores, AutoDock Vina $\Delta G$ binding energies).

### In Silico Docking Disclaimer

> [!IMPORTANT]
> AutoDock Vina binding scores ($\text{kcal/mol}$) are **computational estimates** of protein–ligand interaction potentials. They do **not** replace in vitro or in vivo experimental binding assays (e.g., ITC, SPR, IC50 measurements) and do **not** constitute proof of pharmacological efficacy or clinical safety.

---

## 13. Scientific Attribution & Third-Party Licenses

BioInsight AI 2.0 complies fully with open-science attribution guidelines and open-source licenses:

- **Scientific Data Sources**: For exhaustive citations, API documentation, rate limits, and database terms of use for all 11 biological sources, refer to [`docs/DATA_SOURCES_AND_ATTRIBUTION.md`](docs/DATA_SOURCES_AND_ATTRIBUTION.md).
- **Third-Party Software & Licenses**: For the complete audit of external software packages, versions, licenses (SPDX), and the AutoDock Vina Apache 2.0 notice, refer to [`docs/THIRD_PARTY_LICENSES.md`](docs/THIRD_PARTY_LICENSES.md).

---

## 14. Documentation Links

- [Scientific Data Sources & Attribution Guide](docs/DATA_SOURCES_AND_ATTRIBUTION.md)
- [Third-Party Software & Licenses (SBOM)](docs/THIRD_PARTY_LICENSES.md)
- [Testing & Quality Gates Manual](docs/TESTING.md)
- [System Architecture Specification](docs/ARCHITECTURE.md)
- [API Reference Manual](docs/API_REFERENCE.md)
- [Production Deployment Audit Report](docs/PRODUCTION_DEPLOYMENT_AUDIT.md)
- [Security & Privacy Guide](docs/SECURITY.md)
- [Developer Setup Guide](docs/FRIEND_SETUP_GUIDE.md)

---

## License

This project is open-source software licensed under the **[MIT License](LICENSE)**.
Scripps AutoDock Vina is licensed under the **Apache License 2.0**.
