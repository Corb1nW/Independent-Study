from pathlib import Path
from copy import deepcopy
import yaml

class QuantitativeSchema:
    def __init__(self, path):
        self.path = Path(path)
        self.data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        self.classes = self.data["property_classes"]
        self.template = self.data["quantitative_datum_template"]
        self.vocab = self.data["controlled_vocabularies"]

    def property_definition(self, property_id):
        for class_id, block in self.classes.items():
            if property_id in block.get("properties", {}):
                result = deepcopy(block["properties"][property_id])
                result["property_class"] = class_id
                return result
        raise KeyError(property_id)

    def properties_for_entity_class(self, entity_class):
        out = {}
        for class_id, block in self.classes.items():
            if entity_class in block.get("applies_to_classes", []):
                out[class_id] = deepcopy(block.get("properties", {}))
        return out

    def new_datum(self, property_id, entity_ids=None):
        definition = self.property_definition(property_id)
        datum = deepcopy(self.template)
        datum["target"]["entity_ids"] = list(entity_ids or [])
        datum["property_id"] = property_id
        datum["property_definition"] = definition["definition"]
        datum["value_form"] = definition["value_form"]
        datum["unit"] = definition.get("canonical_unit")
        return datum

    def load_dataset(self, path):
        return yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    def validate_datum(self, datum):
        errors = []
        required = self.data["required_datum_fields"]
        for field in required:
            if field not in datum:
                errors.append(f"missing required field: {field}")
        target = datum.get("target", {})
        if datum.get("status") == "populated" and not target.get("entity_ids"):
            errors.append("populated datum requires at least one target entity_id")
        if datum.get("datum_kind") not in self.vocab["datum_kind"]:
            errors.append(f"invalid datum_kind: {datum.get('datum_kind')}")
        if datum.get("value_form") not in self.vocab["value_form"]:
            errors.append(f"invalid value_form: {datum.get('value_form')}")
        status = datum.get("status")
        if status == "populated":
            if datum.get("value") is None:
                errors.append("populated datum has no value")
            claims = datum.get("provenance", {}).get("source_claims", [])
            if not claims and datum.get("datum_kind") != "assumed":
                errors.append("populated non-assumed datum requires source_claims")
            for claim in claims:
                if not claim.get("source_id"):
                    errors.append("source_claim missing source_id")
                if not claim.get("supports"):
                    errors.append("source_claim must identify supported claim(s)")
            definition = self.property_definition(datum["property_id"])
            if definition.get("requires_coordinate_context"):
                ctx = datum.get("coordinate_context", {})
                if not ctx.get("frame_id") and not ctx.get("coordinate_id"):
                    errors.append("coordinate-dependent datum requires frame_id or coordinate_id")
            if datum.get("datum_kind") in {"literature_derived", "model_derived", "scaled", "estimated", "calculated"}:
                if not datum.get("provenance", {}).get("transformation_history") and datum.get("datum_kind") in {"scaled", "calculated"}:
                    errors.append(f"{datum.get('datum_kind')} datum requires transformation_history")
        return errors

    def validation_report(self, datum):
        errors = self.validate_datum(datum)
        populated = datum.get("status") == "populated"
        if errors:
            readiness = "NO"
        elif populated:
            readiness = "YES"
        else:
            readiness = "NO — datum is intentionally unpopulated"

        missing = []
        if datum.get("value") is None:
            missing.append("quantitative value")
        if datum.get("datum_kind") is None:
            missing.append("datum kind")
        if not datum.get("provenance", {}).get("source_claims"):
            missing.append("evidence/source claim")
        if not datum.get("target", {}).get("entity_ids"):
            missing.append("target ontology entity")
        if datum.get("applicability", {}).get("level") is None:
            missing.append("applicability level")

        return {
            "status": str(datum.get("status", "unknown")).upper(),
            "ready_for_simulation": readiness,
            "expected_incomplete": not populated,
            "missing_information": missing,
            "validation_errors": errors,
        }

    def print_validation_report(self, datum, title="VALIDATION RESULT"):
        report = self.validation_report(datum)
        line = "=" * 72
        print(f"\n{line}\n{title}\n{line}")
        print(f"Datum status:         {report['status']}")
        print(f"Ready for simulation: {report['ready_for_simulation']}")
        if report["expected_incomplete"]:
            print("Interpretation:        This datum is intentionally incomplete; rejection is expected.")
        else:
            print("Interpretation:        Populated datum is being checked for evidence readiness.")
        if report["missing_information"]:
            print("\nMissing information:")
            for item in report["missing_information"]:
                print(f"  - {item}")
        if report["validation_errors"]:
            print("\nValidator messages:")
            for error in report["validation_errors"]:
                print(f"  - {error}")
        else:
            print("\nValidator messages:   PASS — no schema violations found.")
        print(line)
