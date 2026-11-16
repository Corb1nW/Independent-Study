"""Stage D4 (D-062 with Amendment 1): the squat model stated in the ontology and assembled by generic code.

Step 1 (this part of the file): ontology and schema.
- relationship_additions across modules and the knee-edge repair (item 5; the demo review's P1);
- machine-readable coordinate conventions (item 2) and model-element names;
- target.model_entity_id (item 4, LB-QPS 0.9.0) and the regenerated datasets;
- the executable specification squat_d4 and the endpoint rule (item 1, Amendment 1, D062-B03).

Passing tests show the code does what it says; they never show the anatomy or the biomechanics is right.
"""
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from src.model_spec import SpecError, joint_endpoints, load_spec, resolve_endpoint
from src.ontology import AnatomyOntology
from src.quantitative import QuantitativeSchema
from tools import build_segment_datasets as bsd

ROOT = Path(__file__).resolve().parents[1]
HIP = ROOT / "ontology" / "hip.yaml"
LOWER = ROOT / "ontology" / "lower_limb_sagittal.yaml"
SCHEMA = ROOT / "ontology" / "quantitative_schema.yaml"
DATA = ROOT / "ontology" / "quantitative_data"
REPAIRED = ("BICEPS_FEMORIS_LONG", "SEMIMEMBRANOSUS", "SEMITENDINOSUS", "RECTUS_FEMORIS")


@pytest.fixture(scope="module")
def onto():
    return AnatomyOntology([HIP, LOWER])


@pytest.fixture(scope="module")
def schema(onto):
    return QuantitativeSchema(SCHEMA, ontology=onto)


@pytest.fixture(scope="module")
def spec(onto, schema):
    return load_spec("squat_d4", onto, schema)


def _module(tmp_path, change):
    module = yaml.safe_load(LOWER.read_text(encoding="utf-8"))
    change(module)
    path = tmp_path / "module.yaml"
    path.write_text(yaml.safe_dump(module, sort_keys=False), encoding="utf-8")
    return [HIP, path]


# ------------------------------------------------------------- relationship additions (item 5)
def test_hip_module_still_loads_alone_without_knee_edges():
    hip = AnatomyOntology(HIP)
    for base in REPAIRED:
        for side in "RL":
            rel = hip.get(f"LB:MUS:{base}_{side}")["relationships"]
            assert rel["CROSSES"] == [f"LB:JOINT:HIP_{side}"] and rel["ACTS_ON"] == [f"LB:JOINT:HIP_{side}"]
    assert hip.added_edges == []


def test_knee_edges_added_on_both_sides_with_their_evidence(onto):
    added = {(e["entity"], e["predicate"], e["target"]) for e in onto.added_edges}
    expected = {(f"LB:MUS:{b}_{s}", p, f"LB:JOINT:KNEE_{s}") for b in REPAIRED for s in "RL" for p in ("CROSSES", "ACTS_ON")}
    assert added == expected and len(onto.added_edges) == 16
    for e in onto.added_edges:
        assert e["module"] == "lower_limb_sagittal" and e["evidence"] == ["SRC:STATPEARLS_THIGH_MUSCLES"]
        assert e["basis"].startswith("StatPearls, Thigh Muscles (read 2026-11-16)")
        assert e["target"] in onto.related(e["entity"], e["predicate"])
    assert onto.edge_origin("LB:MUS:SEMITENDINOSUS_L", "CROSSES", "LB:JOINT:KNEE_L") == "lower_limb_sagittal"
    assert onto.edge_origin("LB:MUS:SEMITENDINOSUS_L", "CROSSES", "LB:JOINT:HIP_L") is None
    assert onto.edge_evidence("LB:MUS:SEMITENDINOSUS_L", "CROSSES", "LB:JOINT:HIP_L") == ["SRC:STATPEARLS_HIP"]


def test_the_edge_evidence_is_a_registered_project_source():
    text = (ROOT / "sources" / "SOURCES.md").read_text(encoding="utf-8")
    assert "SRC:STATPEARLS_THIGH_MUSCLES" in text


@pytest.mark.parametrize("change, message", [
    (lambda a: a.update({"entity": "LB:MUS:SOLEUS_R"}), "not defined in an earlier module"),
    (lambda a: a.update({"add": {"PULLS": ["LB:JOINT:KNEE_R"]}}), "unknown predicate"),
    (lambda a: a.update({"add": {"CROSSES": ["LB:JOINT:NOT_THERE"]}}), "does not exist"),
    (lambda a: a.update({"add": {"CROSSES": ["LB:JOINT:HIP_R"]}}), "already exists"),
    (lambda a: a.update({"evidence": []}), "evidence must be a non-empty list"),
    (lambda a: a.update({"evidence": ["SRC:NOT_A_SOURCE"]}), "unknown evidence source"),
    (lambda a: a.pop("evidence"), "needs entity, add and evidence"),
    (lambda a: a.update({"remove": {"CROSSES": ["LB:JOINT:HIP_R"]}}), "needs entity, add and evidence"),
])
def test_relationship_additions_are_checked(tmp_path, change, message):
    paths = _module(tmp_path, lambda m: change(m["relationship_additions"][0]))
    with pytest.raises(ValueError, match=message):
        AnatomyOntology(paths)


