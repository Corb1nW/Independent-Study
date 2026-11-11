"""Stage D3 checks (D-060): Gait2392's moving knee in the squat mechanics and muscles.

Kinematics and muscles are compared with OpenSim values in tests/data/d3_oracle_reference.json
(tools/make_d2_oracle.py --knee moving); these tests never import OpenSim. The mechanics are
checked by two formulations and identities, as in D1. Passing tests show the stated model is
computed correctly; they do not validate it against measured squats or muscle activity.
"""
import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest

from src import muscles_d2 as m2
from src import squat_d1 as sq
from src import squat_d3 as d3
from tools import run_phase_d3 as d3r

ROOT = Path(__file__).resolve().parents[1]
REF = json.loads((ROOT / "tests" / "data" / "d3_oracle_reference.json").read_text(encoding="utf-8"))
CFG, PARAMS = sq.load_config(ROOT / "config" / "phase_d1_squat.yaml")
G = PARAMS["gravity"]


def _motion_samples(step=10):
    m = sq.Motion(PARAMS["start_angles"], PARAMS["depth_angles"], PARAMS["period"])
    return m(np.linspace(0, PARAMS["period"], int(PARAMS["samples"]))[::step])


# ------------------------------------------------------------------- knee model and data
def test_knee_splines_come_from_the_model_and_reproduce_their_knots():
    knee, used = d3.load_knee(1.0)
    assert used == ["LB-QD:G2392:JOINT:KNEE_R_MOVING"]
    for th, x in zip(knee.sx.x, knee.sx.y):
        assert knee.sx.value(th) == pytest.approx(x, abs=1e-15)
    T0, _, _ = knee.T(0.0)
    T100, _, _ = knee.T(np.radians(100))
    assert 1000 * (T100 - T0) == pytest.approx([6.289864, -21.120820], abs=1e-5)   # ChatGPT note D3-N01


def test_frozen_knee_uses_d1_datum_not_t0():
    """ChatGPT note D3-N02: D1's datum is a linear interpolation, 0.40 / 0.08 mm from the spline's T(0)."""
    frozen, _ = d3.load_knee(1.0, frozen=True)
    moving, _ = d3.load_knee(1.0)
    datum = m2.d1_joints(1.0).knee[:2]
    assert np.array_equal(frozen.T(0.7)[0], datum)
    assert 1000 * (datum - moving.T(0.0)[0]) == pytest.approx([0.401592, -0.080506], abs=1e-6)


def test_simm_spline_second_derivative():
    knee, _ = d3.load_knee(1.0)
    h = 1e-5
    for th in (-1.6, -1.2, -0.5, -0.1, 0.25):
        num = (knee.sx.derivative(th + h) - knee.sx.derivative(th - h)) / (2 * h)
        assert knee.sx.second_derivative(th) == pytest.approx(num, abs=1e-6)


@pytest.mark.parametrize("body", ["female", "male", "gait2392"])
def test_frozen_knee_reproduces_d1_torques(body):
    b = d3.build_body(body, frozen=True)
    r = d3.run(b, PARAMS)
    r1 = sq.run(sq.build_body(body), PARAMS)
    assert np.max(np.abs(r["tau"] - r1["tau"])) < 1e-10
    assert np.nanmax(np.abs(r["cop_x"] - r1["cop_x"])) < 1e-12


def test_thigh_centre_of_mass_converted_once_into_the_femur_frame():
    for body in ("female", "male", "gait2392"):
        b = d3.build_body(body)
        th = b.base.segments["thigh"]
        assert np.allclose(b.c_f, th.com - th.upper)


