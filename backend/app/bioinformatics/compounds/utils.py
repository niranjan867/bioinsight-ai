from app.bioinformatics.compounds.schemas import LipinskiRuleOfFive


def evaluate_lipinski_rule_of_five(
    molecular_weight: float | None,
    xlogp: float | None,
    h_bond_donors: int | None,
    h_bond_acceptors: int | None,
) -> LipinskiRuleOfFive:
    """Evaluate Lipinski's Rule of 5 for drug-likeness.

    Criteria:
    - Molecular weight <= 500 Da
    - LogP <= 5.0
    - H-bond donors <= 5
    - H-bond acceptors <= 10
    A drug-like molecule typically has no more than 1 violation.
    """
    mw_pass = molecular_weight is None or molecular_weight <= 500.0
    logp_pass = xlogp is None or xlogp <= 5.0
    donors_pass = h_bond_donors is None or h_bond_donors <= 5
    acceptors_pass = h_bond_acceptors is None or h_bond_acceptors <= 10

    violations = 0
    if not mw_pass:
        violations += 1
    if not logp_pass:
        violations += 1
    if not donors_pass:
        violations += 1
    if not acceptors_pass:
        violations += 1

    return LipinskiRuleOfFive(
        molecular_weight_pass=mw_pass,
        logp_pass=logp_pass,
        h_bond_donors_pass=donors_pass,
        h_bond_acceptors_pass=acceptors_pass,
        violations_count=violations,
        is_druglike=(violations <= 1),
    )


def get_pubchem_image_url(cid: int) -> str:
    """Return canonical 2D structure image URL for a PubChem CID."""
    return f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG"