def test_the_primary_module_cannot_carry_additions(tmp_path):
    hip = yaml.safe_load(HIP.read_text(encoding="utf-8"))
    hip["relationship_additions"] = [{"entity": "LB:MUS:SEMITENDINOSUS_R", "add": {"ASSOCIATED_WITH": ["LB:JOINT:HIP_R"]},
                                      "evidence": ["SRC:STATPEARLS_HIP"]}]
    path = tmp_path / "hip.yaml"
    path.write_text(yaml.safe_dump(hip), encoding="utf-8")
    with pytest.raises(ValueError, match="primary module"):
        AnatomyOntology(path)


# ------------------------------------------------------------- coordinates and model elements (item 2)
def test_retained_coordinates_state_their_motions_and_model_coordinates(onto):
    expected = {"LB:DOF:ANKLE_DORSI_PLANTAR_R": ("ankle_dorsiflexion", "ankle_plantarflexion", "ankle_angle_r", 1),
                "LB:DOF:KNEE_FLEX_EXT_R": ("knee_flexion", "knee_extension", "knee_angle_r", -1),
                "LB:DOF:HIP_FLEX_EXT_R": ("hip_flexion", "hip_extension", "hip_flexion_r", 1)}
    for dof, (pos, neg, coord, sign) in expected.items():
        e = onto.get(dof)
        assert (e["positive_motion"], e["negative_motion"]) == (pos, neg)
        assert onto.model_coordinate(dof, "gait2392") == (coord, sign)
        assert onto.coordinate_for_motion(pos) == [(dof, 1)] and onto.coordinate_for_motion(neg) == [(dof, -1)]


def test_the_coordinate_signs_match_the_oracle_tool():
    """The OpenSim oracle tool's own sign table (written for D2) agrees with the new ontology fields."""
    from tools import make_d2_oracle as mo
    onto = AnatomyOntology([HIP, LOWER])
    dof = {"ankle": "LB:DOF:ANKLE_DORSI_PLANTAR_R", "knee": "LB:DOF:KNEE_FLEX_EXT_R", "hip": "LB:DOF:HIP_FLEX_EXT_R"}
    for k, d in dof.items():
        assert onto.model_coordinate(d, "gait2392") == (mo.COORDS[k], int(mo.SIGN[k]))


@pytest.mark.parametrize("change, message", [
    (lambda e: e.update({"model_coordinates": [{"model": "gait2392", "coordinate": "knee_angle_r", "sign": 2}]}), "sign"),
    (lambda e: e.update({"negative_motion": e["positive_motion"]}), "two different names"),
    (lambda e: e.pop("model_coordinates"), "non-empty list"),
])
def test_coordinate_fields_are_checked(tmp_path, change, message):
    paths = _module(tmp_path, lambda m: change(m["entities"]["LB:DOF:KNEE_FLEX_EXT_R"]))
    with pytest.raises(ValueError, match=message):
        AnatomyOntology(paths)


def test_coordinate_fields_only_on_coordinates(tmp_path):
    paths = _module(tmp_path, lambda m: m["entities"]["LB:SEG:SHANK_R"].update({"positive_motion": "x", "negative_motion": "y"}))
    with pytest.raises(ValueError, match="only to a JointCoordinate"):
        AnatomyOntology(paths)


def test_model_elements_are_unique(tmp_path):
    def dup(m):
        m["entities"]["LB:FRAME:GAIT2392_TORSO"]["model_element"] = {"model": "gait2392", "name": "pelvis"}
    with pytest.raises(ValueError, match="also named by"):
        AnatomyOntology(_module(tmp_path, dup))


# ---------------------------------------------------------------- schema and datasets (item 4)
def test_schema_version_and_field(schema):
    assert schema.data["schema"]["version"] == "0.9.0"
    assert schema.data["model_entity_classes"] == ["CoordinateFrame", "ModelJoint", "ModelActuator"]
    assert "model_entity_id" in schema.template["target"]


def _a_record(schema, name, oid):
    d = schema.load_dataset(DATA / name)
    return d, deepcopy(d["observations"][oid])


