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

    def new_datum(self, property_id):
        definition = self.property_definition(property_id)
        datum = deepcopy(self.template)
        datum["property_id"] = property_id
        datum["property_definition"] = definition["definition"]
        datum["value_form"] = definition["value_form"]
        datum["unit"] = definition.get("canonical_unit")
        return datum

    def validate_datum(self, datum):
        errors = []
        required = self.data["required_datum_fields"]
        for field in required:
            if field not in datum:
                errors.append(f"missing required field: {field}")
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
            definition = self.property_definition(datum["property_id"])
            if definition.get("requires_coordinate_context"):
                ctx = datum.get("coordinate_context", {})
                if not ctx.get("frame_id") and not ctx.get("coordinate_id"):
                    errors.append("coordinate-dependent datum requires frame_id or coordinate_id")
        return errors
