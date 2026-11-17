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
    assert onto.edge_evidence("LB:MUS:SEMITENDINOSUS_L", "CROSSES", "LB:JOINT:HIP_L") == \
        ["SRC:STATPEARLS_HIP", "SRC:STATPEARLS_THIGH_MUSCLES"]          # the entity's evidence (Amendment 3)


def test_the_four_muscles_cite_the_thigh_muscles_chapter_in_hip_module_alone():
    """D-062 Amendment 3 (Q71): the chapter that supports the knee edges is also part of the eight entities' evidence,
    registered once, in hip.yaml, which still loads on its own."""
    hip = AnatomyOntology(HIP)
    assert "SRC:STATPEARLS_THIGH_MUSCLES" in hip.sources
    for base in REPAIRED:
        for side in "RL":
            assert hip.get(f"LB:MUS:{base}_{side}")["evidence"] == ["SRC:STATPEARLS_HIP", "SRC:STATPEARLS_THIGH_MUSCLES"]
    lower = yaml.safe_load(LOWER.read_text(encoding="utf-8"))
    assert "SRC:STATPEARLS_THIGH_MUSCLES" not in lower["sources"]


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
    """The dataset covers every actuator any model view or specification names, in order of first appearance."""
    expected = []
    for spec in onto.data["models"].values():
        for a in list(spec.get("represents") or []) + list(spec.get("actuators") or []) + list(spec.get("add_actuators") or []):
            if onto.get(a).get("class") == "ModelActuator" and onto.model_element(a)[1] not in expected:
                expected.append(onto.model_element(a)[1])
    names = list(bsd.model_actuators())
    assert names == expected
    assert names[:14] == [onto.model_element(a)[1] for a in onto.data["models"]["squat_d2"]["represents"]]
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


# =============================================================================================================
# Step 2: the generic assembler, dynamics and muscle geometry (items 3 and 6), criteria A1 and A3.
# Regression oracles: src/squat_d1.py (fixed knee), src/squat_d3.py (moving knee; frozen = D1), src/muscles_d2.py.
# =============================================================================================================
import dataclasses  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402

import numpy as np  # noqa: E402

from src import model_assembly as ma  # noqa: E402
from src import muscle_paths as mp  # noqa: E402
from src import muscles_d2 as m2  # noqa: E402
from src import squat_d1 as sq  # noqa: E402
from src import squat_d3 as d3  # noqa: E402
from tools import run_phase_d2 as d2r  # noqa: E402
from tools.oracle_coverage import check_reference  # noqa: E402

D1_CFG, D1P = sq.load_config(ROOT / "config" / "phase_d1_squat.yaml")
_, D2P = d2r.load_config()
D3_TOL = yaml.safe_load((ROOT / "config" / "phase_d3_moving_knee.yaml").read_text(encoding="utf-8"))["tolerances"]
CASES = [(b, v) for b in ("female", "male", "gait2392") for v in ("fixed_knee", "moving_knee")]
# A1 tolerances, stated in D-062 before the build.
A1 = {"tau": 1e-9, "length": 1e-12, "arm": 1e-12, "t_star": 1e-7, "activation": 1e-6}
SEG = {"foot": "LB:SEG:FOOT_R", "shank": "LB:SEG:SHANK_R", "thigh": "LB:SEG:THIGH_R", "hat": "LB:SEG:HAT"}


def _motion():
    t = np.linspace(0, D1P["period"], int(D1P["samples"]))
    return sq.Motion(D1P["start_angles"], D1P["depth_angles"], D1P["period"])(t)


@pytest.fixture(scope="module")
def assembled(spec):
    return {(b, v): ma.assemble(spec, b, v) for b, v in CASES}


@pytest.fixture(scope="module")
def oracles(schema):
    """The D1-D3 modules for each case (the regression oracles, D-062 item 6)."""
    out = {}
    for b, v in CASES:
        body = d3.build_body(b, QuantitativeSchema(SCHEMA), frozen=(v == "fixed_knee"))
        s = d2r.body_scale(body.base)
        acts, _ = m2.load_actuators(s, QuantitativeSchema(SCHEMA))
        joints = m2.d1_joints(s, QuantitativeSchema(SCHEMA))
        if v == "moving_knee":
            joints = dataclasses.replace(joints, moving_knee=body.knee)
        out[(b, v)] = (body, acts, joints)
    return out


def test_derived_angle_map_equals_d1(assembled):
    for m in assembled.values():
        assert np.array_equal(m.B[1:], sq.B_MAP)
        assert m.B[0].tolist() == [0.0, 0.0, 0.0]          # the ground segment does not turn


@pytest.mark.parametrize("body,variant", CASES)
def test_a1_body_parameters_and_scale(assembled, oracles, body, variant):
    m, (b, _, _) = assembled[(body, variant)], oracles[(body, variant)]
    assert m.scale == d2r.body_scale(b.base)
    assert (m.body_mass, m.stature) == (b.base.body_mass, b.base.stature)
    for key, sid in (("shank", SEG["shank"]), ("thigh", SEG["thigh"]), ("hat", SEG["hat"])):
        old, new = b.base.segments[key], m.segments[sid]
        assert new.mass == pytest.approx(old.mass, rel=1e-14) and new.inertia == pytest.approx(old.inertia, rel=1e-12)
    assert m.segments[SEG["foot"]].mass == pytest.approx(b.base.foot.mass, rel=1e-14)
    assert np.allclose(m.segments[SEG["foot"]].com, b.base.foot.com, atol=1e-15)
    assert np.allclose(m.contact["heel"][:2], b.base.foot.heel, atol=1e-15)
    assert np.allclose(m.contact["ball"][:2], b.base.foot.ball, atol=1e-15)
    assert m.ground_y == pytest.approx(b.base.foot.ground_y, abs=1e-15)
    assert 2 * m.per_side_mass() / m.body_mass - 1 == pytest.approx(2 * b.base.per_leg_mass() / b.base.body_mass - 1,
                                                                      abs=1e-14)


