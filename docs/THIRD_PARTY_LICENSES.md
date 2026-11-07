# Third-Party Software & Open-Source Licenses

This document provides a complete audit of all third-party open-source software, computational libraries, runtimes, bundled binaries, and developer tooling utilized by **BioInsight AI 2.0**.

BioInsight AI 2.0 is released under the **MIT License**. It integrates independent open-source packages governed by their respective licenses. BioInsight AI makes no claim of ownership over any third-party software or libraries described herein.

---

## 1. Bundled Computational Binaries

### Scripps AutoDock Vina v1.2.5

- **Binary Location**: `backend/bin/vina.exe` (Windows x64 executable)
- **Version**: 1.2.5
- **License**: **Apache License 2.0**
- **Copyright**: Copyright (c) 2006–2021 The Scripps Research Institute
- **Official Repository**: [https://github.com/ccsb-scripps/AutoDock-Vina](https://github.com/ccsb-scripps/AutoDock-Vina)
- **Official Release**: [https://github.com/ccsb-scripps/AutoDock-Vina/releases/tag/v1.2.5](https://github.com/ccsb-scripps/AutoDock-Vina/releases/tag/v1.2.5)
- **Licensing Terms & Redistribution Obligations**:
  - AutoDock Vina version 1.2.x is licensed under the Apache License, Version 2.0.
  - Users and redistributors are granted a perpetual, worldwide, non-exclusive, no-charge, royalty-free copyright and patent license to reproduce, prepare derivative works of, publicly display, publicly perform, sublicense, and distribute the work.
  - A copy of the Apache 2.0 License and applicable NOTICE statements must accompany binary distributions.
  - Primary Scientific Citations:
    - *Eberhardt J, Santos-Martins D, Tillack AF, Forli S. AutoDock Vina 1.2.0: New Docking Methods, Expanded Force Field, and Python Bindings. J Chem Inf Model. 2021 Aug 23;61(8):3891-3898. doi: 10.1021/acs.jcim.1c00203.*
    - *Trott O, Olson AJ. AutoDock Vina: improving the speed and accuracy of docking with a new scoring function, efficient optimization, and multithreading. J Comput Chem. 2010 Jan 30;31(2):455-61. doi: 10.1002/jcc.21334.*

---

## 2. Core Scientific & Cheminformatics Libraries (Python)

| Library | Installed Version | SPDX License | Official Repository | Purpose / Role |
|---|:---:|:---:|---|---|
| **RDKit** | 2026.9.1 | `BSD-3-Clause` | [github.com/rdkit/rdkit](https://github.com/rdkit/rdkit) | Small-molecule cheminformatics, 3D conformer generation (ETKDGv3), force-field energy minimization (UFF), SMILES validation |
| **Meeko** | 0.8.0 | `LGPL-2.1-or-later` / `Apache-2.0` | [github.com/forlilab/Meeko](https://github.com/forlilab/Meeko) | Ligand PDBQT preparation, Gasteiger charges, and flexible torsion tree generation for AutoDock Vina |
| **Biopython** | 1.88 | `Biopython License` (BSD-style) | [github.com/biopython/biopython](https://github.com/biopython/biopython) | Macromolecular PDB parsing, atomic coordinates, sequence validation, translation across 6 frames, Needleman-Wunsch & Smith-Waterman alignment, `ProtParam` physicochemical analysis |
| **Gemmi** | 0.7.5 | `MPL-2.0` | [github.com/project-gemmi/gemmi](https://github.com/project-gemmi/gemmi) | Macromolecular crystallographic coordinate processing and structural validation |
| **NumPy** | 2.5.4 | `BSD-3-Clause` | [github.com/numpy/numpy](https://github.com/numpy/numpy) | High-performance N-dimensional arrays, vector math, and coordinate matrix transformations |
| **SciPy** | 1.18.1 | `BSD-3-Clause` | [github.com/scipy/scipy](https://github.com/scipy/scipy) | Spatial distance matrix calculations, Euclidean kd-tree searches, and binding contact geometry |

---

## 3. Backend Web Framework & Infrastructure (Python)

| Library | Installed Version | SPDX License | Official Repository | Purpose / Role |
|---|:---:|:---:|---|---|
| **FastAPI** | 0.162.0 | `MIT` | [github.com/fastapi/fastapi](https://github.com/fastapi/fastapi) | Asynchronous ASGI REST API framework |
| **Pydantic** | 2.14.2 | `MIT` | [github.com/pydantic/pydantic](https://github.com/pydantic/pydantic) | Data modeling, input validation, and schema definitions |
| **SQLAlchemy** | 2.1.6 | `MIT` | [github.com/sqlalchemy/sqlalchemy](https://github.com/sqlalchemy/sqlalchemy) | Relational database ORM and connection pooling |
| **psycopg** | 3.3.7 | `LGPL-3.0-or-later` | [github.com/psycopg/psycopg](https://github.com/psycopg/psycopg) | Next-generation PostgreSQL 3 database adapter |
| **Alembic** | 1.20.1 | `MIT` | [github.com/sqlalchemy/alembic](https://github.com/sqlalchemy/alembic) | PostgreSQL schema migration management |
| **ReportLab** | 5.1.0 | `BSD-3-Clause` | [hg.reportlab.com/hg-public/reportlab](https://hg.reportlab.com/hg-public/reportlab) | Programmatic PDF report generation engine |
| **python-docx** | 1.2.0 | `MIT` | [github.com/python-openxml/python-docx](https://github.com/python-openxml/python-docx) | Microsoft Word DOCX report creation |
| **HTTPX** | 0.28.1 | `BSD-3-Clause` | [github.com/encode/httpx](https://github.com/encode/httpx) | Asynchronous HTTP client for federated database queries |
| **Uvicorn** | 0.54.0 | `BSD-3-Clause` | [github.com/encode/uvicorn](https://github.com/encode/uvicorn) | High-performance ASGI web server |
| **Argon2-cffi** | 25.1.0 | `MIT` | [github.com/hynek/argon2-cffi](https://github.com/hynek/argon2-cffi) | Secure password hashing algorithm |
| **pwdlib** | 0.3.1 | `MIT` | [github.com/frankie567/pwdlib](https://github.com/frankie567/pwdlib) | Modern password hashing helper for Python |
| **PyJWT** | 2.15.1 | `MIT` | [github.com/jpadilla/pyjwt](https://github.com/jpadilla/pyjwt) | JSON Web Token (JWT) signing and validation |
| **python-multipart**| 0.0.33 | `Apache-2.0` | [github.com/Kludex/python-multipart](https://github.com/Kludex/python-multipart) | Multipart/form-data parser for FASTA uploads |
| **pytest** | 9.2.0 | `MIT` | [github.com/pytest-dev/pytest](https://github.com/pytest-dev/pytest) | Test execution framework |
| **Ruff** | 0.17.3 | `MIT` / `Apache-2.0` | [github.com/astral-sh/ruff](https://github.com/astral-sh/ruff) | High-speed Python linter and code formatter |

---

## 4. Frontend Web Framework & 3D Visualization (Node.js / React)

| Library / Asset | Version | SPDX License | Source / Repository | Purpose / Role |
|---|:---:|:---:|---|---|
| **3Dmol.js** | 2.4.2 | `BSD-3-Clause` | [github.com/3dmol/3Dmol.js](https://github.com/3dmol/3Dmol.js) | Hardware-accelerated WebGL molecular viewer for 3D proteins, ligands, binding boxes, and interatomic vectors |
| **Next.js** | 16.4.4 | `MIT` | [github.com/vercel/next.js](https://github.com/vercel/next.js) | React framework with App Router and Turbopack compiler |
| **React** | 19.3.0 | `MIT` | [github.com/facebook/react](https://github.com/facebook/react) | Core UI component rendering library |
| **React DOM** | 19.3.0 | `MIT` | [github.com/facebook/react](https://github.com/facebook/react) | DOM rendering engine for React |
| **Tailwind CSS** | 4.x | `MIT` | [github.com/tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss) | Utility-first CSS framework |
| **Lucide React** | 1.67.0 | `ISC` | [github.com/lucide-icons/lucide](https://github.com/lucide-icons/lucide) | Modern iconography for life-science workflows |
| **Base UI / Radix** | 1.9.0 | `MIT` | [github.com/mui/base-ui](https://github.com/mui/base-ui) | Accessible, unstyled UI primitives |
| **Recharts** | 3.10.1 | `MIT` | [github.com/recharts/recharts](https://github.com/recharts/recharts) | Composable charting library for scientific metrics |
| **Zod** | 4.6.7 | `MIT` | [github.com/colinhacks/zod](https://github.com/colinhacks/zod) | TypeScript-first schema validation |
| **TypeScript** | 5.x | `Apache-2.0` | [github.com/microsoft/TypeScript](https://github.com/microsoft/TypeScript) | Strongly typed JavaScript superset |

---

## 5. Software Bill of Materials (SBOM) Summary

```json
{
  "bomFormat": "CycloneDX-Compatible",
  "specVersion": "1.5",
  "component": {
    "name": "bioinsight-ai",
    "version": "2.0.0",
    "type": "application",
    "licenses": [{"license": {"id": "MIT"}}]
  },
  "dependencies": [
    {"name": "autodock-vina", "version": "1.2.5", "license": "Apache-2.0"},
    {"name": "rdkit", "version": "2026.9.1", "license": "BSD-3-Clause"},
    {"name": "meeko", "version": "0.8.0", "license": "LGPL-2.1-or-later"},
    {"name": "gemmi", "version": "0.7.5", "license": "MPL-2.0"},
    {"name": "biopython", "version": "1.88", "license": "Biopython-License"},
    {"name": "scipy", "version": "1.18.1", "license": "BSD-3-Clause"},
    {"name": "numpy", "version": "2.5.4", "license": "BSD-3-Clause"},
    {"name": "fastapi", "version": "0.162.0", "license": "MIT"},
    {"name": "pydantic", "version": "2.14.2", "license": "MIT"},
    {"name": "sqlalchemy", "version": "2.1.6", "license": "MIT"},
    {"name": "psycopg", "version": "3.3.7", "license": "LGPL-3.0-or-later"},
    {"name": "reportlab", "version": "5.1.0", "license": "BSD-3-Clause"},
    {"name": "python-docx", "version": "1.2.0", "license": "MIT"},
    {"name": "httpx", "version": "0.28.1", "license": "BSD-3-Clause"},
    {"name": "next", "version": "16.4.4", "license": "MIT"},
    {"name": "react", "version": "19.3.0", "license": "MIT"},
    {"name": "3dmol", "version": "2.4.2", "license": "BSD-3-Clause"},
    {"name": "lucide-react", "version": "1.67.0", "license": "ISC"}
  ]
}
```

---

## 6. License Compliance & Redistribution Verification

- **Permissive Licenses**: The overwhelming majority of dependencies (MIT, BSD-3-Clause, Apache-2.0, ISC) are highly permissive and grant full rights for non-commercial and commercial compilation, modification, and redistribution.
- **Copyleft & Weak Copyleft Review**:
  - `psycopg` (LGPL-3.0) and `meeko` (LGPL-2.1): Used as dynamic library imports via Python package installation without modification of their core source code, fully complying with LGPL dynamic linking exceptions.
  - `gemmi` (MPL-2.0): Used as an unmodified binary wheel package; file-level copyleft requirements under MPL-2.0 are satisfied.
- **AutoDock Vina Binary Notice**:
  - AutoDock Vina v1.2.5 is distributed in accordance with the Apache License 2.0. Copyright (c) 2006–2021 The Scripps Research Institute.