def test_model_entity_id_is_validated(schema):
    d, rec = _a_record(schema, "muscles_gait2392.yaml", "LB-QD:G2392:MUS:SOLEUS_R:OPTIMAL_FIBER_LENGTH")
    assert rec["target"]["model_entity_id"] == "LB:ACT:G2392:SOLEUS_R"
    assert schema.validate_datum(rec, d) == []
    rec["target"]["model_entity_id"] = "LB:ACT:G2392:NOT_THERE"
    assert any("model_entity_id LB:ACT:G2392:NOT_THERE does not exist" in e for e in schema.validate_datum(rec, d))
    rec["target"]["model_entity_id"] = "LB:MUS:SOLEUS_R"
    assert any("allowed: CoordinateFrame, ModelJoint, ModelActuator" in e for e in schema.validate_datum(rec, d))
    del rec["target"]["model_entity_id"]
    assert schema.validate_datum(rec, d) == []      # optional


def test_regenerated_datasets_are_current():
    for name, builder in bsd.DATASETS.items():
        assert (DATA / name).read_text(encoding="utf-8") == bsd.render(builder), name


def test_dataset_records_name_their_model_element(onto, schema):
    muscles = schema.load_dataset(DATA / "muscles_gait2392.yaml")["observations"]
    for oid, o in muscles.items():
        actuator = o["target"]["model_entity_id"]
        assert onto.get(actuator)["class"] == "ModelActuator"
        assert f"({actuator})" in o["target"]["computational_representation"]
        assert oid.split(":")[3] == onto.model_element(actuator)[1].upper()
    segs = schema.load_dataset(DATA / "segments_gait2392.yaml")["observations"]
    with_frame = {oid: o for oid, o in segs.items() if o["target"].get("model_entity_id")}
    assert len(with_frame) == 22   # 7 bodies x (mass, centre of mass, inertia) + the model joint 'back'
    for oid, o in with_frame.items():
        assert onto.get(o["target"]["model_entity_id"])["class"] in ("CoordinateFrame", "ModelJoint")


def test_generator_reads_its_actuator_list_from_the_ontology(onto):
    names = list(bsd.model_actuators())
    assert names == [onto.model_element(a)[1] for a in onto.data["models"]["squat_d2"]["represents"]]
    assert not hasattr(bsd, "D2_ACTUATORS")


def test_path_point_coordinate_text_agrees_with_the_coordinate_fields(onto):
    muscles = yaml.safe_load((DATA / "muscles_gait2392.yaml").read_text(encoding="utf-8"))["observations"]
    checked = 0
    for o in muscles.values():
        if o["value_form"] != "function":
            continue
        dof = o["coordinate_context"]["coordinate_id"]
        coord, sign = onto.model_coordinate(dof, "gait2392")
        text = o["value"]["coordinate"]
        assert text.startswith(f"Gait2392 {coord} ") and text.endswith(("-" if sign < 0 else "") + dof)
        checked += 1
    assert checked > 0


# ------------------------------------------------------------------ the specification (item 1)
def test_specification_structure_is_derived(spec):
    assert spec.segments == ["LB:SEG:FOOT_R", "LB:SEG:SHANK_R", "LB:SEG:THIGH_R", "LB:SEG:HAT"]
    assert [t[0] for t in spec.tree] == ["LB:JOINT:ANKLE_R", "LB:JOINT:KNEE_R", "LB:JOINT:HIP_R"]
    assert spec.parts["LB:SEG:HAT"] == ["LB:SEG:HAT", "LB:SEG:PELVIS", "LB:SEG:TORSO"]
    assert spec.frames["LB:SEG:FOOT_R"] == ["LB:FRAME:GAIT2392_TALUS_R", "LB:FRAME:GAIT2392_CALCN_R",
                                           "LB:FRAME:GAIT2392_TOES_R"]
    assert spec.frames["LB:SEG:HAT"] == ["LB:FRAME:GAIT2392_PELVIS", "LB:FRAME:GAIT2392_TORSO"]
    assert spec.coordinates == ["LB:DOF:ANKLE_DORSI_PLANTAR_R", "LB:DOF:KNEE_FLEX_EXT_R", "LB:DOF:HIP_FLEX_EXT_R"]
    assert len(spec.actuators) == 14 and spec.variants == ["moving_knee", "fixed_knee"]