# ------------------------------------------------------------------- kinematics vs OpenSim
def test_kinematics_match_opensim_with_the_knee_kept():
    assert REF["provenance"]["knee_mode"] == "moving"
    assert REF["provenance"]["matched_model_changes"] == ["ankle_r rotation1 axis -> 0 0 1; rotation3 axis -> 1 0 0",
                                                          "subtalar_angle_r and mtp_angle_r locked at 0"]
    from tools import make_d2_oracle
    import hashlib
    assert REF["provenance"]["matched_model_sha256"] == hashlib.sha256(make_d2_oracle.matched_model_xml("moving")).hexdigest()
    assert len(REF["kinematics"]) == 301
    assert d3r.kinematics_oracle_error(REF) < 1e-9


def test_kinematic_derivatives_by_finite_differences():
    b = d3.build_body("gait2392")
    q, qd, qdd = _motion_samples(25)
    k = d3.kinematics(b, q, qd, qdd)
    h = 1e-5
    for i in range(q.shape[1]):
        kp = d3.kinematics(b, (q[:, i] + h * qd[:, i])[:, None], qd[:, i:i + 1], qdd[:, i:i + 1])
        km = d3.kinematics(b, (q[:, i] - h * qd[:, i])[:, None], qd[:, i:i + 1], qdd[:, i:i + 1])
        for key in ("hip", "com_thigh", "com_hat"):
            vel = (kp[key][0][:, 0] - km[key][0][:, 0]) / (2 * h)
            assert np.allclose(vel, k[key][1][:, i], atol=1e-8)


# ---------------------------------------------------------------------------- mechanics
@pytest.mark.parametrize("body", ["female", "male", "gait2392"])
def test_newton_euler_and_kane_agree_with_the_moving_knee(body):
    b = d3.build_body(body)
    q, qd, qdd = _motion_samples(5)
    assert np.max(np.abs(d3.inverse_dynamics(b, q, qd, qdd, G)["tau"] - d3.kane(b, q, qd, qdd, G)["tau"])) < 1e-8


def test_kane_matches_an_independent_finite_difference_projection():
    """Guards the knee translation term (a first Newton-Euler version had it with the wrong sign)."""
    b = d3.build_body("gait2392")
    q, qd, qdd = _motion_samples(30)
    kn = d3.kane(b, q, qd, qdd, G)["tau"]

    def coms(qq):
        return np.concatenate([p for p, _, _ in d3._jacobians(b, qq)])
    for c in range(q.shape[1]):
        h = 1e-5
        x0 = coms(q[:, c])
        J = np.column_stack([(coms(q[:, c] + h * e) - coms(q[:, c] - h * e)) / (2 * h) for e in np.eye(3)])
        a = J @ qdd[:, c] + (coms(q[:, c] + h * qd[:, c]) - 2 * x0 + coms(q[:, c] - h * qd[:, c])) / h ** 2
        tau = J.T @ (np.repeat(b.mass, 2) * (a - np.tile([0, -G], 3))) + sq.B_MAP.T @ (np.array(b.inertia) * (sq.B_MAP @ qdd[:, c]))
        assert np.max(np.abs(tau - kn[:, c])) < 1e-3       # finite-difference accuracy
    assert np.max(np.abs(d3.inverse_dynamics(b, q, qd, qdd, G)["knee_translation_term"])) > 1.0   # the term matters


def test_mechanics_checks_pass_for_gait2392():
    b = d3.build_body("gait2392")
    r = d3.run(b, PARAMS)
    c = d3.check_residuals(b, PARAMS, r)
    tol = d3r.load_config()["tolerances"]
    assert c["newton_euler_vs_kane_N_m"] < tol["newton_euler_vs_kane_N_m"]
    assert c["static_virtual_work_N_m"] < tol["static_virtual_work_N_m"]
    assert c["energy_W"] < tol["energy_W"]
    assert c["newton_identity_per_leg_N"] < tol["newton_identity_N"]
    assert c["local_one_step_rad_at_1ms"] < tol["local_one_step_rad_at_1ms"]
    assert c["short_horizon_0p1s_rad_at_1ms"] < tol["short_horizon_0p1s_rad_at_1ms"]
    assert r["contact"]["feasible"]


