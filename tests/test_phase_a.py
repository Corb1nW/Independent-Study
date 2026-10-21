"""Phase A (Integrity) tests — DECISIONS.md D-024, D-025, D-026, D-027, D-031, D-034, D-035.

Each validator rule has a failing-case test (D-025): a malformed record must be rejected
with a message that names the problem. Legitimate records and conversions must pass.
"""
from copy import deepcopy
from math import isclose, pi
from pathlib import Path

import pytest

from src.integrity import check_project
from src.ontology import AnatomyOntology
from src.quantitative import QuantitativeSchema

ROOT = Path(__file__).parents[1]
q = QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
data = q.load_dataset(ROOT / "ontology" / "quantitative_data" / "gluteus_maximus.yaml")
OBS = data["observations"]
MASS = "LB-QD:GMAX:MASS:WARD2009"


def mass(**changes):
    d = deepcopy(OBS[MASS])
    d.update(changes)
    return d


def errors_contain(d, fragment):
    errs = q.validate_datum(d, data)
    assert any(fragment in e for e in errs), f"expected '{fragment}' in {errs}"


# ---------------------------------------------------------------- baseline still valid
def test_valid_record_passes():
    assert q.validate_datum(OBS[MASS], data) == []


def test_project_integrity_passes():
    assert check_project(ROOT) == []


# ---------------------------------------------------------------- D-026 units
def test_missing_unit_rejected():                      # probe 2
    errors_contain(mass(unit=None), "requires a unit")


def test_incompatible_unit_rejected():                 # probe 1b
    errors_contain(mass(unit="m"), "dimensionally incompatible")


def test_unrecognized_unit_rejected():
    errors_contain(mass(unit="furlongs-ish"), "unrecognized unit")


def test_relabeled_unit_rejected():                    # probe 1: label changed, value not converted
    d = mass(unit="lb")
    d["uncertainty"]["unit"] = "lb"
    errors_contain(d, "do not match the last recorded transformation output")


def test_compatible_non_canonical_unit_must_be_converted():
    d = mass(unit="lb")
    d["uncertainty"]["unit"] = "lb"
    d["provenance"]["transformation_history"] = []
    errors_contain(d, "not the canonical unit")


def test_valid_conversion_passes():
    """A value reported in pounds, converted with convert_to_canonical, validates."""
    d = deepcopy(OBS[MASS])
    value, step = q.convert_to_canonical(1.2063, "lb", "muscle_mass")
    unc, unc_step = q.convert_to_canonical(0.3576, "lb", "muscle_mass")
    unc_step["operation"] = "uncertainty_unit_conversion"
    d["value"], d["uncertainty"]["value"] = value, unc
    d["provenance"]["transformation_history"] = [step, unc_step]
    assert isclose(value, 0.5472, rel_tol=1e-3)
    assert q.validate_datum(d, data) == []


def test_uncertainty_unit_must_match_datum_unit():
    d = mass()
    d["uncertainty"]["unit"] = "g"
    errors_contain(d, "uncertainty unit g differs")


# ---------------------------------------------------------------- bounds
def test_negative_mass_rejected():                     # probe 3
    errors_contain(mass(value=-5, provenance={**OBS[MASS]["provenance"], "transformation_history": []}),
                   "below the physical bound")


def test_zero_mass_rejected():
    errors_contain(mass(value=0, provenance={**OBS[MASS]["provenance"], "transformation_history": []}),
                   "below the physical bound")


def test_pennation_at_or_above_right_angle_rejected():
    d = deepcopy(OBS["LB-QD:GMAX:PENNATION:WARD2009"])
    d["value"] = pi / 2
    d["provenance"]["transformation_history"] = []
    errors_contain(d, "above the physical bound")


def test_negative_uncertainty_rejected():
    d = mass()
    d["uncertainty"]["value"] = -0.1
    errors_contain(d, "uncertainty value must be non-negative")


# ---------------------------------------------------------------- vocabularies
def test_status_typo_rejected():                       # probe 4
    errors_contain(mass(status="Populated"), "invalid status: Populated")


def test_invalid_applicability_level_rejected():      # probe 6
    d = mass()
    d["applicability"]["level"] = "individual-ish"
    errors_contain(d, "invalid applicability level")


def test_invalid_datum_kind_rejected():
    errors_contain(mass(datum_kind="guessed"), "invalid datum_kind")


def test_invalid_uncertainty_type_rejected():
    d = mass()
    d["uncertainty"]["type"] = "vibes"
    errors_contain(d, "invalid uncertainty type")


