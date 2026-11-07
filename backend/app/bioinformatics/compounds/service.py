import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bioinformatics.compounds.client import CompoundClient
from app.bioinformatics.compounds.schemas import (
    Compound3DConformerResponse,
    CompoundDetailResponse,
    CompoundSearchHit,
    CompoundSearchResponse,
    CompoundTargetsResponse,
    DrugTargetRelationship,
)
from app.bioinformatics.compounds.utils import (
    evaluate_lipinski_rule_of_five,
    get_pubchem_image_url,
)
from app.models.compound_cache import CompoundCache

logger = logging.getLogger(__name__)


class CompoundService:
    """Orchestrates compound searches, chemical property analysis, ChEMBL mapping, and caching."""

    def __init__(self, client: CompoundClient | None = None) -> None:
        self.client = client or CompoundClient()

    async def search(self, query: str, max_records: int = 15) -> CompoundSearchResponse:
        """Search compounds in PubChem by name, synonym, or SMILES."""
        raw_props = await self.client.search_by_name(query.strip(), max_records=max_records)
        hits: list[CompoundSearchHit] = []

        for p in raw_props:
            cid = p.get("CID")
            if not cid:
                continue

            mw = None
            if p.get("MolecularWeight"):
                try:
                    mw = float(p["MolecularWeight"])
                except ValueError:
                    pass

            name = p.get("Title") or f"CID {cid}"
            smiles = p.get("CanonicalSMILES") or p.get("ConnectivitySMILES")

            hits.append(
                CompoundSearchHit(
                    cid=cid,
                    name=name,
                    molecular_formula=p.get("MolecularFormula"),
                    molecular_weight=mw,
                    canonical_smiles=smiles,
                    inchi_key=p.get("InChIKey"),
                    image_url=get_pubchem_image_url(cid),
                )
            )

        return CompoundSearchResponse(query=query, total=len(hits), results=hits)

    async def get_compound(
        self,
        identifier: str,
        db: Session,
        force_refresh: bool = False,
    ) -> CompoundDetailResponse | None:
        """Retrieve compound details, Lipinski evaluation, ChEMBL targets, and cache in PostgreSQL."""
        clean_id = identifier.strip()

        # Check local PostgreSQL cache first
        if not force_refresh:
            cached = db.scalar(
                select(CompoundCache).where(
                    (CompoundCache.compound_id == clean_id)
                    | (CompoundCache.name.ilike(clean_id))
                    | (CompoundCache.inchi_key == clean_id)
                )
            )
            if cached and cached.source_data:
                data = cached.source_data
                return CompoundDetailResponse(
                    cid=int(data.get("cid", 0)),
                    name=cached.name,
                    iupac_name=data.get("iupac_name"),
                    molecular_formula=cached.formula,
                    molecular_weight=float(cached.molecular_weight) if cached.molecular_weight else None,
                    canonical_smiles=cached.smiles,
                    isomeric_smiles=data.get("isomeric_smiles"),
                    inchi_key=cached.inchi_key,
                    xlogp=data.get("xlogp"),
                    tpsa=data.get("tpsa"),
                    h_bond_donor_count=data.get("h_bond_donor_count"),
                    h_bond_acceptor_count=data.get("h_bond_acceptor_count"),
                    rotatable_bond_count=data.get("rotatable_bond_count"),
                    exact_mass=data.get("exact_mass"),
                    image_url=get_pubchem_image_url(int(data.get("cid", 0))),
                    lipinski=evaluate_lipinski_rule_of_five(
                        float(cached.molecular_weight) if cached.molecular_weight else None,
                        data.get("xlogp"),
                        data.get("h_bond_donor_count"),
                        data.get("h_bond_acceptor_count"),
                    ),
                    chembl_id=data.get("chembl_id"),
                    drug_targets=[
                        DrugTargetRelationship(**t) for t in data.get("drug_targets", [])
                    ],
                    source=cached.source,
                    is_cached=True,
                    retrieved_at=cached.retrieved_at,
                )

        # Cold fetch from PubChem
        # Determine if identifier is integer CID or string name
        cid: int | None = None
        if clean_id.isdigit():
            cid = int(clean_id)
            props = await self.client.get_by_cid(cid)
        else:
            search_res = await self.client.search_by_name(clean_id, max_records=1)
            props = search_res[0] if search_res else None
            if props:
                cid = props.get("CID")

        if not props or not cid:
            return None

        # Extract properties
        mw = None
        if props.get("MolecularWeight"):
            try:
                mw = float(props["MolecularWeight"])
            except ValueError:
                pass

        xlogp = None
        if props.get("XLogP") is not None:
            try:
                xlogp = float(props["XLogP"])
            except ValueError:
                pass

        tpsa = None
        if props.get("TPSA") is not None:
            try:
                tpsa = float(props["TPSA"])
            except ValueError:
                pass

        donors = props.get("HBondDonorCount")
        acceptors = props.get("HBondAcceptorCount")
        rotatable = props.get("RotatableBondCount")
        exact_mass = None
        if props.get("ExactMass"):
            try:
                exact_mass = float(props["ExactMass"])
            except ValueError:
                pass

        name = props.get("Title")
        if not name:
            synonyms = await self.client.get_synonyms(cid)
            name = synonyms[0] if synonyms else f"Compound {cid}"

        smiles = props.get("CanonicalSMILES") or props.get("ConnectivitySMILES")
        inchi_key = props.get("InChIKey")

        # Cross-reference with ChEMBL for mechanism and target relationships
        chembl_id = None
        drug_targets: list[DrugTargetRelationship] = []
        if inchi_key:
            chembl_id = await self.client.find_chembl_molecule_by_inchi_key(inchi_key)
            if chembl_id:
                raw_mechanisms = await self.client.get_chembl_mechanisms(chembl_id)
                for m in raw_mechanisms:
                    target_name = m.get("target_name") or m.get("mechanism_of_action") or "Biological Target"
                    moa = m.get("mechanism_of_action") or "Pharmacological Action"
                    action_type = m.get("action_type")
                    refs = [
                        ref.get("ref_url")
                        for ref in m.get("mechanism_refs", [])
                        if ref.get("ref_url")
                    ]
                    drug_targets.append(
                        DrugTargetRelationship(
                            mechanism_of_action=moa,
                            target_name=target_name,
                            target_chembl_id=m.get("target_chembl_id"),
                            action_type=action_type,
                            references=refs,
                        )
                    )

        lipinski = evaluate_lipinski_rule_of_five(mw, xlogp, donors, acceptors)

        # Cache in PostgreSQL
        compound_id_key = f"CID:{cid}"
        cached_entry = db.scalar(
            select(CompoundCache).where(CompoundCache.compound_id == compound_id_key)
        )

        payload_to_store: dict[str, Any] = {
            "cid": cid,
            "iupac_name": props.get("IUPACName"),
            "isomeric_smiles": props.get("IsomericSMILES"),
            "xlogp": xlogp,
            "tpsa": tpsa,
            "h_bond_donor_count": donors,
            "h_bond_acceptor_count": acceptors,
            "rotatable_bond_count": rotatable,
            "exact_mass": exact_mass,
            "chembl_id": chembl_id,
            "drug_targets": [t.model_dump() for t in drug_targets],
            "raw": props,
        }

        now = datetime.now(UTC)
        if cached_entry:
            cached_entry.name = name
            cached_entry.formula = props.get("MolecularFormula")
            cached_entry.smiles = smiles
            cached_entry.inchi_key = inchi_key
            cached_entry.molecular_weight = str(mw) if mw else None
            cached_entry.source_data = payload_to_store
            cached_entry.updated_at = now
            db.add(cached_entry)
        else:
            cached_entry = CompoundCache(
                compound_id=compound_id_key,
                name=name,
                formula=props.get("MolecularFormula"),
                smiles=smiles,
                inchi_key=inchi_key,
                molecular_weight=str(mw) if mw else None,
                source="PubChem / ChEMBL",
                source_data=payload_to_store,
                retrieved_at=now,
                updated_at=now,
            )
            db.add(cached_entry)

        try:
            db.commit()
            db.refresh(cached_entry)
        except Exception:
            logger.exception("Failed to commit compound cache for CID %d", cid)
            db.rollback()

        return CompoundDetailResponse(
            cid=cid,
            name=name,
            iupac_name=props.get("IUPACName"),
            molecular_formula=props.get("MolecularFormula"),
            molecular_weight=mw,
            canonical_smiles=smiles,
            isomeric_smiles=props.get("IsomericSMILES"),
            inchi_key=inchi_key,
            xlogp=xlogp,
            tpsa=tpsa,
            h_bond_donor_count=donors,
            h_bond_acceptor_count=acceptors,
            rotatable_bond_count=rotatable,
            exact_mass=exact_mass,
            image_url=get_pubchem_image_url(cid),
            lipinski=lipinski,
            chembl_id=chembl_id,
            drug_targets=drug_targets,
            source="PubChem / ChEMBL",
            is_cached=False,
            retrieved_at=now,
        )

    async def get_targets(self, cid: int, db: Session) -> CompoundTargetsResponse:
        """Fetch targeted proteins/genes from ChEMBL for this compound."""
        details = await self.get_compound(str(cid), db=db)
        if not details:
            return CompoundTargetsResponse(cid=cid, name=f"CID {cid}", targets=[])

        return CompoundTargetsResponse(
            cid=cid,
            name=details.name,
            chembl_id=details.chembl_id,
            targets=details.drug_targets,
            source="ChEMBL",
        )

    async def get_3d_conformer(self, cid: int) -> Compound3DConformerResponse | None:
        """Fetch 3D SDF coordinates for structural viewer and docking analysis."""
        sdf = await self.client.get_3d_sdf(cid)
        if not sdf:
            return None
        return Compound3DConformerResponse(cid=cid, name=f"CID {cid}", format="sdf", sdf_data=sdf)