# ------------------------------------------------------------------------------ muscles
ACTS, _ = m2.load_actuators(1.0)
BY = {a.name: a for a in ACTS}
JM = dataclasses.replace(m2.d1_joints(1.0), moving_knee=d3.load_knee(1.0)[0])


@pytest.mark.parametrize("kind", ["d1_sample", "spline_knot", "switch_side", "switch_edge"])
def test_moving_knee_muscle_geometry_matches_opensim(kind):
    rows = [g for g in REF["geometry"] if g["kind"] == kind]
    assert rows
    assert check_reference(REF, "moving") == []       # full, ordered coverage first (ChatGPT note D3-N03)
    for g in rows:
        q = np.array(g["q"])
        for n in REF["actuators"]:
            L, R, _ = m2.path(BY[n], q, JM)
            assert abs(L - g["length_m"][n]) < 1e-9
            assert np.max(np.abs(R - np.array(g["moment_arm_m"][n]))) < 1e-9


def test_moving_knee_forces_match_opensim():
    assert check_reference(REF, "moving") == []       # full, ordered coverage first (ChatGPT note D3-N03)
    for f in REF["forces"]:
        q, qd = np.array(f["q"]), np.array(f["qdot"])
        for n, v in f["values"].items():
            a = BY[n]
            L, R, _ = m2.path(a, q, JM)
            st = m2.fiber_state(a, L, -R @ qd)
            F = f["activation"] * m2.unit_tendon_force(a, st) + (m2.passive_tendon_force(a, st) if f["passive"] else 0)
            assert abs(F - v["tendon_force_N"]) < 1e-8


def test_moving_knee_moment_arms_by_finite_differences():
    q = np.array([0.4, 1.2, 0.8])
    for a in ACTS:
        _, R, _ = m2.path(a, q, JM)
        h = 1e-6
        num = [-(m2.path(a, q + h * e, JM)[0] - m2.path(a, q - h * e, JM)[0]) / (2 * h) for e in np.eye(3)]
        assert np.allclose(num, R, atol=1e-8)


def test_fixed_knee_geometry_unchanged_when_no_moving_knee():
    J = m2.d1_joints(1.0)
    q = np.array([0.4, 1.2, 0.8])
    assert J.moving_knee is None
    assert np.array_equal(J.knee_at(q[1])[0], J.knee)


# ------------------------------------------------------------------------------- runner
def test_d3_configuration_guards(tmp_path):
    import yaml
    cfg = yaml.safe_load(d3r.CONFIG.read_text(encoding="utf-8"))
    assert d3r.load_config()["knee_model"] == "gait2392_moving"
    for mutate in (lambda c: c.update(knee_model="rolling_contact"),
                   lambda c: c["tolerances"].pop("kinematics_oracle_m"),
                   lambda c: c["tolerances"].update(energy_W=0.0)):
        bad = yaml.safe_load(yaml.safe_dump(cfg))
        mutate(bad)
        p = tmp_path / "bad.yaml"
        p.write_text(yaml.safe_dump(bad), encoding="utf-8")
        with pytest.raises(ValueError):
            d3r.load_config(p)


def test_d3_exit_code_fails_only_on_verification():
    good = {"mechanics_verification": "passed", "kinematics_verification": "passed", "optimizer_verification": "passed",
            "contact_feasibility": "flagged", "muscle_feasibility": "flagged", "force_law_domain": "flagged"}
    assert d3r.exit_code({"status": good}) == 0
    for k in ("mechanics_verification", "kinematics_verification", "optimizer_verification"):
        assert d3r.exit_code({"status": dict(good, **{k: "failed"})}) == 1


# ----------------------------------------------- oracle coverage (ChatGPT note D3-N03)
from tools.oracle_coverage import check_reference  # noqa: E402


@pytest.mark.parametrize("path,mode", [("tests/data/d3_oracle_reference.json", "moving"),
                                       ("tests/data/d2_oracle_reference.json", "fixed")])