def test_invalid_evidence_domain_rejected():
    d = mass()
    d["provenance"]["source_claims"][0]["evidence_domain"] = "blog"
    errors_contain(d, "invalid evidence_domain")


def test_unpopulated_datum_may_have_null_kind():
    d = q.new_datum("maximum_isometric_force", ["LB:MUS:GLUTEUS_MAXIMUS_R"])
    assert q.validate_datum(d, data) == []


# ---------------------------------------------------------------- property definition (D5)
def test_role_mismatch_rejected():
    errors_contain(mass(property_role="state_output"), "does not match definition")


def test_value_form_not_allowed_rejected():
    errors_contain(mass(value_form="time_series"), "not allowed for muscle_mass")


def test_unknown_property_rejected():
    errors_contain(mass(property_id="muscle_charisma"), "unknown property_id")


def test_deprecated_property_name_rejected_in_data():
    d = deepcopy(OBS["LB-QD:GMAX:PENNATION:WARD2009"])
    d["property_id"] = "pennation_angle"
    errors_contain(d, "deprecated; use pennation_angle_at_optimal")


def test_property_alias_still_resolves():
    assert q.property_definition("pennation_angle")["property_id"] == "pennation_angle_at_optimal"


def test_function_of_state_forms_reconciled():
    assert "function" in q.property_definition("musculotendon_length")["allowed_value_forms"]
    assert "time_series" in q.property_definition("muscle_force")["allowed_value_forms"]


# ---------------------------------------------------------------- references (D1, D3, D8)
def test_unknown_target_rejected():                    # probe 8
    d = mass()
    d["target"]["entity_ids"] = ["LB:MUS:NOT_A_MUSCLE"]
    errors_contain(d, "does not exist in the ontology")


def test_dangling_coordinate_rejected_even_when_unpopulated():   # D1
    d = deepcopy(OBS["LB-QD:GMAX:MOMENT_ARM:R"])
    d["coordinate_context"]["coordinate_id"] = "LB:DOF:HIP_FLEXION_R"
    errors_contain(d, "coordinate_context.coordinate_id LB:DOF:HIP_FLEXION_R does not exist")


def test_right_coordinate_on_bilateral_record_rejected():        # D8
    d = deepcopy(OBS["LB-QD:GMAX:MOMENT_ARM:R"])
    d["target"]["entity_ids"] = ["LB:MUS:GLUTEUS_MAXIMUS_R", "LB:MUS:GLUTEUS_MAXIMUS_L"]
    errors_contain(d, "split the record per side")


def test_property_must_apply_to_target_class():
    d = mass()
    d["target"]["entity_ids"] = ["LB:NERVE:SCIATIC"]
    errors_contain(d, "does not apply to LB:NERVE:SCIATIC")


def test_hip_joint_receives_kinematic_properties():              # D3 / D-031
    onto = q.ontology
    assert onto.class_ancestors("SynovialBallAndSocketJoint") == ["SynovialBallAndSocketJoint", "SynovialJoint"]
    for joint in ("LB:JOINT:HIP_R", "LB:JOINT:HIP_L"):
        assert q.property_applies_to_entity("coordinate_value", joint)
        assert q.property_applies_to_entity("range_of_motion", joint)


def test_class_hierarchy_cycle_rejected(tmp_path):
    text = (ROOT / "ontology" / "hip.yaml").read_text(encoding="utf-8")
    text = text.replace("  SynovialBallAndSocketJoint: SynovialJoint\n",
                        "  SynovialBallAndSocketJoint: SynovialJoint\n  SynovialJoint: SynovialBallAndSocketJoint\n")
    path = tmp_path / "hip.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="cycle"):
        AnatomyOntology(path)


def test_split_records_have_one_side_each():
    for side in ("R", "L"):
        for prop in ("MOMENT_ARM", "MUSCULOTENDON_LENGTH"):
            d = OBS[f"LB-QD:GMAX:{prop}:{side}"]
            assert d["target"]["entity_ids"] == [f"LB:MUS:GLUTEUS_MAXIMUS_{side}"]
            assert d["coordinate_context"]["coordinate_id"] == f"LB:DOF:HIP_FLEX_EXT_{side}"


def test_old_observation_ids_resolve_through_aliases():
    assert q.resolve_observation_ids(data, "LB-QD:GMAX:MOMENT_ARM") == \
        ["LB-QD:GMAX:MOMENT_ARM:R", "LB-QD:GMAX:MOMENT_ARM:L"]
    with pytest.raises(KeyError):
        q.resolve_observation_ids(data, "LB-QD:GMAX:NEVER_EXISTED")