@pytest.mark.parametrize("body,variant", CASES)
def test_a1_kinematics_and_torques_regress_to_d1_d3(assembled, oracles, body, variant):
    m, (b, _, _) = assembled[(body, variant)], oracles[(body, variant)]
    q, qd, qdd = _motion()
    g = D1P["gravity"]
    old, new = d3.inverse_dynamics(b, q, qd, qdd, g), ma.inverse_dynamics(m, q, qd, qdd, g)
    assert np.max(np.abs(old["tau"] - new["tau"])) < A1["tau"]
    if variant == "fixed_knee":     # D3 frozen reproduces D1; check against D1 itself as well
        assert np.max(np.abs(sq.inverse_dynamics(b.base, q, qd, qdd, g)["tau"] - new["tau"])) < A1["tau"]
    assert np.max(np.abs(old["grf"] - new["grf"])) < 1e-9
    assert np.nanmax(np.abs(old["cop_x"] - new["cop_x"])) < 1e-12
    ko, kn = old["kinematics"], new["kinematics"]
    pairs = [(ko["knee"], kn[SEG["thigh"]]["joint"]), (ko["hip"], kn[SEG["hat"]]["joint"])]
    for o, s in (("com_shank", "shank"), ("com_thigh", "thigh"), ("com_hat", "hat")):
        pairs += [(ko[o][0], kn[SEG[s]]["c"]), (ko[o][2], kn[SEG[s]]["ac"])]
    for a, c in pairs:
        assert np.max(np.abs((a[0] if isinstance(a, tuple) else a) - c)) < 1e-12
    if variant == "moving_knee":
        assert np.max(np.abs(old["knee_translation_term"] - new["moving_centre_terms"]["LB:JOINT:KNEE_R"])) < 1e-9
    else:
        assert not np.any(new["moving_centre_terms"]["LB:JOINT:KNEE_R"])


@pytest.mark.parametrize("body,variant", CASES)
def test_a1_muscle_geometry_regresses_to_d2_d3(assembled, oracles, body, variant):
    m, (_, acts, joints) = assembled[(body, variant)], oracles[(body, variant)]
    assert [a.name for a in acts] == [a.name for a in m.actuators]
    for a, b in zip(acts, m.actuators):
        assert (a.f0, a.l_opt, a.l_ts, a.alpha0, a.v_max, a.entity) == (b.f0, b.l_opt, b.l_ts, b.alpha0, b.v_max, b.entity)
    q, _, _ = _motion()
    worst_l = worst_r = 0.0
    for i in range(q.shape[1]):
        frames = ma.segment_frames(m, q[:, i])
        for a, b in zip(acts, m.actuators):
            L0, R0, p0 = m2.path(a, q[:, i], joints)
            L1, R1, p1 = mp.path(m, b, q[:, i], frames)
            assert len(p0) == len(p1)
            worst_l, worst_r = max(worst_l, abs(L0 - L1)), max(worst_r, float(np.max(np.abs(R0 - R1))))
    assert worst_l < A1["length"] and worst_r < A1["arm"]


@pytest.mark.parametrize("body,variant", CASES)
def test_a1_recruitment_regresses_to_d2_d3(assembled, oracles, body, variant):
    m, (b, acts, joints) = assembled[(body, variant)], oracles[(body, variant)]
    q, qd, qdd = _motion()
    g, delta = D1P["gravity"], D2P["solver_band_delta"]
    tau_old = d3.inverse_dynamics(b, q, qd, qdd, g)["tau"]
    new = mp.recruit_series(m, q, qd, ma.inverse_dynamics(m, q, qd, qdd, g)["tau"], delta, second_solver=False,
                            needed_reserve=False)
    t_old = np.zeros(q.shape[1])
    for i in range(q.shape[1]):
        Cm = np.zeros((3, len(acts)))
        for j, a in enumerate(acts):
            L, R, _ = m2.path(a, q[:, i], joints)
            Cm[:, j] = m2.unit_tendon_force(a, m2.fiber_state(a, L, -R @ qd[:, i])) * R
        rec = m2.recruit(Cm, tau_old[:, i], delta=delta, second_solver=False)
        t_old[i] = rec.t_star
        assert np.max(np.abs(rec.activation - new["activation"][:, i])) < A1["activation"]
    assert np.max(np.abs(t_old - new["t_star"])) < A1["t_star"]
    eps = D2P["epsilon_reserve"]
    assert (np.max(t_old) <= eps) == (np.max(new["t_star"]) <= eps)          # identical muscle-feasibility status
    assert not new["flags"]


@pytest.mark.parametrize("body,variant", CASES)
def test_a3_mechanics_checks_on_the_assembled_model(assembled, oracles, body, variant):
    m, (b, _, _) = assembled[(body, variant)], oracles[(body, variant)]
    res = ma.run(m, D1P)
    checks = ma.check_residuals(m, D1P, res)
    for key in ("newton_euler_vs_kane_N_m", "static_virtual_work_N_m", "energy_W", "local_one_step_rad_at_1ms",
                "short_horizon_0p1s_rad_at_1ms"):
        assert abs(checks[key]) <= D3_TOL[key], key
    assert checks["newton_identity_per_side_N"] <= D3_TOL["newton_identity_N"]
    assert abs(checks["mass_bookkeeping_relative"]) <= D3_TOL["mass_fraction_sum"]
    old = d3.run(b, D1P)
    assert res["contact"]["feasible"] == old["contact"]["feasible"]          # identical contact status
    assert res["contact"]["cop_min_m"] == pytest.approx(old["contact"]["cop_min_m"], abs=1e-12)


@pytest.mark.parametrize("variant,path,mode", [("fixed_knee", "tests/data/d2_oracle_reference.json", "fixed"),
                                               ("moving_knee", "tests/data/d3_oracle_reference.json", "moving")])
def test_a3_assembled_geometry_matches_opensim(assembled, variant, path, mode):
    ref = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert check_reference(ref, mode) == []
    m = assembled[("gait2392", variant)]
    by_name = {a.name: a for a in m.actuators}
    assert set(ref["actuators"]) <= set(by_name)
    for g in ref["geometry"]:
        q = np.array(g["q"])
        frames = ma.segment_frames(m, q)
        for name in ref["actuators"]:
            L, R, _ = mp.path(m, by_name[name], q, frames)
            assert abs(L - g["length_m"][name]) < 1e-9, (name, g["kind"])
            assert np.max(np.abs(R - np.array(g["moment_arm_m"][name]))) < 1e-9, (name, g["kind"])


def test_a3_assembled_kinematics_match_opensim(assembled):
    ref = json.loads((ROOT / "tests" / "data" / "d3_oracle_reference.json").read_text(encoding="utf-8"))
    m = assembled[("gait2392", "moving_knee")]
    zero = np.zeros((3, 1))
    for row in ref["kinematics"]:
        q = np.array(row["q"])[:, None]
        k = ma.kinematics(m, q, zero, zero)
        mine = {"knee_m": k[SEG["shank"]]["o"], "hip_m": k[SEG["thigh"]]["o"], "pelvis_origin_m": k[SEG["hat"]]["o"],
                "femur_com_m": k[SEG["thigh"]]["c"], "tibia_com_m": k[SEG["shank"]]["c"]}
        for key, v in mine.items():
            assert np.max(np.abs(v[:, 0] - np.array(row[key][:2]))) < D3_TOL["kinematics_oracle_m"], key