def test_committed_references_cover_exactly_the_expected_states(path, mode):
    ref = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert check_reference(ref, mode) == []


def _tampered(change):
    import copy
    ref = copy.deepcopy(REF)
    change(ref)
    return ref


@pytest.mark.parametrize("label,change", [
    ("301 copies of the upright row (the reviewer's probe)",
     lambda r: r.update(kinematics=[dict(r["kinematics"][0], index=i) for i in range(301)])),
    ("truncated kinematics", lambda r: r.update(kinematics=r["kinematics"][:300])),
    ("reordered kinematics", lambda r: r["kinematics"].reverse()),
    ("non-finite position", lambda r: r["kinematics"][7]["hip_m"].__setitem__(1, float("nan"))),
    ("truncated geometry", lambda r: r.update(geometry=r["geometry"][:5])),
    ("geometry pose edited", lambda r: r["geometry"][40]["q"].__setitem__(1, 0.5)),
    ("missing actuator in geometry", lambda r: r["geometry"][3]["length_m"].pop("soleus_r")),
    ("forces truncated", lambda r: r.update(forces=r["forces"][:-1])),
    ("force value non-finite", lambda r: r["forces"][2]["values"]["vas_lat_r"].__setitem__("tendon_force_N", float("inf"))),
    ("unmodified rows thinned", lambda r: r.update(unmodified_geometry=r["unmodified_geometry"][::2])),
    ("fixed-knee reference passed as moving", lambda r: r["provenance"].update(knee_mode="fixed")),
    ("matched model hash stale", lambda r: r["provenance"].update(matched_model_sha256="0" * 64)),
    ("oracle tool hash stale", lambda r: r["provenance"].update(tool_sha256="0" * 64)),
])
def test_tampered_reference_fails_coverage_and_the_runner_check(label, change):
    bad = _tampered(change)
    assert check_reference(bad, "moving"), label
    assert d3r.kinematics_oracle_error(bad) == float("inf"), label


def test_kinematics_rows_follow_the_d1_motion_exactly():
    m = sq.Motion(PARAMS["start_angles"], PARAMS["depth_angles"], PARAMS["period"])
    q, _, _ = m(np.linspace(0, PARAMS["period"], int(PARAMS["samples"])))
    assert [r["index"] for r in REF["kinematics"]] == list(range(q.shape[1]))
    assert np.array_equal(np.array([r["q"] for r in REF["kinematics"]]).T, q)


# ----------------------------------- ankle and foot simplification size (ChatGPT finding D3-B03)
def test_ankle_foot_simplification_size_is_reported_and_cross_checked():
    r = d3r.ankle_foot_simplification_size(ACTS, JM, REF)
    assert r["reported_not_pass_fail"] is True
    assert set(r["by_actuator"]) == set(REF["actuators"])
    assert r["largest_by_coordinate"]["ankle"] == {"actuator": "tib_ant_r", "mm": pytest.approx(4.393, abs=1e-3)}
    assert r["largest_by_coordinate"]["knee"]["actuator"] == "lat_gas_r"
    assert r["largest_by_coordinate"]["knee"]["mm"] == pytest.approx(0.0188, abs=1e-4)
    assert r["largest_by_coordinate"]["hip"]["mm"] < 1e-3            # the hip is not affected by ankle or foot changes
    # the implementation-based figures equal the OpenSim-only comparison of the two models
    assert r["opensim_only_cross_check"]["largest_difference_from_implementation_based_mm"] < 1e-3


def test_knee_is_identical_in_both_models_of_the_comparison():
    """What 8f measures in D3 is only the ankle and foot: the knee XML is the same in the matched copy and the source."""
    import xml.etree.ElementTree as ET
    from tools import make_d2_oracle as oracle
    knee = lambda root: ET.tostring([j for j in root.iter("CustomJoint") if j.get("name") == "knee_r"][0])  # noqa: E731
    assert knee(ET.fromstring(oracle.matched_model_xml("moving"))) == knee(ET.parse(oracle.OSIM).getroot())


