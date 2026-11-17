"""Stage D5, step 1 (D-063 with Amendment 1): the generic preparation, made before any anatomy is added.

- lumped actuators (item 5): a list in `represents` with represented_scope "lumped"; C1 per represented muscle, C4
  evidence for each, C3 capabilities as their union;
- bounded direction exceptions (Amendment 1, ChatGPT D5-R01): a disagreement passes only when declared and confirmed by
  the reference's own moment arm; undeclared, unconfirmed and stale declarations fail;
- nested specifications in the oracle tool (D5-R02); tools read the schema's ontology list;
- the complete C5 inventory of muscles without an actuator (D5-R02);
- per-actuator torque shares (A8), opt-in through the run configuration.
"""
import copy
import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from src import consistency as cs
from src import model_assembly as ma
from src import muscle_paths as mp
from src.model_spec import SpecError, default_ontology, default_schema, load_spec, raw_specification, represented
from src.ontology import AnatomyOntology
from tools import make_d2_oracle as oracle_tool
from tools import run_phase_d4 as d4r

ROOT = Path(__file__).resolve().parents[1]
HIP, LOWER = ROOT / "ontology" / "hip.yaml", ROOT / "ontology" / "lower_limb_sagittal.yaml"
FIXED_REF = ROOT / "tests" / "data" / "d2_oracle_reference.json"
MOVING_REF = ROOT / "tests" / "data" / "d3_oracle_reference.json"
BODIES = ("female", "male", "gait2392")
BFL = "LB:MUS:BICEPS_FEMORIS_LONG_R"
KNEE = "LB:DOF:KNEE_FLEX_EXT_R"


def _reference_arms(path):
    ref = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = sorted((g for g in ref["geometry"] if g["kind"] == "d1_sample"), key=lambda g: g["index"])
    return {n: np.array([g["moment_arm_m"][n] for g in rows]).T for n in ref["actuators"]}


@pytest.fixture(scope="module")
def references():
    return {"fixed_knee": _reference_arms(FIXED_REF), "moving_knee": _reference_arms(MOVING_REF)}


@pytest.fixture(scope="module")
def motion():
    from src import squat_d1 as sq
    _, d1p = sq.load_config(ROOT / "config" / "phase_d1_squat.yaml")
    return d1p


@pytest.fixture(scope="module")
def arms(motion):
    spec = load_spec("squat_d4")
    res = ma.run(ma.assemble(spec, "gait2392", "moving_knee"), motion)
    q = res["q"]
    return {(b, v): mp.moment_arm_series(ma.assemble(spec, b, v), q) for b in BODIES for v in ("moving_knee", "fixed_knee")}


def _onto(change=None):
    onto = AnatomyOntology([HIP, LOWER])
    if change:
        change(onto)
    return onto


def _checks(onto, arms, references, spec_change=None):
    schema = default_schema(onto)
    spec = load_spec("squat_d4", onto, schema)
    if spec_change:
        spec_change(spec)
    models = [ma.assemble(spec, "gait2392", "moving_knee")]
    return cs.run_checks(spec, models, arms, references)


# ------------------------------------------------------------------------- bounded direction rule (D5-R01)
def test_d4_specification_passes_with_both_references(arms, references):
    r = _checks(_onto(), arms, references)
    assert r["passed"], {k: v.get("passed") for k, v in r.items() if isinstance(v, dict)}
    for b in BODIES:
        e = r["C3_actions"]["direction"][f"{b} | fixed_knee"]
        assert [d["actuator"] for d in e["declared_and_confirmed"]] == ["LB:ACT:G2392:LAT_GAS_R"]
        assert not r["C3_actions"]["direction"][f"{b} | moving_knee"]["disagreements_at_least_1mm"]


