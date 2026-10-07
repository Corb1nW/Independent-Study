from pathlib import Path
from src.quantitative import QuantitativeSchema

ROOT = Path(__file__).parent
q = QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")

print("\nLB-QPS QUANTITATIVE SCHEMA DEMONSTRATION")
print("=" * 72)
print("Musculotendon properties available to SkeletalMuscle:")
for group, properties in q.properties_for_entity_class("SkeletalMuscle").items():
    print(f"  {group}:")
    for name in properties:
        print(f"    - {name}")

print("\nTEST 1 — BLANK DATUM")
print("Purpose: prove that the ontology does not invent a quantitative value.")
datum = q.new_datum("maximum_isometric_force", ["LB:MUS:GLUTEUS_MAXIMUS_R"])
q.print_validation_report(datum, "EXPECTED VALIDATION RESULT — BLANK DATUM")

print("\nTEST 2 — FIRST POPULATED GLUTEUS MAXIMUS EVIDENCE CHAIN")
print("Purpose: load a real literature-derived observation and verify provenance.")
dataset = q.load_dataset(ROOT / "ontology" / "quantitative_data" / "gluteus_maximus.yaml")
obs_id = "LB-QD:GMAX:OPTIMAL_FIBER_LENGTH:WARD2009"
obs = dataset["observations"][obs_id]
print(f"Observation ID: {obs_id}")
print(f"Property:       {obs['property_id']}")
print(f"Value:          {obs['value']} {obs['unit']}")
print(f"Uncertainty:    SD {obs['uncertainty']['value']} {obs['uncertainty']['unit']}")
print(f"Sample size:    n={obs['applicability']['sample_size']}")
print("Targets:")
for entity_id in obs["target"]["entity_ids"]:
    print(f"  - {entity_id}")
print("Evidence chain:")
for claim in obs["provenance"]["source_claims"]:
    print(f"  - {claim['source_id']}: {', '.join(claim['supports'])}")
print("Transformations:")
for step in obs["provenance"]["transformation_history"]:
    print(f"  - {step['operation']}: {step['input_value']} {step['input_unit']} -> {step['output_value']} {step['output_unit']}")
q.print_validation_report(obs, "VALIDATION RESULT — POPULATED LITERATURE DATUM")

print("\nWORKFLOW SUMMARY")
print("  Primary measurement -> source claim -> unit-preserving transformation")
print("  -> applicability/limitations -> ontology datum -> validator")
print("\nImportant: this cohort value is NOT a subject-specific measurement and is")
print("not automatically promoted to a personalized digital-twin parameter.")
