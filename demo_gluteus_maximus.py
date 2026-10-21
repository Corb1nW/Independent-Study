from pathlib import Path
from src.quantitative import QuantitativeSchema

ROOT = Path(__file__).parent
q = QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
data = q.load_dataset(ROOT / "ontology" / "quantitative_data" / "gluteus_maximus.yaml")


# load_dataset() resolves dataset defaults (QuantitativeSchema.resolve_defaults), so records
# can be used directly; there is a single defaults implementation (D-024, defect D6).

print("\nLB-AO — GLUTEUS MAXIMUS REFERENCE MUSCLE AUDIT (dataset " + data["dataset"]["version"] + ")")
print("=" * 78)
print("Baseline policy: one evidence-backed generic baseline initializes LEFT and RIGHT.")
print("This is a MODEL ASSUMPTION, not a claim that human anatomy is perfectly symmetric.")
print("Each side remains independently overridable for future personalization.\n")

for obs_id, raw in data["observations"].items():
    d = raw
    print("-" * 78)
    print(obs_id)
    print(f"Property:       {d['property_id']}")
    print(f"Role:           {d.get('property_role')}")
    print(f"Evidence kind:  {d.get('datum_kind')}")
    print(f"Status:         {d.get('status')}")
    if d.get("value") is not None:
        print(f"Value:          {d['value']} {d.get('unit')}")
        u = d.get("uncertainty", {})
        if u.get("value") is not None:
            print(f"Uncertainty:    {u.get('type')} = {u['value']} {u.get('unit')}")
    else:
        print("Value:          intentionally unresolved / computed at runtime")
    claims = d.get("provenance", {}).get("source_claims", [])
    print("Evidence:")
    if claims:
        for c in claims:
            print(f"  - {c['source_id']} supports {', '.join(c.get('supports', []))}")
    else:
        print("  - no numeric source promoted; model selection/evidence still required")
    deriv = d.get("derivation", {})
    if deriv.get("formula"):
        print(f"Derivation:     {deriv['formula']}")
    if deriv.get("assumptions"):
        print("Assumptions:")
        for a in deriv["assumptions"]:
            print(f"  - {a}")
    if d.get("status") == "populated":
        errors = q.validate_datum(d, data)
        print("Validation:     " + ("PASS" if not errors else "FAIL"))
        for e in errors:
            print(f"  - {e}")
    else:
        print("Validation:     NOT A FIXED POPULATED DATUM — this is intentional")

print("\n" + "=" * 78)
print("SUMMARY")
print("  Direct/literature architecture: mass, muscle length, fiber length, pennation, PCSA")
print("  Model-derived parameter: maximum isometric force")
print("  Model-specific unresolved: tendon slack length, contraction velocity, activation constants")
print("  Functions of state: moment arm r(q), musculotendon length L_MT(q)")
print("  Dynamic output: muscle force F(t)")
print("  Bilateral baseline: shared initially; LEFT/RIGHT can be independently overridden later")
print("=" * 78)
