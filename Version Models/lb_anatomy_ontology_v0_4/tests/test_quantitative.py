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