@pytest.mark.parametrize("variants", [("moving_knee",), ("fixed_knee",), ("moving_knee", "fixed_knee")])
def test_chatgpts_probe_fails_with_the_reference_supplied(arms, references, variants):
    """ChatGPT's D5-R01 probe: biceps femoris long head declared a knee extensor, geometry unchanged, matched
    references supplied. Under D4's rule this passed on the moving knee; now every case fails as undeclared."""
    def flip(o):
        caps = o.entities[BFL]["mechanical_capabilities"]
        caps[caps.index("knee_flexion")] = "knee_extension"
    r = _checks(_onto(flip), arms, {v: references[v] for v in variants} | {"fixed_knee": references["fixed_knee"]})
    c3 = r["C3_actions"]
    assert not c3["passed"]
    failed = {tuple(f["case"]) for f in c3["direction_failures"] if "undeclared" in f
              and any(d["actuator"] == "LB:ACT:G2392:BIFEMLH_R" for d in f["undeclared"])}
    assert failed == {(b, v) for b in BODIES for v in ("moving_knee", "fixed_knee")}


def test_an_undeclared_new_disagreement_fails_even_where_the_reference_agrees(arms, references):
    """The reference geometry has the same sign as the model; without a declaration that is not enough."""
    def drop_ankle(o):
        caps = o.entities["LB:MUS:SOLEUS_R"]["mechanical_capabilities"]
        caps.remove("ankle_plantarflexion")
    r = _checks(_onto(drop_ankle), arms, references)
    undeclared = [d for f in r["C3_actions"]["direction_failures"] if "undeclared" in f for d in f["undeclared"]]
    assert undeclared and {d["actuator"] for d in undeclared} == {"LB:ACT:G2392:SOLEUS_R"}


def test_a_declared_deviation_the_reference_does_not_confirm_fails(arms, references):
    ref = copy.deepcopy(references)
    r_lat = ref["fixed_knee"]["lat_gas_r"]
    r_lat[1] = np.abs(r_lat[1])                 # the reference no longer has the knee-extension moment arm
    r = _checks(_onto(), arms, ref)
    fails = [f for f in r["C3_actions"]["direction_failures"] if "unconfirmed_by_reference" in f]
    assert {tuple(f["case"]) for f in fails} == {(b, "fixed_knee") for b in BODIES}


def test_a_declaration_with_the_wrong_motion_does_not_cover_the_disagreement(arms, references):
    def wrong(spec):
        spec.raw["expected_direction_deviations"] = [dict(d, drives="knee_flexion")
                                                     for d in spec.raw["expected_direction_deviations"]]
    r = _checks(_onto(), arms, references, spec_change=wrong)
    kinds = {k for f in r["C3_actions"]["direction_failures"] for k in f if k != "case"}
    assert kinds == {"undeclared", "stale_declarations"}


def test_a_stale_declaration_fails(arms, references):
    def stale(spec):
        spec.raw["expected_direction_deviations"] = list(spec.raw["expected_direction_deviations"]) + [
            {"actuator": "LB:ACT:G2392:TIB_ANT_R", "coordinate": "LB:DOF:ANKLE_DORSI_PLANTAR_R",
             "variants": ["moving_knee"], "drives": "ankle_plantarflexion", "basis": "a test declaration that never occurs"}]
    r = _checks(_onto(), arms, references, spec_change=stale)
    (f,) = [f for f in r["C3_actions"]["direction_failures"] if "stale_declarations" in f]
    assert f["stale_declarations"] == [{"actuator": "LB:ACT:G2392:TIB_ANT_R",
                                        "coordinate": "LB:DOF:ANKLE_DORSI_PLANTAR_R", "variant": "moving_knee"}]


@pytest.mark.parametrize("bad, message", [
    ({"basis": "short"}, "a basis"),
    ({"drives": "hip_flexion"}, "is not a motion of"),
    ({"variants": ["no_such_variant"]}, "must be variants of"),
    ({"actuator": "LB:ACT:G2392:ILIACUS_R"}, "is not an actuator of"),
    ({"extra": 1}, "needs exactly"),
])
def test_deviation_declarations_are_checked(bad, message):
    onto = _onto()
    dev = onto.data["models"]["squat_d4"]["expected_direction_deviations"][0]
    dev.update(bad)
    with pytest.raises(SpecError, match=message):
        load_spec("squat_d4", onto, default_schema(onto))


def test_extensions_inherit_and_add_declarations():
    onto = _onto()
    onto.data["models"]["probe_ext"] = {"kind": "executable_specification", "extends": "squat_d4_iliopsoas",
                                        "add_actuators": [], "expected_direction_deviations": [{"x": 1}]}
    raw = raw_specification(onto, "probe_ext")
    assert len(raw["actuators"]) == 16 and len(raw["expected_direction_deviations"]) == 2