def test_moving_centre_derivatives_by_differences(assembled):
    """The moving joint centre's first and second derivatives agree with central differences of its value."""
    m = assembled[("male", "moving_knee")]
    ib = m.segments[SEG["thigh"]].inbound
    assert ib.moving
    h = 1e-5
    for qk in (0.1, 0.7, 1.3):
        v, d, dd = ib.outer_point(qk)
        vp, vm = ib.outer_point(qk + h)[0], ib.outer_point(qk - h)[0]
        assert np.max(np.abs((vp - vm) / (2 * h) - d)) < 1e-9
        assert np.max(np.abs((vp - 2 * v + vm) / h ** 2 - dd)) < 1e-4


# ----------------------------------------------------------------------------- A6: no anatomy in the code
ANATOMY_TERMS = ("knee", "hip", "ankle", "foot", "feet", "heel", "toe", "toes", "leg", "legs", "thigh", "shank",
                 "pelvis", "pelvic", "torso", "trunk", "femur", "femoral", "tibia", "tibial", "talus", "calcaneus",
                 "calcn", "lumbar", "gluteus", "glut", "vastus", "gastrocnemius", "soleus", "hamstring",
                 "hamstrings", "quadriceps", "iliacus", "psoas", "iliopsoas", "rectus", "biceps", "semimembranosus",
                 "semitendinosus", "subtalar", "metatarsophalangeal", "mtp", "hat", "forearm", "hand", "head",
                 "sagittal", "flexion", "extension", "dorsiflexion", "plantarflexion")
NEW_MODULES = ("src/model_spec.py", "src/model_assembly.py", "src/muscle_paths.py", "src/consistency.py",
               "tools/run_phase_d4.py")