def test_endpoint_rule_resolves_every_joint(onto, spec):
    """D062-B03: hip through the bony pelvis; knee and ankle directly; subtalar inside the foot; low back to pelvis
    and torso; the lumped MTP has no stated endpoints."""
    assert resolve_endpoint(onto, "LB:BONE:HIP_BONE_R") == "LB:SEG:PELVIS"
    assert resolve_endpoint(onto, "LB:BONE:HIP_BONE_L") == "LB:SEG:PELVIS"
    assert joint_endpoints(onto, "LB:JOINT:HIP_R") == ("LB:SEG:PELVIS", "LB:SEG:THIGH_R")
    assert joint_endpoints(onto, "LB:JOINT:KNEE_R") == ("LB:SEG:THIGH_R", "LB:SEG:SHANK_R")
    assert joint_endpoints(onto, "LB:JOINT:ANKLE_R") == ("LB:SEG:SHANK_R", "LB:SEG:FOOT_R")
    assert joint_endpoints(onto, "LB:JOINT:SUBTALAR_R") == ("LB:SEG:FOOT_R", "LB:SEG:FOOT_R")
    assert joint_endpoints(onto, "LB:JOINT:LUMBAR_GAIT2392") == ("LB:SEG:PELVIS", "LB:SEG:TORSO")
    assert joint_endpoints(onto, "LB:JOINT:MTP_R") is None
    assert spec.joints["LB:JOINT:HIP_R"].segments == ("LB:SEG:HAT", "LB:SEG:THIGH_R")
    log = {e["joint"]: e for e in spec.endpoint_log}
    assert log["LB:JOINT:MTP_R"]["note"] == "merged; endpoints not stated in the ontology"


def test_unrepresented_hip_bone_stops_the_assembly(schema):
    """Amendment 1, A5: with REPRESENTED_BY removed from the bony pelvis, assembly stops naming the hip bone."""
    onto = AnatomyOntology([HIP, LOWER])
    onto.entities["LB:BONE:PELVIS"]["relationships"].pop("REPRESENTED_BY")
    with pytest.raises(SpecError, match="LB:BONE:HIP_BONE_R is unresolved"):
        load_spec("squat_d4", onto, schema)


def test_a_second_represented_complex_is_ambiguous(schema):
    """Amendment 1, A5: a second represented complex containing the hip bone stops the assembly as ambiguous."""
    onto = AnatomyOntology([HIP, LOWER])
    onto.entities["LB:BONE:PELVIS_COPY"] = {"name": "copy", "class": "SkeletalComplex",
                                            "relationships": {"HAS_PART": ["LB:BONE:HIP_BONE_R"],
                                                              "REPRESENTED_BY": ["LB:SEG:HAT"]}}
    with pytest.raises(SpecError, match="LB:BONE:HIP_BONE_R is ambiguous"):
        load_spec("squat_d4", onto, schema)


def _spec_with(change):
    onto = AnatomyOntology([HIP, LOWER])
    change(onto.data["models"]["squat_d4"])
    return onto


@pytest.mark.parametrize("change, message", [
    (lambda s: s["segments"].remove("LB:SEG:HAT"), "not a model segment|not in the model"),
    (lambda s: s["bodies"]["female"]["segment_rules"].pop("LB:SEG:HAT"), "body female: rules"),
    (lambda s: s["bodies"]["male"]["segment_rules"]["LB:SEG:FOOT_R"].update({"rule": "direct"}), "direct needs one frame"),
    (lambda s: s["bodies"]["female"]["segment_rules"]["LB:SEG:THIGH_R"].update(
        {"center_of_mass_fraction": "LB-QD:DELEVA:F:NOPE"}), "found in 0 datasets"),
    (lambda s: s["modelled_joints"]["LB:JOINT:KNEE_R"]["location"].update({"bent": "LB-QD:G2392:JOINT:KNEE_R"}),
     "are not declared"),
    (lambda s: s["retained_coordinates"].pop(), "must be exactly the modelled joints"),
    (lambda s: s["actuators"].append("LB:MUS:SOLEUS_R"), "has class SkeletalMuscle"),
    (lambda s: s["ground"].update({"segment": "LB:SEG:SHANK_R"}), "ground reference frame"),
    (lambda s: s["merged_joints"]["LB:JOINT:SUBTALAR_R"].update({"into": "LB:SEG:SHANK_R"}), "merged into both"),
    (lambda s: s["bodies"]["gait2392"].update({"geometry_scale": "stature_ratio_to_reference"}), "exactly one body"),
])
def test_specification_errors_are_reported(schema, change, message):
    with pytest.raises(SpecError, match=message):
        load_spec("squat_d4", _spec_with(change), schema)


def test_an_extension_may_only_add_actuators(schema):
    def ext(models):
        models["squat_d4_ext"] = {"kind": "executable_specification", "extends": "squat_d4",
                                  "add_actuators": ["LB:ACT:G2392:SOLEUS_R"]}
    onto = AnatomyOntology([HIP, LOWER])
    ext(onto.data["models"])
    with pytest.raises(SpecError, match="already in squat_d4"):
        load_spec("squat_d4_ext", onto, schema)
    onto.data["models"]["squat_d4_ext"] = {"kind": "executable_specification", "extends": "squat_d4", "segments": []}
    with pytest.raises(SpecError, match="may only add actuators"):
        load_spec("squat_d4_ext", onto, schema)
