"""LB-QPS quantitative schema: loading, defaults resolution and validation.

Validation runs in layers (D-035):
  1. structural  - field names and types (Pydantic models in src/datum_model.py)
  2. semantic    - controlled vocabularies, property definition, units (D-026),
                   physical bounds, coordinate context, cross-file references
  3. evidence    - source claims, assumptions, derivations, applicability
validation_report() states whether a datum is admissible as a candidate simulation
input. That is a datum-level check only: model-level simulation readiness (geometry,
dynamics, parameter completeness, force-to-torque representation) is D-035's fourth
layer and is not implemented before Phase C.

What the evidence layer does and does not establish (review finding A4): it checks
that provenance metadata is complete and that every cited source is registered.
It does not check that a cited source actually supports the value; that is
source-level verification by a reviewer (D-045).

Source registry (review finding A1): a datum may cite sources registered in the
ontology plus, when validated with its dataset, that dataset's own `sources` block.
Loading a dataset never changes what other datasets may cite.

Reference fields checked (review finding A2):
  target.entity_ids[]                         -> ontology entity
  coordinate_context.frame_id, coordinate_id  -> ontology entity
  coordinate_context.convention_source_id     -> source registry
  provenance.source_claims[].source_id        -> source registry
  derivation.inputs[].source_id (structured)  -> source registry
  quality.value_comparisons[].related_observation -> observation in the same dataset*
  quality.conflicts_with[]                    -> observation in the same dataset*
  normalization.reference_observation         -> observation in the same dataset* whose
                                                 property is normalization.length_property (C3)
  (* checked when validate_datum() is given the dataset; integrity check always does)
Free-text descriptions, not references, and therefore not checked:
  method.derived_from[], derivation.inputs[] given as plain strings.

Error messages from the baseline validator are kept verbatim where the rule is
unchanged, so existing tests and documents still match.
"""
from copy import deepcopy
from math import isclose
from pathlib import Path

import pint
import yaml
from pydantic import ValidationError

from .datum_model import Datum
from .ontology import AnatomyOntology

UNITS = pint.UnitRegistry()
# Velocity normalized by optimal fiber length (LB-QPS maximum_contraction_velocity).
UNITS.define("optimal_fiber_lengths = [normalized_length]")

DEFAULTABLE_FIELDS = ("target", "symmetry_policy", "applicability", "quality")
EMPTY_COORDINATE_CONTEXT = {"frame_id": None, "coordinate_id": None, "convention_source_id": None,
                            "axis": None, "reference_pose": None}


def _parse_unit(unit):
    return UNITS.parse_units(str(unit)) if str(unit) != "1" else UNITS.dimensionless