@pytest.mark.parametrize("path", NEW_MODULES)
def test_a6_no_anatomy_or_ontology_ids_in_the_new_modules(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    assert not re.search(r"\bLB(:|-QD)", text), "ontology or dataset ID in code"
    words = set(re.findall(r"[a-z]+", text.lower()))
    assert not words & set(ANATOMY_TERMS), sorted(words & set(ANATOMY_TERMS))


def test_a6_scan_would_catch_a_planted_term(tmp_path):
    text = (ROOT / NEW_MODULES[1]).read_text(encoding="utf-8") + "\n# knee\n"
    assert set(re.findall(r"[a-z]+", text.lower())) & set(ANATOMY_TERMS) == {"knee"}


# =============================================================================================================
# Step 3: the consistency checks C1-C5, required edges and mirror (item 7, Amendment 1), criteria A4 and A5.
# =============================================================================================================
from src import consistency as cs  # noqa: E402

FIXED_REF = ROOT / "tests" / "data" / "d2_oracle_reference.json"
BFL = ("LB:MUS:BICEPS_FEMORIS_LONG_R", "LB:MUS:BICEPS_FEMORIS_LONG_L")


def _reference_arms(path=FIXED_REF, change=None):
    ref = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = sorted((g for g in ref["geometry"] if g["kind"] == "d1_sample"), key=lambda g: g["index"])
    arms = {n: np.array([g["moment_arm_m"][n] for g in rows]).T for n in ref["actuators"]}
    if change:
        change(arms)
    return arms


@pytest.fixture(scope="module")
def arm_series(assembled):
    q, _, _ = _motion()
    return {case: mp.moment_arm_series(m, q) for case, m in assembled.items()}


def _checks(onto, schema, arm_series, references="default", extra_actuator=None):
    spec = load_spec("squat_d4", onto, schema)
    models = [ma.assemble(spec, "gait2392", "moving_knee")]
    if references == "default":
        references = {"fixed_knee": _reference_arms()}
    return cs.run_checks(spec, models, arm_series, references)


def _onto(change=None, repaired=True, tmp_path=None):
    if repaired:
        onto = AnatomyOntology([HIP, LOWER])
    else:
        module = yaml.safe_load(LOWER.read_text(encoding="utf-8"))
        module.pop("relationship_additions")
        path = tmp_path / "unrepaired.yaml"
        path.write_text(yaml.safe_dump(module, sort_keys=False), encoding="utf-8")
        onto = AnatomyOntology([HIP, path])
    if change:
        change(onto)
    return onto


def _drop(onto, eid, pred, target):
    onto.entities[eid]["relationships"][pred].remove(target)


def test_a4_all_checks_pass_on_the_repaired_ontology(onto, schema, arm_series):
    r = _checks(onto, schema, arm_series)
    assert r["passed"]
    for key in ("C1_crossings", "C2_leverage", "C3_actions", "C4_evidence", "required_edges", "mirror"):
        assert r[key]["passed"], key


def test_a4_on_the_unrepaired_ontology(schema, arm_series, tmp_path):
    """C1 flags exactly the four right-side muscles; the required-edge check flags their knee CROSSES and ACTS_ON on
    both sides (eight entities, no others); the mirror check passes, as expected for a symmetric omission."""
    onto = _onto(repaired=False, tmp_path=tmp_path)
    r = _checks(onto, QuantitativeSchema(SCHEMA, ontology=onto), arm_series)
    flagged = {f["muscle"]: f["missing_CROSSES"] for f in r["C1_crossings"]["failures"]}
    assert flagged == {f"LB:MUS:{b}_R": ["LB:JOINT:KNEE_R"] for b in REPAIRED}
    missing = {(m["entity"], m["predicate"], m["target"]) for m in r["required_edges"]["missing"]}
    assert missing == {(f"LB:MUS:{b}_{s}", p, f"LB:JOINT:KNEE_{s}") for b in REPAIRED for s in "RL"
                       for p in ("CROSSES", "ACTS_ON")}
    assert r["mirror"]["passed"]


def test_a5_deleting_a_crossing_fails_c1_naming_the_muscle(schema, arm_series):
    onto = _onto(lambda o: _drop(o, BFL[0], "CROSSES", "LB:JOINT:KNEE_R"))
    r = _checks(onto, schema, arm_series)
    assert [f["muscle"] for f in r["C1_crossings"]["failures"]] == [BFL[0]]
    assert not r["passed"]


def test_a5_deleting_an_action_fails_c3(schema, arm_series):
    onto = _onto(lambda o: _drop(o, BFL[0], "ACTS_ON", "LB:JOINT:KNEE_R"))
    r = _checks(onto, schema, arm_series)
    assert r["C1_crossings"]["passed"] and not r["C3_actions"]["passed"]
    assert {"muscle": BFL[0], "capability": "knee_flexion", "joint_missing_from_ACTS_ON": "LB:JOINT:KNEE_R"} in \
        r["C3_actions"]["structural_failures"]


def test_a5_swapping_a_capability_fails_the_direction_check(schema, arm_series):
    def swap(o):
        caps = o.entities[BFL[0]]["mechanical_capabilities"]
        caps[caps.index("knee_flexion")] = "knee_extension"
    r = _checks(_onto(swap), schema, arm_series)
    fails = r["C3_actions"]["direction_failures"]
    moving = [f for f in fails if f["case"][1] == "moving_knee"]
    assert {tuple(f["case"]) for f in moving} == {(b, "moving_knee") for b in ("female", "male", "gait2392")}
    assert all(d["actuator"] == "LB:ACT:G2392:BIFEMLH_R" and d["drives"] == "knee_flexion"
               for f in moving for d in f["direction_disagreements"])


def test_a5_a_path_through_a_joint_centre_crosses_with_negligible_leverage(spec):
    """ChatGPT's counterexample (D061-B01): anchors on two segments at ChatGPT's probe coordinates, routed through the
    fixed joint centre. The length is constant, so the moment arm is zero; C1 counts the crossing, C2 accepts it and
    records negligible leverage."""
    m = ma.assemble(spec, "gait2392", "fixed_knee")
    thigh, shank = m.segments[SEG["thigh"]], m.segments[SEG["shank"]]
    femur, tibia = thigh.reference_frame, shank.reference_frame
    centre = thigh.inbound.outer_point(0.0)[0]          # the fixed joint centre in the thigh's coordinates
    pts = [ma.PathPoint(femur, SEG["thigh"], "fixed", location=centre + np.array([-0.21, 0.06, 0.0])),
           ma.PathPoint(femur, SEG["thigh"], "fixed", location=centre),
           ma.PathPoint(tibia, SEG["shank"], "fixed", location=np.array([0.22, -0.07, 0.0]))]
    probe = dataclasses.replace(m.actuators[0], points=pts)
    probe.id = "probe"
    m.actuators = [probe]
    q, _, _ = _motion()
    ids, R = mp.moment_arm_series(m, q)
    lengths = [mp.path(m, probe, q[:, i])[0] for i in range(q.shape[1])]
    assert max(lengths) - min(lengths) < 1e-12 and float(np.max(np.abs(R))) < 1e-9
    crossings = cs.derived_crossings(spec, {"probe": [p.frame for p in pts]})
    assert crossings["probe"][0] == ["LB:JOINT:KNEE_R"]
    c2 = cs.check_c2(spec, crossings, {("gait2392", "fixed_knee"): (ids, R)})
    assert c2["passed"] and [n["joint"] for n in c2["crosses_negligible_leverage"]] == ["LB:JOINT:KNEE_R"]


def test_a5_fixed_knee_c3_fails_when_the_reference_lacks_the_disagreement(schema, arm_series):
    """Amendment 1: with the lateral gastrocnemius disagreement removed from a copy of the fixed-knee reference, the
    fixed-knee C3 fails, naming lat_gas_r."""
    def remove(arms):
        r = arms["lat_gas_r"]
        r[1] = np.where(r[1] < 0, abs(r[1]), r[1])
    r = _checks(AnatomyOntology([HIP, LOWER]), schema, arm_series,
                references={"fixed_knee": _reference_arms(change=remove)})
    fails = [f for f in r["C3_actions"]["direction_failures"] if "unconfirmed_by_reference" in f]
    assert {tuple(f["case"]) for f in fails} == {(b, "fixed_knee") for b in ("female", "male", "gait2392")}
    assert {u["actuator"] for f in fails for u in f["unconfirmed_by_reference"]} == {"LB:ACT:G2392:LAT_GAS_R"}


def test_a5_fixed_knee_without_a_reference_would_fail_pass_fail(schema, arm_series):
    r = _checks(AnatomyOntology([HIP, LOWER]), schema, arm_series, references={})
    cases = {tuple(f["case"]) for f in r["C3_actions"]["direction_failures"]}
    assert cases == {(b, "fixed_knee") for b in ("female", "male", "gait2392")}


def test_fixed_knee_direction_deviations_are_registered(onto, schema, arm_series):
    """C5 (Amendment 1): with the fixed knee, lateral gastrocnemius (at least 1 mm, 49 poses, 126-174) and medial
    gastrocnemius (below 1 mm, 29 poses) drive knee extension; the moving knee has none."""
    r = _checks(onto, schema, arm_series)
    for body, extreme in (("female", -2.973741e-3), ("male", -2.984025e-3), ("gait2392", -3.085149e-3)):
        e = r["C3_actions"]["direction"][f"{body} | fixed_knee"]
        assert e["reference_confirmed"] and e["same_samples_as_reference"]
        (lat,) = e["disagreements_at_least_1mm"]
        assert (lat["actuator"], lat["samples"], lat["first_sample"], lat["last_sample"]) == \
            ("LB:ACT:G2392:LAT_GAS_R", 49, 126, 174)
        assert lat["extreme_moment_arm_m"] == pytest.approx(extreme, abs=1e-9) and lat["extreme_sample"] == 150
        small = {d["actuator"]: d for d in e["disagreements_above_numerical_zero"]}
        assert small["LB:ACT:G2392:MED_GAS_R"]["samples"] == 29
        assert abs(small["LB:ACT:G2392:MED_GAS_R"]["extreme_moment_arm_m"]) < 1e-3
        assert not r["C3_actions"]["direction"][f"{body} | moving_knee"]["disagreements_above_numerical_zero"]
    reg = r["C5_deviation_register"]
    assert set(reg["direction_disagreements"]) == {f"{b} | fixed_knee" for b in ("female", "male", "gait2392")}


def test_a5_left_deletion_fails_required_edges_and_mirror(schema, arm_series):
    r = _checks(_onto(lambda o: _drop(o, BFL[1], "CROSSES", "LB:JOINT:KNEE_L")), schema, arm_series)
    assert not r["required_edges"]["passed"] and not r["mirror"]["passed"] and r["C1_crossings"]["passed"]
    assert r["mirror"]["differences"] == [{"pair": list(BFL), "predicates": ["CROSSES"]}]


def test_a5_deletion_on_both_sides_fails_required_edges_and_c1_not_mirror(schema, arm_series):
    def both(o):
        _drop(o, BFL[0], "CROSSES", "LB:JOINT:KNEE_R")
        _drop(o, BFL[1], "CROSSES", "LB:JOINT:KNEE_L")
    r = _checks(_onto(both), schema, arm_series)
    assert not r["required_edges"]["passed"] and not r["C1_crossings"]["passed"] and r["mirror"]["passed"]


def test_c5_register_contents(onto, schema, arm_series):
    reg = _checks(onto, schema, arm_series)["C5_deviation_register"]
    assert reg["represented"]["modelled_joints"] == ["LB:JOINT:ANKLE_R", "LB:JOINT:KNEE_R", "LB:JOINT:HIP_R"]
    assert reg["simplified"]["merged_segments"] == {"LB:SEG:HAT": ["LB:SEG:HAT", "LB:SEG:PELVIS", "LB:SEG:TORSO"]}
    merged = {j["joint"]: j for j in reg["simplified"]["locked_or_merged_joints"]}
    assert merged["LB:JOINT:MTP_R"]["note"] == "merged; endpoints not stated in the ontology"
    assert reg["simplified"]["crossed_not_modelled"]["LB:MUS:GASTROCNEMIUS_R"] == ["LB:JOINT:SUBTALAR_R"]
    omitted = reg["omitted"]
    assert omitted["coordinates"] == ["LB:DOF:HIP_AB_AD_R", "LB:DOF:HIP_ROTATION_R"]
    assert {"LB:MUS:SARTORIUS_R", "LB:MUS:ADDUCTOR_LONGUS_R", "LB:MUS:ILIOPSOAS_ILIACUS_R"} <= \
        set(omitted["muscles_crossing_a_modelled_joint_without_an_actuator"])
    assert "external_rotation" in omitted["out_of_plane_capabilities"]["LB:MUS:GLUTEUS_MAXIMUS_R"]


def test_c4_fails_without_registered_evidence(schema, arm_series):
    onto = _onto(lambda o: o.entities["LB:MUS:SOLEUS_R"].update({"evidence": []}))
    r = _checks(onto, schema, arm_series)
    assert not r["C4_evidence"]["passed"]
    assert {"entity": "LB:MUS:SOLEUS_R", "problem": "no registered evidence"} in r["C4_evidence"]["failures"]


# ------------------------------------------------------------- the runner and the generic oracle tool (A2, A7 prep)
import xml.etree.ElementTree as ET  # noqa: E402

from tools import make_d2_oracle as oracle_tool  # noqa: E402
from tools import run_phase_d4 as d4r  # noqa: E402


def test_runner_configuration_loads_and_rejects_unknown_fields(tmp_path):
    cfg = d4r.load_config()
    assert cfg["specification"] == "squat_d4" and cfg["baseline_variant"] == "moving_knee"
    bad = dict(cfg, extra=1)
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="must be exactly"):
        d4r.load_config(path)


