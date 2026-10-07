"""Project-wide cross-file integrity check (D-024; DECISIONS.md D1, D2, D3, D8).

Checks that every reference between the ontology, the quantitative schema and the
quantitative datasets resolves, and that every observation passes validation.

    python -m src.integrity          # from the repository root; exit code 1 on failure
"""
import sys
from pathlib import Path

from .quantitative import QuantitativeSchema

ROOT = Path(__file__).resolve().parents[1]


def check_project(root=ROOT):
    root = Path(root)
    errors = []
    schema = QuantitativeSchema(root / "ontology" / "quantitative_schema.yaml")
    onto = schema.ontology  # loading also runs the ontology's own validation

    # Ontology -> schema: listed model parameters must be canonical schema properties
    # that apply to the entity's class (D2, D3).
    for eid, e in onto.entities.items():
        for name in e.get("model_parameter_schema", []) or []:
            try:
                definition = schema.property_definition(name)
            except KeyError:
                errors.append(f"{eid}: model_parameter_schema lists unknown property {name}")
                continue
            if name != definition["property_id"]:
                errors.append(f"{eid}: model_parameter_schema uses deprecated name {name}; "
                              f"use {definition['property_id']}")
            if not schema.property_applies_to_entity(name, eid):
                errors.append(f"{eid}: property {name} does not apply to class {e['class']}")

    # Ontology model views must reference existing entities.
    for model_id, model in (onto.data.get("models") or {}).items():
        for key in ("represents", "retained_coordinates", "omitted_coordinates"):
            for ref in model.get(key, []) or []:
                if ref not in onto.entities:
                    errors.append(f"model {model_id}: {key} references missing {ref}")

    # Class hierarchy parents must be classes the schema or ontology knows about.
    schema_classes = {c for b in schema.classes.values() for c in b.get("applies_to_classes", [])}
    onto_classes = {e["class"] for e in onto.entities.values()}
    for child, parent in onto.class_hierarchy.items():
        if child not in onto_classes:
            errors.append(f"class_hierarchy: {child} is not used by any entity")
        if parent not in schema_classes | onto_classes | set(onto.class_hierarchy):
            errors.append(f"class_hierarchy: parent {parent} of {child} is unknown")

    # Datasets: every observation validates; aliases point to existing observations.
    for path in sorted((root / "ontology" / "quantitative_data").glob("*.yaml")):
        dataset = schema.load_dataset(path)
        observations = dataset.get("observations", {})
        for obs_id, obs in observations.items():
            for msg in schema.validate_datum(obs):
                errors.append(f"{path.name}: {obs_id}: {msg}")
        for old_id, alias in (dataset.get("observation_aliases") or {}).items():
            if old_id in observations:
                errors.append(f"{path.name}: alias {old_id} is still an active observation ID")
            for new_id in alias.get("replaced_by", []):
                if new_id not in observations:
                    errors.append(f"{path.name}: alias {old_id} points to missing {new_id}")
        policy = (dataset.get("dataset") or {}).get("bilateral_policy") or {}
        for ref in policy.get("shared_baseline_targets", []) or []:
            if ref not in onto.entities:
                errors.append(f"{path.name}: bilateral_policy references missing {ref}")
    return errors


def main():
    errors = check_project()
    if errors:
        print(f"INTEGRITY CHECK FAILED ({len(errors)} problems)")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("INTEGRITY CHECK PASSED: all cross-file references resolve and all observations validate.")


if __name__ == "__main__":
    main()