class QuantitativeSchema:
    def __init__(self, path, ontology=None):
        self.path = Path(path)
        self.data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        self.classes = self.data["property_classes"]
        self.template = self.data["quantitative_datum_template"]
        self.vocab = self.data["controlled_vocabularies"]
        self.property_aliases = self.data.get("property_aliases", {}) or {}
        if ontology is None and self.data.get("ontology"):
            ontology = AnatomyOntology(self.path.parent / self.data["ontology"])
        self.ontology = ontology
        # Project-wide sources (the ontology's). Dataset-specific sources are added per
        # validation call by source_registry(dataset), never accumulated here (A1).
        self.known_sources = set(ontology.sources) if ontology else set()

    # ------------------------------------------------------------------ properties
    def canonical_property_id(self, property_id):
        """Resolve a deprecated property name to its canonical ID (D-039 Amendment 1)."""
        alias = self.property_aliases.get(property_id)
        return alias["canonical"] if alias else property_id

    def property_definition(self, property_id):
        pid = self.canonical_property_id(property_id)
        for class_id, block in self.classes.items():
            if pid in block.get("properties", {}):
                result = deepcopy(block["properties"][pid])
                result["property_class"] = class_id
                result["property_id"] = pid
                result.setdefault("allowed_value_forms", [result["value_form"]])
                return result
        raise KeyError(property_id)

    def properties_for_entity_class(self, entity_class):
        """Properties applicable to a class, including those inherited through IS_A (D-031)."""
        lineage = self.ontology.class_ancestors(entity_class) if self.ontology else [entity_class]
        out = {}
        for class_id, block in self.classes.items():
            if any(c in block.get("applies_to_classes", []) for c in lineage):
                out[class_id] = deepcopy(block.get("properties", {}))
        return out

    def property_applies_to_entity(self, property_id, entity_id):
        definition = self.property_definition(property_id)
        cls = self.ontology.get(entity_id)["class"]
        return definition["property_class"] in self.properties_for_entity_class(cls)

    def new_datum(self, property_id, entity_ids=None):
        definition = self.property_definition(property_id)
        datum = deepcopy(self.template)
        datum["target"]["entity_ids"] = list(entity_ids or [])
        datum["property_id"] = definition["property_id"]
        datum["property_definition"] = definition["definition"]
        datum["value_form"] = definition["value_form"]
        datum["property_role"] = definition.get("property_role")
        datum["unit"] = definition.get("canonical_unit")
        return datum

    def convert_to_canonical(self, value, unit, property_id):
        """Convert a value to the property's canonical unit and return (value, transformation step)."""
        canonical = self.property_definition(property_id)["canonical_unit"]
        converted = (value * _parse_unit(unit)).to(_parse_unit(canonical)).magnitude
        step = {"operation": "unit_conversion", "input_value": value, "input_unit": unit,
                "output_value": converted, "output_unit": canonical,
                "formula": f"pint conversion {unit} -> {canonical}"}
        return converted, step

    # ------------------------------------------------------------------ datasets
    @staticmethod
    def resolve_defaults(observation, common):
        """Single defaults-resolution implementation (D-024 / defect D6).

        Precedence: a field stated on the observation wins over the dataset's `common`
        block, wholesale (no deep merge), so one study's context is never mixed into a
        record that states its own. Missing coordinate_context becomes an explicit
        empty context.
        """
        d = deepcopy(observation)
        for key in DEFAULTABLE_FIELDS:
            if key not in d and key in (common or {}):
                d[key] = deepcopy(common[key])
        d.setdefault("coordinate_context", deepcopy(EMPTY_COORDINATE_CONTEXT))
        return d

    def load_dataset(self, path):
        dataset = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        common = dataset.get("common", {})
        if "observations" in dataset:
            dataset["observations"] = {k: self.resolve_defaults(v, common)
                                       for k, v in dataset["observations"].items()}
        return dataset

    def dataset_observations(self, dataset):
        return dataset.get("observations", {})

    def resolve_observation_ids(self, dataset, observation_id):
        """Return current observation IDs for an ID, following documented aliases."""
        if observation_id in dataset.get("observations", {}):
            return [observation_id]
        alias = (dataset.get("observation_aliases") or {}).get(observation_id)
        if alias:
            return list(alias["replaced_by"])
        raise KeyError(observation_id)

    def observations_for_target(self, dataset, entity_id):
        return {k: v for k, v in self.dataset_observations(dataset).items()
                if entity_id in v.get("target", {}).get("entity_ids", [])}

    def effective_baseline(self, dataset, entity_id):
        """Return populated parameter observations applicable to an entity.

        Shared bilateral baseline records remain shared evidence; this method does not
        duplicate them into false side-specific measurements.
        """
        return {k: v for k, v in self.observations_for_target(dataset, entity_id).items()
                if v.get("status") == "populated" and v.get("property_role") == "parameter"}

    # ------------------------------------------------------------------ validation
    def source_registry(self, dataset=None):
        """Sources a datum may cite: the ontology's, plus the given dataset's own (A1)."""
        return self.known_sources | set((dataset or {}).get("sources", {}) or {})

    def validate_datum(self, datum, dataset=None):
        """Validate one datum. Pass the dataset it belongs to so that the dataset's own
        sources and observation IDs can be resolved; without it, only ontology sources
        are known and observation cross-references are not checked."""
        errors = []
        required = self.data["required_datum_fields"]
        for field in required:
            if field not in datum:
                errors.append(f"missing required field: {field}")
        try:
            Datum.model_validate(datum)
        except ValidationError as exc:
            for e in exc.errors():
                loc = ".".join(str(p) for p in e["loc"])
                if e["type"] == "missing" and len(e["loc"]) == 1:
                    continue  # already reported above
                errors.append(f"structure: {loc}: {e['msg']}")
        if errors:
            return errors  # semantic checks assume a well-formed record
        errors += self._semantic_errors(datum, dataset)
        errors += self._evidence_errors(datum, dataset)
        return errors

    def _vocab_error(self, field, value, vocab_key, allow_null=False):
        if value is None and allow_null:
            return []
        if value not in self.vocab[vocab_key]:
            return [f"invalid {field}: {value}"]
        return []

    def _semantic_errors(self, d, dataset=None):
        errors = []
        status = d.get("status")
        populated = status == "populated"
        errors += self._vocab_error("status", status, "status")
        errors += self._vocab_error("datum_kind", d.get("datum_kind"), "datum_kind", allow_null=not populated)
        errors += self._vocab_error("value_form", d.get("value_form"), "value_form")
        errors += self._vocab_error("property_role", d.get("property_role"), "property_role")
        level = (d.get("applicability") or {}).get("level")
        errors += self._vocab_error("applicability level", level, "applicability_level", allow_null=True)
        unc = d.get("uncertainty") or {}
        errors += self._vocab_error("uncertainty type", unc.get("type"), "uncertainty_type", allow_null=True)
        for claim in (d.get("provenance") or {}).get("source_claims") or []:
            errors += self._vocab_error("evidence_domain", claim.get("evidence_domain"), "evidence_domain",
                                        allow_null=True)
        for comp in (d.get("quality") or {}).get("value_comparisons") or []:
            errors += self._vocab_error("value comparison relationship", comp.get("relationship"),
                                        "value_comparison_relationship")

        # property definition is authoritative (defect D5)
        try:
            definition = self.property_definition(d["property_id"])
        except KeyError:
            return errors + [f"unknown property_id: {d['property_id']}"]
        if d["property_id"] != definition["property_id"]:
            errors.append(f"property_id {d['property_id']} is deprecated; use {definition['property_id']}")
        if definition.get("property_role") and d.get("property_role") != definition["property_role"]:
            errors.append(f"property_role {d.get('property_role')} does not match definition "
                          f"({definition['property_role']})")
        if d.get("value_form") not in definition["allowed_value_forms"]:
            errors.append(f"value_form {d.get('value_form')} not allowed for {definition['property_id']} "
                          f"(allowed: {definition['allowed_value_forms']})")

        errors += self._unit_errors(d, definition, populated)
        errors += self._bounds_errors(d, definition, populated)
        errors += self._reference_errors(d, definition, populated)
        errors += self._observation_reference_errors(d, dataset)
        errors += self._normalization_errors(d, definition, populated, dataset)
        return errors

    def _unit_errors(self, d, definition, populated):
        """D-026: units must be present (when populated), dimensionally compatible, and
        stored in the canonical unit (D-017); conversions are checked against history."""
        errors = []
        canonical = definition.get("canonical_unit")
        unit = d.get("unit")
        if canonical is None:
            return errors
        if unit is None:
            if populated:
                errors.append("populated datum requires a unit")
            return errors
        try:
            parsed, canon = _parse_unit(unit), _parse_unit(canonical)
        except Exception:  # pint raises several error types for unknown units
            return [f"unrecognized unit: {unit}"]
        if parsed.dimensionality != canon.dimensionality:
            errors.append(f"unit {unit} is dimensionally incompatible with {canonical}")
        elif populated and parsed != canon:
            errors.append(f"unit {unit} is not the canonical unit {canonical}; convert the value and "
                          f"record the conversion in transformation_history (D-017, D-026)")
        unc = d.get("uncertainty") or {}
        if unc.get("value") is not None and unc.get("unit") is not None:
            try:
                if _parse_unit(unc["unit"]) != parsed:
                    errors.append(f"uncertainty unit {unc['unit']} differs from datum unit {unit}")
            except Exception:
                errors.append(f"unrecognized uncertainty unit: {unc['unit']}")
        # Relabeling check: the last recorded conversion must produce the stored value and unit.
        history = (d.get("provenance") or {}).get("transformation_history") or []
        value_steps = [s for s in history if not str(s.get("operation", "")).startswith("uncertainty")]
        if populated and value_steps and isinstance(d.get("value"), (int, float)):
            last = value_steps[-1]
            if last.get("output_unit") != unit or last.get("output_value") is None \
                    or not isclose(last["output_value"], d["value"], rel_tol=1e-9, abs_tol=1e-12):
                errors.append(f"value/unit ({d.get('value')} {unit}) do not match the last recorded "
                              f"transformation output ({last.get('output_value')} {last.get('output_unit')})")
        unc_steps = [s for s in history if str(s.get("operation", "")).startswith("uncertainty")]
        if populated and unc_steps and unc.get("value") is not None:
            last = unc_steps[-1]
            if last.get("output_value") is None or not isclose(last["output_value"], unc["value"], rel_tol=1e-9):
                errors.append("uncertainty value does not match the last recorded uncertainty transformation")
        return errors

    def _bounds_errors(self, d, definition, populated):
        errors = []
        bounds = definition.get("bounds")
        value = d.get("value")
        if populated and bounds and d.get("value_form") == "scalar" and isinstance(value, (int, float)):
            lo, hi = bounds.get("min"), bounds.get("max")
            if lo is not None and (value < lo or (value == lo and not bounds.get("min_inclusive", True))):
                errors.append(f"value {value} is below the physical bound for {definition['property_id']} "
                              f"({'≥' if bounds.get('min_inclusive', True) else '>'} {lo})")
            if hi is not None and (value > hi or (value == hi and not bounds.get("max_inclusive", True))):
                errors.append(f"value {value} is above the physical bound for {definition['property_id']} "
                              f"({'≤' if bounds.get('max_inclusive', True) else '<'} {hi})")
        unc = d.get("uncertainty") or {}
        if isinstance(unc.get("value"), (int, float)) and unc["value"] < 0:
            errors.append("uncertainty value must be non-negative")
        return errors

    def _reference_errors(self, d, definition, populated):
        """Targets and coordinate references must resolve in the ontology (D1, D3, D8)."""
        errors = []
        targets = (d.get("target") or {}).get("entity_ids") or []
        if populated and not targets:
            errors.append("populated datum requires at least one target entity_id")
        ctx = d.get("coordinate_context") or {}
        if populated and definition.get("requires_coordinate_context"):
            if not ctx.get("frame_id") and not ctx.get("coordinate_id"):
                errors.append("coordinate-dependent datum requires frame_id or coordinate_id")
        if not self.ontology:
            return errors
        ids = self.ontology.entities
        target_sides = set()
        for t in targets:
            if t not in ids:
                errors.append(f"target entity {t} does not exist in the ontology")
                continue
            target_sides.add(ids[t].get("side"))
            if not self.property_applies_to_entity(definition["property_id"], t):
                errors.append(f"property {definition['property_id']} does not apply to {t} "
                              f"(class {ids[t]['class']})")
        for field in ("frame_id", "coordinate_id"):
            ref = ctx.get(field)
            if ref and ref not in ids:
                errors.append(f"coordinate_context.{field} {ref} does not exist in the ontology")
        coord = ctx.get("coordinate_id")
        if coord in ids and ids[coord].get("side"):
            other = target_sides - {ids[coord]["side"]}
            if other:
                errors.append(f"coordinate {coord} is {ids[coord]['side']}-sided but the record also targets "
                              f"{sorted(str(s) for s in other)} entities; split the record per side")
        return errors

    def _normalization_errors(self, d, definition, populated, dataset):
        """Normalized quantities name their normalizing length (D-050 caveat, D-055 C3).

        A populated datum of a property with `normalization_required` must state
        `normalization.length_property` (as the schema requires) and
        `normalization.reference_observation`. The reference must resolve in the same
        dataset (current ID or alias) to an observation of that length property;
        resolution is checked when the dataset is given. Properties without the
        requirement may not carry a normalization block.
        """
        required = definition.get("normalization_required")
        norm = d.get("normalization")
        if not required:
            return [f"normalization is not defined for {definition['property_id']}"] if norm else []
        errors = []
        if norm is None:
            if populated:
                errors.append(f"populated {definition['property_id']} must declare normalization "
                              f"(length_property: {required['length_property']})")
            return errors
        if norm.get("length_property") != required["length_property"]:
            errors.append(f"normalization.length_property must be {required['length_property']}, "
                          f"not {norm.get('length_property')}")
        ref = norm.get("reference_observation")
        if populated and not ref:
            errors.append("populated normalized datum must name normalization.reference_observation")
        if ref and dataset is not None:
            try:
                ids = self.resolve_observation_ids(dataset, ref)
            except KeyError:
                return errors + [f"normalization.reference_observation {ref} does not exist in the dataset"]
            for oid in ids:
                pid = dataset["observations"][oid].get("property_id")
                if self.canonical_property_id(pid) != required["length_property"]:
                    errors.append(f"normalization.reference_observation {oid} is {pid}, "
                                  f"not {required['length_property']}")
        return errors

    def _observation_reference_errors(self, d, dataset):
        """quality.value_comparisons / conflicts_with must name observations in the same
        dataset, by current ID or documented alias (A2). Skipped without a dataset."""
        if dataset is None:
            return []
        known = set(dataset.get("observations", {})) | set(dataset.get("observation_aliases") or {})
        quality = d.get("quality") or {}
        errors = []
        for comp in quality.get("value_comparisons") or []:
            ref = comp.get("related_observation")
            if ref and ref not in known:
                errors.append(f"quality.value_comparisons related_observation {ref} does not exist in the dataset")
        for ref in quality.get("conflicts_with") or []:
            if ref not in known:
                errors.append(f"quality.conflicts_with {ref} does not exist in the dataset")
        return errors

    def _evidence_errors(self, d, dataset=None):
        errors = []
        registry = self.source_registry(dataset)
        # Source references outside source_claims are checked whatever the status (A2).
        conv = (d.get("coordinate_context") or {}).get("convention_source_id")
        if conv and registry and conv not in registry:
            errors.append(f"coordinate_context.convention_source_id cites unknown source {conv}")
        for item in (d.get("derivation") or {}).get("inputs") or []:
            if isinstance(item, dict) and item.get("source_id") and registry \
                    and item["source_id"] not in registry:
                errors.append(f"derivation input {item.get('name')} cites unknown source {item['source_id']}")
        if d.get("status") != "populated":
            return errors
        kind = d.get("datum_kind")
        if d.get("value") is None:
            errors.append("populated datum has no value")
        if (d.get("applicability") or {}).get("level") is None:
            errors.append("populated datum requires an applicability level")
        claims = (d.get("provenance") or {}).get("source_claims") or []
        if not claims and kind != "assumed":
            errors.append("populated non-assumed datum requires source_claims")
        for claim in claims:
            if not claim.get("source_id"):
                errors.append("source_claim missing source_id")
            elif registry and claim["source_id"] not in registry:
                errors.append(f"source_claim cites unknown source {claim['source_id']}")
            elif not registry:
                errors.append(f"cannot verify source {claim['source_id']}: no source registry loaded")
            if not claim.get("supports"):
                errors.append("source_claim must identify supported claim(s)")
        derivation = d.get("derivation") or {}
        if kind == "assumed" and not derivation.get("assumptions"):
            errors.append("assumed datum requires a stated rationale in derivation.assumptions")
        history = (d.get("provenance") or {}).get("transformation_history") or []
        if kind in {"scaled", "calculated"} and not history:
            errors.append(f"{kind} datum requires transformation_history")
        if kind == "model_derived":
            if not derivation.get("formula"):
                errors.append("model_derived datum requires derivation.formula")
            if not (d.get("applicability") or {}).get("model_id"):
                errors.append("model_derived datum must identify its model in applicability.model_id")
        return errors

    def validation_report(self, datum, dataset=None):
        """Datum-level report. `admissible_as_simulation_input` means the datum passed
        structural, semantic and evidence checks and may be offered to a model; it is
        not model-level simulation readiness (A3; D-035 layer 4, Phase C)."""
        errors = self.validate_datum(datum, dataset)
        populated = datum.get("status") == "populated"
        if errors:
            admissible = "NO"
        elif populated:
            admissible = "YES (datum-level checks only; not model readiness)"
        else:
            admissible = "NO — datum is intentionally unpopulated"

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
            "admissible_as_simulation_input": admissible,
            "expected_incomplete": not populated,
            "missing_information": missing,
            "validation_errors": errors,
        }

    def print_validation_report(self, datum, title="VALIDATION RESULT", dataset=None):
        report = self.validation_report(datum, dataset)
        line = "=" * 72
        print(f"\n{line}\n{title}\n{line}")
        print(f"Datum status:         {report['status']}")
        print(f"Admissible as simulation input: {report['admissible_as_simulation_input']}")
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