def test_stored_precision_comparison():
    assert d4r.stored_precision_difference([0.123457], [0.1234565], 6)[0] == 0.0
    assert d4r.stored_precision_difference([0.123457], [0.1234575001], 6)[0] > 0      # one unit off at 6 decimals
    assert d4r.stored_precision_difference([0.0, 0.0], [0.0, 4e-2], 9)[0] > 0       # zeros are compared at 9 decimals
    assert d4r.stored_precision_difference([[1.5, None]], [[1.5, float("nan")]], 3)[0] == 0.0
    assert d4r.stored_precision_difference([[1.5, None]], [[1.5, 2.0]], 3)[0] == float("inf")


@pytest.fixture(scope="module")
def regression_case(spec):
    """The runner's raw output for the Gait2392 body in both knee variants, produced by the build path's own case
    loop (`run_cases`), with the context A2's derived statuses need."""
    cfg = dict(d4r.load_config(), bodies=["gait2392"])
    from src import squat_d1 as sq1
    _, d1p = sq1.load_config(ROOT / cfg["d1_config"])
    _, d2p = d2r.load_config(ROOT / cfg["d2_config"])
    tol = yaml.safe_load((ROOT / cfg["d3_config"]).read_text(encoding="utf-8"))["tolerances"]
    _, raws, _ = d4r.run_cases(spec, cfg, d1p, d2p, tol)
    raws = {v: raws[("gait2392", v)] for v in ("moving_knee", "fixed_knee")}
    ref = json.loads((ROOT / cfg["references"]["moving_knee"]["path"]).read_text(encoding="utf-8"))
    model = ma.assemble(spec, "gait2392", "moving_knee")
    oracle = {"moving_knee": d4r.reference_comparison(model, ref, cfg["references"]["moving_knee"]["kinematics"])}
    return cfg, raws, {"oracle": oracle, "tol": tol, "d2p": d2p, "d1p": d1p}


def _changed_manifest(tmp_path, role_cfg, change):
    official = json.loads((ROOT / role_cfg["path"]).read_text(encoding="utf-8"))
    run = next(r for r in official["runs"] if r["body"] == "gait2392")
    change(run)
    copy = tmp_path / "changed.json"
    copy.write_text(json.dumps(official), encoding="utf-8")
    return {"changed": dict(role_cfg, path=str(copy))}


def test_a2_compares_every_required_series_and_status(regression_case):
    """D4-B01: every series and status of the pinned D1-D3 manifests is compared, including time and positions."""
    cfg, raws, ctx = regression_case
    reg = cfg["regression"]
    for v, roles in reg["manifests"].items():
        result = d4r.regression(raws[v], roles, reg, ctx)
        assert result["passed"] and result["largest_excess"] == 0.0 and not result["problems"], v
        for role, m in roles.items():
            official = json.loads((ROOT / m["path"]).read_text(encoding="utf-8"))
            run = next(r for r in official["runs"] if r["body"] == "gait2392")
            got = result["by_manifest"][role]
            assert set(got["series"]) == set(run["series"]), (v, role)
            assert set(got["statuses"]) == set(run["status"]), (v, role)
    assert "points_m" in reg["manifests"]["fixed_knee"]["mechanics"]["series"]
    assert "t_s" in reg["manifests"]["moving_knee"]["mechanics_and_muscles"]["series"]


