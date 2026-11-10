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
    for g in rows:
        q = np.array(g["q"])
        for n in REF["actuators"]:
            L, R, _ = m2.path(BY[n], q, JM)
            assert abs(L - g["length_m"][n]) < 1e-9
            assert np.max(np.abs(R - np.array(g["moment_arm_m"][n]))) < 1e-9


def test_moving_knee_forces_match_opensim():
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