# ChatGPT finding D3-B02: each knee mode of the viewer shows its own manifest's assumptions.
from tools import build_d2_page as page  # noqa: E402

D2_MANIFEST = json.loads((ROOT / "results" / "phase_d" / "2026-11-10_d2_muscle_runs_7ac0f2d.json").read_text(encoding="utf-8"))
FIXED_ONLY = ("fixed-centre knee", "inertial torques are kept")


def _declared():
    cfg = d3r.load_config()
    d2_cfg, _ = d3r.d2r.load_config(ROOT / cfg["d2_config"])
    return cfg, d2_cfg, d3r.declared_assumptions(cfg, d2_cfg)


def test_declared_assumptions_restate_every_fixed_knee_item_of_d2():
    cfg, d2_cfg, declared = _declared()
    assert [a["source"] for a in declared] == ["D3"] * len(cfg["assumptions"]) + ["D2"] * len(d2_cfg["assumptions"])
    assert [a["number"] for a in declared if a["source"] == "D2"] == list(range(1, len(d2_cfg["assumptions"]) + 1))
    # The D2 items that describe the fixed knee are exactly the ones restated, and none survives in the D3 list.
    fixed_items = {k for k, t in enumerate(d2_cfg["assumptions"], 1) if any(ph in t for ph in FIXED_ONLY)}
    assert fixed_items == set(cfg["d2_assumption_restatements"]) == {1, 2}
    assert not [a for a in declared if any(ph in a["text"] for ph in FIXED_ONLY)]
    assert {a["number"] for a in declared if a.get("restated_for_stage_d3")} == fixed_items
    # Unrestated D2 items are carried over word for word (numbering prefix removed).
    for a, t in zip([a for a in declared if a["source"] == "D2"], d2_cfg["assumptions"]):
        if not a["restated_for_stage_d3"]:
            assert t.endswith(a["text"])
    assert any("D1's motion q(t) is retained" in a["text"] and "moving knee" in a["text"] for a in declared)


def test_declared_assumptions_reject_a_restatement_of_a_missing_item():
    cfg, d2_cfg, _ = _declared()
    with pytest.raises(ValueError):
        d3r.declared_assumptions(dict(cfg, d2_assumption_restatements={len(d2_cfg["assumptions"]) + 1: "x"}), d2_cfg)


def test_viewer_data_takes_each_modes_assumptions_from_its_own_manifest():
    _, _, declared = _declared()
    fixed = page.compact(D2_MANIFEST)
    assert fixed["knee"] == "fixed"
    assert [a["text"] for a in fixed["assumptions"]] == [
        t.split(". ", 1)[1] if t.split(". ", 1)[0].isdigit() else t for t in D2_MANIFEST["configuration"]["assumptions"]]
    assert any("fixed-centre knee" in a["text"] for a in fixed["assumptions"])
    d3_manifest = json.loads((ROOT / "results" / "phase_d" / "2026-11-10_d3_moving_knee_runs_525e2c3.json")
                             .read_text(encoding="utf-8"))
    with pytest.raises(KeyError):          # a D3 manifest without its own list must not borrow D2's
        page.compact(d3_manifest)
    moving = page.compact(dict(d3_manifest, declared_assumptions=declared))
    assert moving["knee"] == "moving"
    assert [a["text"] for a in moving["assumptions"]] == [a["text"] for a in declared]
    assert not [a for a in moving["assumptions"] if any(ph in a["text"] for ph in FIXED_ONLY)]
    assert [a["label"] for a in moving["assumptions"]][:2] == ["D3-1", "D3-2"]
    assert "D2-1 (restated)" in [a["label"] for a in moving["assumptions"]]
    html = page.render(D2_MANIFEST, dict(d3_manifest, declared_assumptions=declared))
    assert "V.assumptions" in html and "esc(a.text)" in html