@pytest.mark.parametrize("label, change, expect", [
    ("body point", lambda r: r["series"]["d1_points_m"]["knee"]["x"].__setitem__(100, r["series"]["d1_points_m"]["knee"]["x"][100] + 1e-5),
     "series"),
    ("time stamp", lambda r: r["series"]["t_s"].__setitem__(7, r["series"]["t_s"][7] + 1e-6), "series"),
    ("status", lambda r: r["status"].update(optimizer_verification="failed"), "status"),
    ("omitted series", lambda r: r["series"].pop("t_s"), "problem"),
    ("omitted status", lambda r: r["status"].pop("kinematics_verification"), "problem"),
    ("extra series", lambda r: r["series"].update(new_series=[0.0] * 301), "problem"),
    ("two path frames merged", lambda r: r["series"].__setitem__(
        "muscle_path_xy_m", [r["series"]["muscle_path_xy_m"][0] + r["series"]["muscle_path_xy_m"][1]]
        + r["series"]["muscle_path_xy_m"][2:]), "shape"),
])
def test_a2_catches_a_changed_or_missing_official_field(tmp_path, regression_case, label, change, expect):
    """D4-B01: a changed body-point sample, time stamp or status, or an omitted or unexpected field, fails A2."""
    cfg, raws, ctx = regression_case
    roles = _changed_manifest(tmp_path, cfg["regression"]["manifests"]["moving_knee"]["mechanics_and_muscles"], change)
    result = d4r.regression(raws["moving_knee"], roles, cfg["regression"], ctx)
    assert not result["passed"], label
    got = result["by_manifest"].get("changed", {})
    if expect == "series":
        assert result["largest_excess"] > 0
    elif expect == "shape":
        assert result["largest_excess"] == float("inf")
        assert got["series"]["muscle_path_xy_m"]["shape_difference"] == "/: length 300 stored, 301 new"
    elif expect == "status":
        assert not got["statuses"]["optimizer_verification"]["equal"]
    else:
        assert result["problems"]


def test_a2_rejects_a_nonfinite_replacement(regression_case):
    """D4-B01: a finite stored value with a NaN or infinite new value is infinite excess, never a pass."""
    assert d4r.stored_precision_difference([0.123457], [float("nan")], 6)[0] == float("inf")
    assert d4r.stored_precision_difference([0.123457], [float("inf")], 6)[0] == float("inf")
    assert d4r.stored_precision_difference(["passed"], [1.0], 6)[0] == float("inf")
    cfg, raws, ctx = regression_case
    raw = dict(raws["moving_knee"])
    raw["activation"] = raw["activation"].copy()
    raw["activation"][3, 120] = float("nan")
    roles = cfg["regression"]["manifests"]["moving_knee"]
    result = d4r.regression(raw, roles, cfg["regression"], ctx)
    assert not result["passed"] and result["largest_excess"] == float("inf")


def test_a2_derived_status_mappings(regression_case):
    """The two D2/D3 statuses whose meaning differs from D4's are mapped as stated and agree."""
    cfg, raws, ctx = regression_case
    st = cfg["regression"]["statuses"]
    assert st["d1_consistency"]["derived"] == "torque_agreement"
    assert st["kinematics_verification"]["derived"] == "reference_kinematics"
    assert d4r._derived_status("d1_consistency", st["d1_consistency"], raws["fixed_knee"], dict(ctx, reg=cfg["regression"])) == "passed"
    bad = dict(ctx, oracle={"moving_knee": {"largest_kinematics_difference_m": 1.0}}, reg=cfg["regression"])
    assert d4r._derived_status("kinematics_verification", st["kinematics_verification"], raws["moving_knee"], bad) == "failed"


def test_a2_compares_the_emitted_time_on_the_build_path(spec, regression_case, monkeypatch):
    """D4-B01 (re-review): the time a run emits is the time A2 compares. Shift sample 7 of the time the dynamics
    returns by 1 microsecond; through the build path (`run_cases`, `run_regressions`) the published series carries
    the shifted value and A2 fails on `t_s`. Unshifted, the same path passes."""
    cfg, _, ctx = regression_case
    small = dict(cfg, variants=["moving_knee"], baseline_variant="moving_knee",
                 regression=dict(cfg["regression"], manifests={"moving_knee": cfg["regression"]["manifests"]["moving_knee"]}))
    run = ma.run

    def shifted(model, d1p):
        res = run(model, d1p)
        res["t"] = np.array(res["t"], float)
        res["t"][7] += 1e-6
        return res

    monkeypatch.setattr(ma, "run", shifted)
    runs, raws, _ = d4r.run_cases(spec, small, ctx["d1p"], ctx["d2p"], ctx["tol"])
    assert runs[0]["series"]["t_s"][7] == pytest.approx(0.070001, abs=1e-12)
    result = d4r.run_regressions(small, raws, ctx)["gait2392 | moving_knee"]
    assert not result["passed"]
    assert result["by_manifest"]["mechanics_and_muscles"]["series"]["t_s"]["excess_over_half_unit"] > 0
    monkeypatch.setattr(ma, "run", run)
    _, raws, _ = d4r.run_cases(spec, small, ctx["d1p"], ctx["d2p"], ctx["tol"])
    assert d4r.run_regressions(small, raws, ctx)["gait2392 | moving_knee"]["passed"]


def test_a2_checks_the_nested_shape_before_the_values():
    """D4-B01 (re-review): two frames of the committed D3 muscle paths merged into one keep the same flattened
    numbers but fail A2; so does any change in the number of actuators in a frame or points in a path."""
    official = json.loads((ROOT / "results/phase_d/2026-11-11_d3_moving_knee_runs_d3efc56.json").read_text(encoding="utf-8"))
    paths = next(r for r in official["runs"] if r["body"] == "gait2392")["series"]["muscle_path_xy_m"]
    merged = [paths[0] + paths[1]] + paths[2:]
    assert d4r._flatten(merged) == d4r._flatten(paths)             # the bypass ChatGPT found: same flat sequence
    assert d4r.stored_precision_difference(paths, merged, 5)[0] == float("inf")
    assert d4r.shape_difference(paths, merged) == "/: length 301 stored, 300 new"
    assert d4r.stored_precision_difference(paths, deepcopy(paths), 5)[0] == 0.0
    fewer = deepcopy(paths)
    fewer[5] = fewer[5][:-1]                                        # an actuator dropped from one frame
    assert d4r.shape_difference(paths, fewer) == "[5]: length 14 stored, 13 new"
    moved = deepcopy(paths)
    moved[9][0] = moved[9][0][:-1] + [moved[9][0][-1][0]]           # a point's [x, y] turned into a bare x
    assert d4r.shape_difference(paths, moved).startswith("[9][0]")
    assert d4r.stored_precision_difference([[1.0, 2.0]], np.array([[1.0, 2.0]]), 1)[0] == 0.0
    assert d4r.stored_precision_difference([[1.0, 2.0]], np.array([1.0, 2.0]), 1)[0] == float("inf")


