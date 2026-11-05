# Scientific data sources and methods

| Source or method | Current use | Provenance and limits |
|---|---|---|
| MyGene.info | Gene search and annotations | Gene responses include source, retrieval time, and cache state. Upstream availability and source coverage can vary. |
| NCBI Entrez | Gene/client integration and NCBI references | NCBI requests may require a stable contact address and should respect service policy. |
| UniProt REST | Protein search, sequence, annotation, features, evidence, cross references | UniProt record is the source of the protein sequence and annotation; cache state is returned. |
| AlphaFold DB | Predicted structure metadata/confidence | Predictions are explicitly labeled computational, not experimental. |
| RCSB PDB | Experimental structure IDs/metadata through UniProt cross references | The current app does not yet retrieve/visualize full PDB structures directly. |
| Biopython | FASTA parsing, DNA/RNA transforms, translation, pairwise alignment, protein sequence properties, BLAST XML parsing | Results are computational outputs. Sequence parameters and method are returned or documented. |
| NCBI BLAST | Remote asynchronous similarity search | BLAST requires `NCBI_EMAIL`, network access, and time for a queued job. Job tracking is in-process and temporary. |

Open Targets, Europe PMC, PubChem, and ChEMBL are planned integrations and are not currently used by functional disease/compound modules.

## Evidence categories

- **Database annotation:** information returned by MyGene.info or UniProt.
- **Experimental structure:** structure references categorized by PDB/UniProt as experimental.
- **Computational prediction:** AlphaFold predicted structure metadata.
- **Computed result:** sequence statistics, translation, alignment, and BLAST output.
- **User-provided data:** sequences entered or uploaded by the user.

Do not treat a computational prediction as experimental evidence or an AI interpretation as a database annotation.