# --------------------------------------------------------------------------------- lumped actuators (item 5)
def _lump(actuator, muscles_):
    def change(o):
        o.entities[actuator]["represents"] = list(muscles_)
        o.entities[actuator]["represented_scope"] = "lumped"
    return change


def test_a_lumped_actuator_is_checked_against_each_muscle(arms, references):
    onto = _onto(_lump("LB:ACT:G2392:SEMITEN_R", ["LB:MUS:SEMITENDINOSUS_R", "LB:MUS:SEMIMEMBRANOSUS_R"]))
    assert represented(onto, "LB:ACT:G2392:SEMITEN_R") == ["LB:MUS:SEMITENDINOSUS_R", "LB:MUS:SEMIMEMBRANOSUS_R"]
    r = _checks(onto, arms, references)
    assert r["passed"]
    entry = r["C1_crossings"]["per_actuator"]["LB:ACT:G2392:SEMITEN_R"]
    assert entry["agrees"] and set(entry["declared_modelled_per_muscle"]) == {"LB:MUS:SEMITENDINOSUS_R",
                                                                               "LB:MUS:SEMIMEMBRANOSUS_R"}
    assert set(r["C1_crossings"]["per_muscle"]["LB:MUS:SEMIMEMBRANOSUS_R"]["actuators"]) == {
        "LB:ACT:G2392:SEMIMEM_R", "LB:ACT:G2392:SEMITEN_R"}


def test_a_lumped_actuator_missing_evidence_for_one_muscle_fails_c4(arms, references):
    def change(o):
        _lump("LB:ACT:G2392:SEMITEN_R", ["LB:MUS:SEMITENDINOSUS_R", "LB:MUS:SEMIMEMBRANOSUS_R"])(o)
        o.entities["LB:MUS:SEMIMEMBRANOSUS_R"]["evidence"] = []
    r = _checks(_onto(change), arms, references)
    assert not r["C4_evidence"]["passed"]
    assert {"entity": "LB:MUS:SEMIMEMBRANOSUS_R", "problem": "no registered evidence"} in r["C4_evidence"]["failures"]


def test_a_lumped_actuator_whose_path_misses_a_muscles_joint_fails_c1(arms, references):
    """The vastus lateralis path crosses only the knee; lumped with rectus femoris, which crosses the hip too, C1 fails
    for that pairing, naming the actuator and the muscle."""
    onto = _onto(_lump("LB:ACT:G2392:VAS_LAT_R", ["LB:MUS:VASTUS_LATERALIS_R", "LB:MUS:RECTUS_FEMORIS_R"]))
    r = _checks(onto, arms, references)
    fails = r["C1_crossings"]["failures"]
    assert [(f["actuator"], f["muscle"], f["declared_but_not_crossed"]) for f in fails] == [
        ("LB:ACT:G2392:VAS_LAT_R", "LB:MUS:RECTUS_FEMORIS_R", ["LB:JOINT:HIP_R"])]


@pytest.mark.parametrize("represents, scope, message", [
    (["LB:MUS:SEMITENDINOSUS_R", "LB:MUS:SEMIMEMBRANOSUS_R"], "whole muscle", "needs represented_scope 'lumped'"),
    (["LB:MUS:SEMITENDINOSUS_R"], "lumped", "two or more distinct"),
    ("LB:MUS:SEMITENDINOSUS_R", "lumped", "needs a list"),
    (["LB:MUS:SEMITENDINOSUS_R", "LB:MUS:NO_SUCH_R"], "lumped", "represents no known entity"),
])
def test_lumped_representation_is_validated(represents, scope, message):
    onto = _onto()
    onto.entities["LB:ACT:G2392:SEMITEN_R"]["represents"] = represents
    onto.entities["LB:ACT:G2392:SEMITEN_R"]["represented_scope"] = scope
    with pytest.raises(SpecError, match=message):
        load_spec("squat_d4", onto, default_schema(onto))