def test_d2_loader_reads_its_view_not_every_actuator_record():
    acts, _ = m2.load_actuators(1.0)
    onto = AnatomyOntology([HIP, LOWER])
    assert [a.name for a in acts] == [onto.model_element(a)[1] for a in onto.data["models"]["squat_d2"]["represents"]]
    assert "re.fullmatch" not in (ROOT / "src" / "muscles_d2.py").read_text(encoding="utf-8")


def test_oracle_tool_reads_actuators_from_the_ontology():
    assert oracle_tool.ACTUATORS == oracle_tool.actuators_for("squat_d2") == oracle_tool.actuators_for("squat_d4")
    assert len(oracle_tool.ACTUATORS) == 14


def test_oracle_tool_finds_switches_driven_by_any_coordinate():
    """The generic state generator handles points switched by hip flexion (the iliopsoas case of D-062 item 8)
    before any iliopsoas data exist; knee-driven states keep their existing keys."""
    root = ET.fromstring(oracle_tool.matched_model_xml("moving"))
    states = oracle_tool.geometry_states(root, ["iliacus_r", "psoas_r"])
    sides = [s for s in states if s["kind"] == "switch_side"]
    assert sides and all("edge_hip_flexion_gait2392" in s for s in sides)
    assert {s["side"] for s in sides} == {"flexion_side", "extension_side"}
    edges = [s for s in states if s["kind"] == "switch_edge"]
    assert [round(s["edge_hip_flexion_gait2392"], 9) for s in edges] == [round(0.785398 + 1e-5, 9)]
    assert edges[0]["q"][2] == edges[0]["edge_hip_flexion_gait2392"]
    knee = oracle_tool.geometry_states(root)
    assert any("edge_knee_angle_gait2392" in s for s in knee) and not any("edge_hip_flexion_gait2392" in s for s in knee)


@pytest.mark.parametrize("path,mode", [("tests/data/d2_oracle_reference.json", "fixed"),
                                       ("tests/data/d3_oracle_reference.json", "moving")])
def test_regenerated_references_record_their_model(path, mode):
    ref = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert ref["provenance"]["model_specification"] == "squat_d2"
    assert check_reference(ref, mode) == []


# =============================================================================================================
# Step 4: the iliopsoas growth test (item 8), criterion A7. The growth commit itself changed no file in src/ or tools/
# (recorded in D-062's build record with the commit's file list).
# =============================================================================================================
GROWTH = "squat_d4_iliopsoas"
GROWTH_REF = ROOT / "tests" / "data" / "d4_iliopsoas_oracle_reference.json"
NEW = ("LB:ACT:G2392:ILIACUS_R", "LB:ACT:G2392:PSOAS_R")


@pytest.fixture(scope="module")
def growth(onto, schema):
    return load_spec(GROWTH, onto, schema)


def test_a7_growth_specification_extends_the_baseline(growth, spec):
    assert growth.raw["extends"] == "squat_d4"
    assert growth.actuators == spec.actuators + list(NEW)
    assert growth.segments == spec.segments and growth.tree == spec.tree


def test_a7_new_points_are_switched_by_the_hip_coordinate(growth):
    m = ma.assemble(growth, "gait2392", "moving_knee")
    hip = m.coordinates.index("LB:DOF:HIP_FLEX_EXT_R")
    for aid in NEW:
        (act,) = [a for a in m.actuators if a.id == aid]
        cond = [p for p in act.points if p.kind == "conditional"]
        assert len(cond) == 1 and cond[0].coordinate == hip
        q, _, _ = _motion()
        active = [ma.point_active(cond[0], q[:, i]) for i in range(q.shape[1])]
        assert active[0] and not all(active)          # switches off during the squat, as hip flexion passes 45 deg


def test_a7_new_actuator_geometry_matches_opensim(growth):
    ref = json.loads(GROWTH_REF.read_text(encoding="utf-8"))
    assert check_reference(ref, "moving") == []
    assert ref["provenance"]["model_specification"] == GROWTH and ref["actuators"][-2:] == ["iliacus_r", "psoas_r"]
    assert any(k.startswith("edge_hip_flexion") for g in ref["geometry"] for k in g)
    m = ma.assemble(growth, "gait2392", "moving_knee")
    by_name = {a.name: a for a in m.actuators}
    for g in ref["geometry"]:
        q = np.array(g["q"])
        frames = ma.segment_frames(m, q)
        for name in ref["actuators"]:
            L, R, _ = mp.path(m, by_name[name], q, frames)
            assert abs(L - g["length_m"][name]) < 1e-9, (name, g["kind"])
            assert np.max(np.abs(R - np.array(g["moment_arm_m"][name]))) < 1e-9, (name, g["kind"])


def test_a7_consistency_checks_pass_for_the_grown_model(growth):
    q, _, _ = _motion()
    models = [ma.assemble(growth, b, v) for b, v in CASES]
    arms = {(m.body, m.variant): mp.moment_arm_series(m, q) for m in models}
    r = cs.run_checks(growth, models, arms, {"fixed_knee": _reference_arms()})
    for key in ("C1_crossings", "C2_leverage", "C3_actions", "C4_evidence", "required_edges", "mirror"):
        assert r[key]["passed"], key
    per = r["C1_crossings"]["per_muscle"]
    assert per["LB:MUS:ILIOPSOAS_PSOAS_MAJOR_R"]["derived"] == ["LB:JOINT:HIP_R"]
    elements = {e["entity"] for e in r["C5_deviation_register"]["simplified"]["elements"]}
    assert "LB:ACT:G2392:PSOAS_R" in elements
    omitted = r["C5_deviation_register"]["omitted"]["muscles_crossing_a_modelled_joint_without_an_actuator"]
    assert "LB:MUS:ILIOPSOAS_ILIACUS_R" not in omitted and "LB:MUS:SARTORIUS_R" in omitted


def test_a7_baseline_unchanged_by_the_growth(spec):
    """Adding actuators to the ontology and dataset leaves squat_d4 and the D2 view at 14 actuators."""
    assert len(spec.actuators) == 14
    assert len(m2.load_actuators(1.0)[0]) == 14
    assert oracle_tool.actuators_for("squat_d2") == oracle_tool.ACTUATORS


