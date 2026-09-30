from pathlib import Path
from src.quantitative import QuantitativeSchema

ROOT = Path(__file__).parents[1]
q = QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")

def test_muscle_schema_contains_core_hill_parameters():
    props = q.properties_for_entity_class("SkeletalMuscle")["musculotendon"]
    for key in ["maximum_isometric_force", "optimal_fiber_length", "tendon_slack_length", "pennation_angle_at_optimal"]:
        assert key in props

def test_blank_datum_is_not_faked():
    d = q.new_datum("maximum_isometric_force")
    assert d["value"] is None
    assert d["status"] == "unpopulated"

def test_populated_literature_value_requires_source_claim():
    d = q.new_datum("maximum_isometric_force")
    d["value"] = 1.0
    d["datum_kind"] = "literature_derived"
    d["status"] = "populated"
    assert "populated non-assumed datum requires source_claims" in q.validate_datum(d)

def test_coordinate_dependent_property_requires_context():
    d = q.new_datum("moment_arm")
    d["value"] = {"representation": "function"}
    d["datum_kind"] = "model_derived"
    d["status"] = "populated"
    d["provenance"]["source_claims"] = [{"source_id": "EXAMPLE", "supports": ["value"]}]
    assert any("coordinate-dependent" in e for e in q.validate_datum(d))

def test_gluteus_maximus_evidence_datum_passes():
    dataset = q.load_dataset(ROOT / "ontology" / "quantitative_data" / "gluteus_maximus.yaml")
    d = dataset["observations"]["LB-QD:GMAX:OPTIMAL_FIBER_LENGTH:WARD2009"]
    assert q.validate_datum(d) == []
    assert d["value"] == 0.1569
    assert d["applicability"]["sample_size"] == 18
    assert len(d["provenance"]["source_claims"]) == 2

def test_populated_datum_requires_target_entity():
    d = q.new_datum("maximum_isometric_force")
    d["value"] = 100.0
    d["datum_kind"] = "literature_derived"
    d["status"] = "populated"
    d["provenance"]["source_claims"] = [{"source_id": "EXAMPLE", "supports": ["value"]}]
    assert "populated datum requires at least one target entity_id" in q.validate_datum(d)

def _gmax_dataset():
    return q.load_dataset(ROOT / "ontology" / "quantitative_data" / "gluteus_maximus.yaml")

def _mat(obs, data):
    from copy import deepcopy
    d=deepcopy(obs)
    for key in ["target", "symmetry_policy", "applicability", "quality"]:
        d.setdefault(key, deepcopy(data["common"][key]))
    d.setdefault("coordinate_context", {"frame_id": None, "coordinate_id": None})
    return d

def test_property_roles_distinguish_parameter_function_and_output():
    assert q.property_definition("optimal_fiber_length")["property_role"] == "parameter"
    assert q.property_definition("moment_arm")["property_role"] == "function_of_state"
    assert q.property_definition("muscle_force")["property_role"] == "state_output"

def test_gluteus_shared_baseline_is_explicit_and_overridable():
    data=_gmax_dataset()
    policy=data["dataset"]["bilateral_policy"]
    assert policy["assumption"] == "symmetric_baseline"
    assert policy["anatomical_fact"] is False
    assert policy["independent_override_supported"] is True
    assert set(policy["shared_baseline_targets"]) == {"LB:MUS:GLUTEUS_MAXIMUS_R", "LB:MUS:GLUTEUS_MAXIMUS_L"}

def test_direct_architecture_values_present():
    data=_gmax_dataset(); obs=data["observations"]
    assert obs["LB-QD:GMAX:MASS:WARD2009"]["value"] == 0.5472
    assert obs["LB-QD:GMAX:MUSCLE_LENGTH:WARD2009"]["value"] == 0.2695
    assert obs["LB-QD:GMAX:PCSA:WARD2009"]["value"] == 0.00334
    assert obs["LB-QD:GMAX:OPTIMAL_FIBER_LENGTH:WARD2009"]["value"] == 0.1569

def test_fmax_preserves_derivation_and_specific_tension_assumption():
    data=_gmax_dataset(); d=data["observations"]["LB-QD:GMAX:FMAX:ARNOLD2010"]
    assert d["datum_kind"] == "model_derived"
    assert d["value"] == 1852.6
    assert d["derivation"]["formula"] == "Fmax = PCSA * specific_tension"
    assert any(i.get("name") == "specific_tension" and i.get("value") == 61.0 for i in d["derivation"]["inputs"])

def test_unresolved_model_specific_values_are_not_faked():
    data=_gmax_dataset(); obs=data["observations"]
    for key in ["LB-QD:GMAX:TENDON_SLACK_LENGTH:ARNOLD2010", "LB-QD:GMAX:MAX_CONTRACTION_VELOCITY", "LB-QD:GMAX:ACTIVATION_TIME_CONSTANT", "LB-QD:GMAX:DEACTIVATION_TIME_CONSTANT"]:
        assert obs[key]["value"] is None
        assert obs[key]["status"] != "populated"

def test_state_dependent_quantities_are_not_scalar_constants():
    data=_gmax_dataset(); obs=data["observations"]
    assert obs["LB-QD:GMAX:MOMENT_ARM"]["property_role"] == "function_of_state"
    assert obs["LB-QD:GMAX:MUSCULOTENDON_LENGTH"]["property_role"] == "function_of_state"
    assert obs["LB-QD:GMAX:MUSCLE_FORCE"]["property_role"] == "state_output"
    assert obs["LB-QD:GMAX:MOMENT_ARM"]["value"] is None

def test_all_fixed_populated_gmax_records_validate():
    data=_gmax_dataset()
    for raw in data["observations"].values():
        d=_mat(raw,data)
        if d.get("status") == "populated":
            assert q.validate_datum(d) == []