# ------------------------------------------------------------------------------- C5 inventory (D5-R02)
def test_c5_inventory_lists_every_muscle_without_an_actuator(arms, references):
    """A muscle whose only crossing is the unmodelled metatarsophalangeal joint, and one that crosses nothing, appear in
    the inventory; under D4's register they appeared nowhere."""
    def add(o):
        for eid, crosses in (("LB:MUS:PROBE_TOE_R", ["LB:JOINT:MTP_R"]), ("LB:MUS:PROBE_NONE_R", [])):
            o.entities[eid] = {"name": eid, "class": "SkeletalMuscle", "side": "right",
                               "relationships": {"CROSSES": crosses} if crosses else {}}
    r = _checks(_onto(add), arms, references)
    inv = r["C5_deviation_register"]["omitted"]["muscles_without_an_actuator"]
    assert "LB:MUS:PROBE_TOE_R" in inv["crossing_only_joints_the_model_does_not_have"]
    assert "LB:MUS:PROBE_NONE_R" in inv["crossing_no_joint"]
    assert inv["crossing_a_modelled_joint"] == r["C5_deviation_register"]["omitted"][
        "muscles_crossing_a_modelled_joint_without_an_actuator"]
    every = {m for v in inv.values() for m in v} | set(cs.muscles(load_spec("squat_d4")))
    assert every == {e for e, x in _onto(add).entities.items() if x.get("class") == "SkeletalMuscle"}


# ------------------------------------------------------------------------- tools on the schema's modules (D5-R02)
def test_oracle_tool_resolves_nested_extensions(monkeypatch):
    onto = default_ontology()
    onto.data["models"]["probe_nested"] = {"kind": "executable_specification", "extends": "squat_d4_iliopsoas",
                                           "add_actuators": []}
    monkeypatch.setattr(oracle_tool, "_ontology", lambda: onto)
    assert oracle_tool.actuators_for("probe_nested") == oracle_tool.actuators_for("squat_d4_iliopsoas")
    assert len(oracle_tool.actuators_for("probe_nested")) == 16
    assert oracle_tool.actuators_for("squat_d2") == oracle_tool.ACTUATORS


def test_tools_load_the_modules_the_schema_names():
    schema_modules = yaml.safe_load((ROOT / "ontology" / "quantitative_schema.yaml").read_text())["ontology"]
    files = sorted(Path(m).name for m in schema_modules)
    assert sorted(m["file"] for m in oracle_tool._ontology().modules) == files
    from tools import build_segment_datasets as bsd
    assert sorted(m["file"] for m in bsd._onto().modules) == files
    for path in ("tools/make_d2_oracle.py", "tools/build_segment_datasets.py"):
        assert "lower_limb_sagittal.yaml" not in (ROOT / path).read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------ torque shares (A8)
def test_torque_shares_add_up_and_match_the_recruitment(motion):
    spec = load_spec("squat_d4")
    model = ma.assemble(spec, "gait2392", "moving_knee")
    res = ma.run(model, motion)
    every = 10
    q, qd, tau, t = res["q"][:, ::every], res["qd"][:, ::every], res["tau"][:, ::every], res["t"][::every]
    mus = mp.recruit_series(model, q, qd, tau, 1e-6, second_solver=False, needed_reserve=False)
    names = [a.name for a in model.actuators]
    shares = mp.torque_shares(names, model.coordinates, t, mus["force"], mus["moment_arms"])
    for c, row in shares.items():
        assert sum(v["share"] for v in row.values()) == pytest.approx(1.0, abs=1e-5)
    muscle_moment = np.einsum("jn,jkn->kn", mus["force"], mus["moment_arms"])
    np.testing.assert_allclose(muscle_moment + mus["reserve"], tau, atol=1e-6)


def test_runner_accepts_the_optional_torque_share_switch(tmp_path):
    cfg = yaml.safe_load((ROOT / "config" / "phase_d4_assembled.yaml").read_text(encoding="utf-8"))
    for value, ok in ((True, True), (False, True), ("yes", False)):
        path = tmp_path / "c.yaml"
        path.write_text(yaml.safe_dump(dict(cfg, report_torque_shares=value)), encoding="utf-8")
        if ok:
            assert d4r.load_config(path)["report_torque_shares"] is value
        else:
            with pytest.raises(ValueError, match="report_torque_shares"):
                d4r.load_config(path)
    path.write_text(yaml.safe_dump(dict(cfg, unknown=1)), encoding="utf-8")
    with pytest.raises(ValueError, match="configuration fields"):
        d4r.load_config(path)


