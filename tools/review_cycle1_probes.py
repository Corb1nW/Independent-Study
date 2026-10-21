"""Review Cycle 1 probes (Claude, 2026-10-07).

Reproduces the findings in docs/reviews/2026-10-07_Claude_Technical_Review.pdf
(defects D1-D8 and Appendix A). Run from the repository root:

    python tools/review_cycle1_probes.py

Against the baseline commit, every "validator probe" line is expected to print
ACCEPTED (the defect). After Phase A, each should print REJECTED.

Note (D-026): probe 1 changes a unit label without converting the value. That is a
relabeling error, not an invalid unit; it is kept for traceability, but the
meaningful unit probes are 1b (incompatible dimension) and 2 (missing unit).
"""
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ontology import AnatomyOntology  # noqa: E402
from src.quantitative import QuantitativeSchema  # noqa: E402

onto = AnatomyOntology(ROOT / "ontology" / "hip.yaml")
q = QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
data = q.load_dataset(ROOT / "ontology" / "quantitative_data" / "gluteus_maximus.yaml")
ids = set(onto.entities)
obs = data["observations"]

print("== Cross-file references (D1) ==")
for k, v in obs.items():
    for e in v["target"]["entity_ids"]:
        if e not in ids:
            print(f"  UNRESOLVED target {e} in {k}")
    for f in ("frame_id", "coordinate_id"):
        ref = (v.get("coordinate_context") or {}).get(f)
        if ref and ref not in ids:
            print(f"  UNRESOLVED {f} {ref} in {k}")

print("== Parameter names in ontology not in schema (D2) ==")
names = {n for e in onto.entities.values() for n in e.get("model_parameter_schema", [])}
for n in sorted(names):
    try:
        q.property_definition(n)
    except KeyError:
        print(f"  {n}")

print("== Ontology classes receiving no quantitative properties (D3) ==")
for c in sorted({e["class"] for e in onto.entities.values()}):
    if not q.properties_for_entity_class(c):
        print(f"  {c}")

print("== Datum vs. property definition mismatches (D5) ==")
for k, v in obs.items():
    p = q.property_definition(v["property_id"])
    if p["value_form"] != v["value_form"]:
        print(f"  {k}: schema form {p['value_form']}, datum form {v['value_form']}")

print("== Validator probes (D4 / Appendix A) ==")
base = obs["LB-QD:GMAX:MASS:WARD2009"]


def probe(label, mutate):
    d = deepcopy(base)
    mutate(d)
    errs = q.validate_datum(d, data)
    print(f"  {'REJECTED' if errs else 'ACCEPTED'}  {label}" + (f"  -> {errs}" if errs else ""))


probe("1  unit relabeled kg->lb without conversion (see D-026)", lambda d: d.update(unit="lb"))
probe("1b unit with incompatible dimension (m on a mass)", lambda d: d.update(unit="m"))
probe("2  unit missing (null)", lambda d: d.update(unit=None))
probe("3  negative mass", lambda d: d.update(value=-5))


def typo(d):
    d.update(status="Populated", value=None)
    d["provenance"]["source_claims"] = []


probe("4  status typo 'Populated', no value, no source", typo)


def assumed(d):
    d.update(datum_kind="assumed", value=9999)
    d["provenance"]["source_claims"] = []


probe("5  assumed value, no source, no rationale", assumed)
probe("6  invalid applicability level", lambda d: d["applicability"].update(level="individual-ish"))
probe("7  unknown source_id",
      lambda d: d["provenance"]["source_claims"][0].update(source_id="SRC:DOES_NOT_EXIST"))
probe("8  unknown target entity", lambda d: d["target"].update(entity_ids=["LB:MUS:NOT_A_MUSCLE"]))