# ---------------------------------------------------------------- evidence (D-025)
def test_unknown_source_rejected():                    # probe 7
    d = mass()
    d["provenance"]["source_claims"][0]["source_id"] = "SRC:DOES_NOT_EXIST"
    errors_contain(d, "cites unknown source SRC:DOES_NOT_EXIST")


def test_assumed_without_rationale_rejected():        # probe 5
    d = mass(datum_kind="assumed")
    d["provenance"]["source_claims"] = []
    d["derivation"]["assumptions"] = []
    errors_contain(d, "assumed datum requires a stated rationale")


def test_assumed_with_rationale_passes():
    d = mass(datum_kind="assumed")
    d["provenance"]["source_claims"] = []
    d["derivation"]["assumptions"] = ["demonstration value; see DECISIONS.md D-0xx"]
    assert q.validate_datum(d, data) == []


def test_model_derived_requires_model_id():
    d = deepcopy(OBS["LB-QD:GMAX:FMAX:ARNOLD2010"])
    d["applicability"]["model_id"] = None
    errors_contain(d, "must identify its model")


def test_populated_requires_applicability_level():
    d = mass()
    d["applicability"]["level"] = None
    errors_contain(d, "requires an applicability level")


# ---------------------------------------------------------------- structure (D-035; found defect D9)
def test_unknown_field_rejected():
    d = mass()
    d["provenance"]["source_claims"][0]["not a fixed force value."] = None
    errors_contain(d, "Extra inputs are not permitted")


def test_muscle_force_note_no_longer_truncated():      # D9
    note = OBS["LB-QD:GMAX:MUSCLE_FORCE"]["provenance"]["source_claims"][0]["notes"]
    assert note == "Defines the computational context, not a fixed force value."


def test_wrong_type_rejected():
    errors_contain(mass(value="0.5472"), "structure: value")


# ---------------------------------------------------------------- defaults (D6)
def test_explicit_fields_win_over_common_defaults():
    common = {"applicability": {"level": "cohort", "sample_size": 18}}
    resolved = q.resolve_defaults({"applicability": {"level": "generic_model"}}, common)
    assert resolved["applicability"] == {"level": "generic_model"}       # wholesale, no merge
    assert q.resolve_defaults({}, common)["applicability"]["sample_size"] == 18


def test_ward_cohort_not_copied_to_other_records():
    for obs_id, d in OBS.items():
        if "WARD2009" not in obs_id:
            assert d["applicability"].get("sample_size") != 18, obs_id
    assert OBS["LB-QD:GMAX:FMAX:ARNOLD2010"]["applicability"]["model_id"] == "ARNOLD_2010_LOWER_LIMB"


# ---------------------------------------------------------------- D7 / D-027
def test_pcsa_difference_recorded_not_labeled_conflict():
    quality = OBS["LB-QD:GMAX:FMAX:ARNOLD2010"]["quality"]
    assert quality["conflicts_with"] == []
    comp = quality["value_comparisons"][0]
    assert comp["related_observation"] == "LB-QD:GMAX:PCSA:WARD2009"
    assert comp["relationship"] == "differs_not_reconciled"
    assert isclose(33.4 * 61, 2037.4) and "2037.4 N" in comp["downstream_effect"]


def test_invalid_comparison_relationship_rejected():
    d = deepcopy(OBS["LB-QD:GMAX:FMAX:ARNOLD2010"])
    d["quality"]["value_comparisons"][0]["relationship"] = "disagree"
    errors_contain(d, "invalid value comparison relationship")


# ---------------------------------------------------------------- D-034 anatomy, D-019 verification
def test_adductor_magnus_dual_innervation():
    onto = q.ontology
    for side in ("R", "L"):
        nerves = onto.innervation(f"LB:MUS:ADDUCTOR_MAGNUS_{side}")
        assert nerves == ["LB:NERVE:OBTURATOR", "LB:NERVE:SCIATIC_TIBIAL_PORTION"]
        assert "SRC:STATPEARLS_ADDUCTOR_MAGNUS" in onto.get(f"LB:MUS:ADDUCTOR_MAGNUS_{side}")["evidence"]


def test_ward_fiber_length_normalization_recorded():
    claim = OBS["LB-QD:GMAX:OPTIMAL_FIBER_LENGTH:WARD2009"]["provenance"]["source_claims"][0]
    assert "fiber_length_normalized_to_optimal_sarcomere_length" in claim["supports"]