def test_step1_code_names_no_anatomy():
    """A6 of D-062 extends to the step-1 additions: the new generic code names no ontology IDs."""
    for path in ("src/consistency.py", "src/model_spec.py", "src/muscle_paths.py"):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "LB:" not in text, path


# ------------------------------------------------------------------------------ step 2: leg anatomy (item 1)
LEG_NEW = {"BICEPS_FEMORIS_SHORT": True, "POPLITEUS": False, "PLANTARIS": False, "TIBIALIS_POSTERIOR": True,
           "FLEXOR_DIGITORUM_LONGUS": True, "FLEXOR_HALLUCIS_LONGUS": True, "FIBULARIS_LONGUS": True,
           "FIBULARIS_BREVIS": True, "EXTENSOR_DIGITORUM_LONGUS": True, "EXTENSOR_HALLUCIS_LONGUS": True,
           "FIBULARIS_TERTIUS": True}   # muscle -> modelled by Gait2392


def _registered_read():
    text = (ROOT / "sources" / "SOURCES.md").read_text(encoding="utf-8")
    return {line.split("`")[1] for line in text.splitlines()
            if line.startswith("| `SRC:") and line.rstrip().endswith("| Read |")}


def test_step2_leg_muscles_exist_on_both_sides_with_read_evidence():
    onto = default_ontology()
    read = _registered_read()
    for key, modelled in LEG_NEW.items():
        for s in "RL":
            e = onto.get(f"LB:MUS:{key}_{s}")
            assert e["class"] == "SkeletalMuscle" and e["side"] == {"R": "right", "L": "left"}[s]
            r = e["relationships"]
            assert r["CROSSES"] and set(r["ACTS_ON"]) <= set(r["CROSSES"]) and r["INNERVATED_BY"]
            assert all(j.endswith(f"_{s}") for j in r["CROSSES"])
            assert e["evidence"] and set(e["evidence"]) <= set(onto.sources) and set(e["evidence"]) <= read, key
            assert ("model_parameter_schema" in e) == modelled
            for t in r["CROSSES"] + r["INNERVATED_BY"]:
                assert t in onto.entities
    assert cs.check_mirror(onto)["passed"]


def test_step2_crossings_are_limited_to_what_the_sources_name():
    """Conservative edges: the toe extensors and the fibulares cross only the ankle (their chapters name no other
    joint); the long toe flexors also cross the metatarsophalangeal and interphalangeal joints the posterior-compartment
    chapter names; tibialis posterior also crosses the subtalar joint it inverts."""
    onto = default_ontology()
    def joints(k):
        return sorted(j.split(":")[-1] for j in onto.related(f"LB:MUS:{k}_R", "CROSSES"))
    for k in ("EXTENSOR_DIGITORUM_LONGUS", "EXTENSOR_HALLUCIS_LONGUS", "FIBULARIS_TERTIUS", "FIBULARIS_LONGUS",
              "FIBULARIS_BREVIS"):
        assert joints(k) == ["ANKLE_R"], k
    for k in ("FLEXOR_DIGITORUM_LONGUS", "FLEXOR_HALLUCIS_LONGUS"):
        assert joints(k) == ["ANKLE_R", "MTP_R", "TOE_IP_R"], k
    assert joints("TIBIALIS_POSTERIOR") == ["ANKLE_R", "SUBTALAR_R"]
    assert joints("BICEPS_FEMORIS_SHORT") == ["KNEE_R"] and joints("POPLITEUS") == ["KNEE_R"]
    assert joints("PLANTARIS") == ["ANKLE_R", "KNEE_R"]


def test_step2_hip_module_still_loads_alone():
    onto = AnatomyOntology([HIP])
    assert "LB:MUS:GLUTEUS_MEDIUS_R" in onto.entities and "LB:MUS:TIBIALIS_POSTERIOR_R" not in onto.entities
