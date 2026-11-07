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

## Disease Intelligence

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/diseases/search?q=asthma` | Search diseases and phenotypes across Open Targets Platform |
| GET | `/api/v1/diseases/{disease_id}` | Retrieve disease details, therapeutic areas, and associated genetic targets |
| GET | `/api/v1/diseases/{disease_id}/publications?name=asthma` | Search Europe PMC peer-reviewed literature |

## Drug & Compound Intelligence

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/compounds/search?q=aspirin` | Search PubChem compound database by name or SMILES |
| GET | `/api/v1/compounds/{cid}` | Retrieve molecular properties, Lipinski Rule of 5 evaluation, and ChEMBL targets |
| GET | `/api/v1/compounds/{cid}/targets` | Retrieve pharmacological mechanisms and biological targets from ChEMBL |
| GET | `/api/v1/compounds/{cid}/sdf` | Download 3D conformer coordinates in SDF format |

## Macromolecular Structure Explorer

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/structures/{pdb_id}` | Fetch experimental PDB metadata, resolution, and bound ligands |
| GET | `/api/v1/structures/{pdb_id}/pdb` | Download atomic coordinates in standard PDB format |
| GET | `/api/v1/structures/alphafold/{accession}` | Fetch AlphaFold DB predicted structure metadata and pLDDT scores |

## Protein-Ligand Interaction & Docking Laboratory

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/docking/ligands/{pdb_id}` | Extract all bound hetero-residue ligands from a PDB structure |
| POST | `/api/v1/docking/analyze` | Calculate 3D atomic contact matrix, binding pocket geometry, and empirical affinity ($\Delta G$) |

## Research Project Management

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/projects` | List research projects for the signed-in user |
| POST | `/api/v1/projects` | Create a new research project workspace |
| GET | `/api/v1/projects/{project_id}` | Get project details, saved items, and audit activities |
| PATCH | `/api/v1/projects/{project_id}` | Update project metadata, status, or tags |
| DELETE | `/api/v1/projects/{project_id}` | Delete project workspace and associated items |
| POST | `/api/v1/projects/{project_id}/items` | Save a gene, protein, compound, disease, structure, or note to the project |
| DELETE | `/api/v1/projects/{project_id}/items/{item_id}` | Remove saved item from the project |

## Authentication & Authorization

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Register new user with Argon2 password hashing; returns JWT Bearer token |
| POST | `/api/v1/auth/login` | Authenticate with email/password; returns JWT access token |
| GET | `/api/v1/auth/me` | Retrieve signed-in researcher profile |
| PATCH | `/api/v1/auth/me` | Update name or institution |

## AI Research Assistant

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/assistant/chat` | Query grounded research assistant; returns synthesized answer with verifiable citations |
| GET | `/api/v1/assistant/suggestions` | Retrieve curated scientific query prompts |

## Research Report Generator

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/reports/pdf` | Generate publication-grade PDF report via ReportLab |
| POST | `/api/v1/reports/docx` | Generate editable Microsoft Word DOCX document |
| GET | `/api/v1/reports/project/{project_id}/pdf` | Export complete project dataset and audit trail to PDF |
| GET | `/api/v1/reports/project/{project_id}/docx` | Export complete project dataset to DOCX |
