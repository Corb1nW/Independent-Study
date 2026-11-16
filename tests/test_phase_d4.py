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
NEW_MODULES = ("src/model_spec.py", "src/model_assembly.py", "src/muscle_paths.py")


@pytest.mark.parametrize("path", NEW_MODULES)
def test_a6_no_anatomy_or_ontology_ids_in_the_new_modules(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    assert not re.search(r"\bLB(:|-QD)", text), "ontology or dataset ID in code"
    words = set(re.findall(r"[a-z]+", text.lower()))
    assert not words & set(ANATOMY_TERMS), sorted(words & set(ANATOMY_TERMS))


def test_a6_scan_would_catch_a_planted_term(tmp_path):
    text = (ROOT / NEW_MODULES[1]).read_text(encoding="utf-8") + "\n# knee\n"
    assert set(re.findall(r"[a-z]+", text.lower())) & set(ANATOMY_TERMS) == {"knee"}