def test_a8_hip_module_and_phase_b_unchanged():
    hip = AnatomyOntology(HIP)
    assert hip.added_edges == [] and "LB:ACT:G2392:PSOAS_R" not in hip.entities


# =============================================================================================================
# Review D4-B02 to D4-B04 (ChatGPT, PR #48)
# =============================================================================================================
import subprocess  # noqa: E402

from src.run_manifest import VERIFIED, manifest_header  # noqa: E402


def test_c1_is_checked_per_actuator(spec):
    """D4-B02: with the knee crossing removed from one of the two gastrocnemius actuators' paths, the muscle-level
    union still shows both joints, yet C1 fails and names that actuator."""
    m = ma.assemble(spec, "gait2392", "moving_knee")
    frames = cs.actuator_frames(m)
    femur, tibia = m.segments[SEG["thigh"]].reference_frame, m.segments[SEG["shank"]].reference_frame
    frames["LB:ACT:G2392:MED_GAS_R"] = [tibia if f == femur else f for f in frames["LB:ACT:G2392:MED_GAS_R"]]
    r = cs.check_c1(spec, cs.derived_crossings(spec, frames))
    assert r["per_muscle"]["LB:MUS:GASTROCNEMIUS_R"]["derived"] == ["LB:JOINT:ANKLE_R", "LB:JOINT:KNEE_R"]
    assert not r["passed"]
    assert r["failures"] == [{"actuator": "LB:ACT:G2392:MED_GAS_R", "muscle": "LB:MUS:GASTROCNEMIUS_R",
                              "missing_CROSSES": [], "declared_but_not_crossed": ["LB:JOINT:KNEE_R"]}]
    assert r["per_actuator"]["LB:ACT:G2392:LAT_GAS_R"]["agrees"]


def _consumed(spec):
    out = {}
    for b in ("female", "male", "gait2392"):
        for v in ("moving_knee", "fixed_knee"):
            for name, ids in ma.assemble(spec, b, v).consumed.items():
                out.setdefault(name, []).extend(ids)
    return out


def test_c4_traces_every_structural_entity(spec):
    """D4-B03: every represented segment, joint and coordinate has an entity-level basis."""
    r = cs.check_c4(spec, _consumed(spec))
    assert r["passed"]
    basis = r["structural_basis"]
    assert set(basis) == set(spec.segments) | set(spec.joints) | set(spec.coordinates) and len(basis) == 13
    assert all(e["traced"] for e in basis.values())
    assert "LB-QD:G2392:JOINT:KNEE_R_MOVING" in [x["record"] for x in basis["LB:JOINT:KNEE_R"]["basis"]["records"]]
    assert basis["LB:DOF:KNEE_FLEX_EXT_R"]["basis"] == {"declared_model_convention":
                                                         spec.ontology.get("LB:DOF:KNEE_FLEX_EXT_R")["convention"]}
    assert basis["LB:DOF:HIP_FLEX_EXT_R"]["basis"]["convention_source"] == "SRC:ISB_WU_2002"
    assert basis["LB:JOINT:MTP_R"]["declared_state"] == "locked at zero"


def test_c4_fails_for_a_coordinate_without_a_basis(schema):
    """D4-B03: removing the knee coordinate's declared convention leaves it untraced; C4 fails naming it."""
    onto = AnatomyOntology([HIP, LOWER])
    onto.entities["LB:DOF:KNEE_FLEX_EXT_R"].pop("convention")
    sp = load_spec("squat_d4", onto, QuantitativeSchema(SCHEMA, ontology=onto))
    r = cs.check_c4(sp, _consumed(sp))
    assert not r["passed"]
    assert {"entity": "LB:DOF:KNEE_FLEX_EXT_R", "problem": "represented coordinate has no traceable basis"} in r["failures"]


def test_c4_fails_for_a_joint_without_a_basis(schema):
    """D4-B03: the hip joint without its evidence and without a record that names it fails C4, naming it, while
    every numeric input stays valid."""
    onto = AnatomyOntology([HIP, LOWER])
    onto.entities["LB:JOINT:HIP_R"].pop("evidence")
    sp = load_spec("squat_d4", onto, QuantitativeSchema(SCHEMA, ontology=onto))
    consumed = _consumed(sp)
    rec = sp.datasets["geometry"]["observations"]["LB-QD:G2392:JOINT:HIP_R"]
    rec["target"] = dict(rec["target"], entity_ids=["LB:JOINT:HIP_L"])   # still a valid joint record, not this joint
    r = cs.check_c4(sp, consumed)
    assert {"entity": "LB:JOINT:HIP_R", "problem": "represented joint has no traceable basis"} in r["failures"]
    assert not [f for f in r["failures"] if "dataset" in f]          # the numeric gate still passes


def test_a9_inventory_includes_the_active_code(spec):
    """D4-B04: the D1 configuration loader and the datum validator are verified inputs, with every loaded module of
    src/ and tools/."""
    cfg = d4r.load_config()
    paths = d4r.input_paths(cfg, spec, d4r.CONFIG)
    rel = {Path(p).resolve().relative_to(ROOT).as_posix() for p in paths.values()}
    for f in ("src/squat_d1.py", "src/datum_model.py", "src/quantitative.py", "src/model_assembly.py",
              "tools/run_phase_d4.py", "sources/vendor/opensim-models/gait2392_millard2012muscle.osim"):
        assert f in rel, f


def test_a9_a_dirty_d1_loader_prevents_a_verified_manifest(spec, tmp_path):
    """D4-B04: in a clean checkout of HEAD the inputs verify; editing src/squat_d1.py there makes verification fail."""
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    wt = tmp_path / "wt"
    subprocess.run(["git", "worktree", "add", "--detach", str(wt), head], cwd=ROOT, capture_output=True, check=True)
    try:
        cfg = d4r.load_config()
        paths = {k: str(v) for k, v in d4r.input_paths(cfg, spec, d4r.CONFIG, root=wt.resolve()).items()}
        status, _ = d4r.verify_inputs(wt.resolve(), paths, head)
        assert status == VERIFIED
        loader = wt / "src" / "squat_d1.py"
        loader.write_text(loader.read_text(encoding="utf-8") + "\n# local edit\n", encoding="utf-8")
        with pytest.raises(ValueError, match="working file differs from HEAD: src/squat_d1.py"):
            manifest_header(wt.resolve(), paths, head)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=ROOT, capture_output=True)
