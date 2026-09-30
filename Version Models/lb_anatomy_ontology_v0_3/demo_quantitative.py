from pathlib import Path
from src.quantitative import QuantitativeSchema

ROOT = Path(__file__).parent
q = QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")

print("Musculotendon properties available to SkeletalMuscle:")
for group, properties in q.properties_for_entity_class("SkeletalMuscle").items():
    print(f"  {group}:")
    for name in properties:
        print(f"    - {name}")

print("\nBlank, provenance-ready maximum-isometric-force datum:")
datum = q.new_datum("maximum_isometric_force")
print(datum)
print("\nValidation before a value/source is supplied:", q.validate_datum(datum))
