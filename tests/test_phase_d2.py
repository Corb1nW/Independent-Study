"""Stage D2 checks (D-059 item 8 with Amendments 1 and 2).

8a geometry against the OpenSim oracle; 8b moment arms by differentiation and virtual work;
8c the assembled force law against the oracle and an independent hand fixture; 8d the two-stage
optimizer (KKT, second solver, Amendment 2 fixtures). The oracle values are read from
tests/data/d2_oracle_reference.json, written by tools/make_d2_oracle.py with OpenSim 4.6;
these tests never import OpenSim. Passing tests show the code computes what D-059 specifies;
they say nothing about whether real muscles behave this way.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

from src import muscles_d2 as m2
from src.ontology import AnatomyOntology

ROOT = Path(__file__).resolve().parents[1]
REF = json.loads((ROOT / "tests" / "data" / "d2_oracle_reference.json").read_text(encoding="utf-8"))
ACTS, CONSUMED = m2.load_actuators(1.0)
BY_NAME = {a.name: a for a in ACTS}
JOINTS = m2.d1_joints(1.0)
LENGTH_TOL = 1e-9          # m (D-059 8a)
ARM_TOL = 1e-9             # m
FORCE_TOL = 1e-8           # N
INTERMEDIATE_TOL = 1e-12   # m, rad, m/s and dimensionless


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ------------------------------------------------------------------ inputs and provenance
def test_fourteen_actuators_in_d059_order_with_d056_reading():
    assert [a.name for a in ACTS] == REF["actuators"]
    assert len(ACTS) == 14
    assert all(a.v_max == 10.0 for a in ACTS)


def test_oracle_reference_matches_the_current_inputs():
    """The reference was made from the committed model, the current tool and the current D1-matched copy."""
    prov = REF["provenance"]
    assert prov["source_model_sha256"] == _sha(ROOT / "sources/vendor/opensim-models/gait2392_millard2012muscle.osim")
    from tools import make_d2_oracle
    assert prov["matched_model_sha256"] == hashlib.sha256(make_d2_oracle.matched_model_xml()).hexdigest()
    assert prov["opensim_version"].startswith("4.6")
    assert prov["overrides"]["fiber_damping"] == 0.0 and prov["overrides"]["ignore_tendon_compliance"] is True


def test_curve_constants_come_from_the_vendored_header():
    assert _sha(m2.HEADER) == "c430bfc2a69996e6eb5700ea6bd7bc80fcd5ea9bfc6b234e23f05dc7bd8ff3e6"
    assert m2.C["d2"] == -8.149 and m2.C["b31"] == 0.162384573599574
    assert m2.f_active(1.0) == pytest.approx(1.0, abs=1e-12)
    assert m2.f_velocity(-1.0) == pytest.approx(0.0, abs=1e-12)
    assert m2.f_velocity(0.0) == pytest.approx(1.0, abs=1e-12)
    assert m2.f_passive(m2.MIN_NORM_FIBER_LENGTH) == pytest.approx(0.0, abs=1e-15)
    assert (m2.MIN_NORM_FIBER_LENGTH, m2.MAX_NORM_FIBER_LENGTH) == (0.2, 1.8)


def test_muscle_inputs_pass_the_traceability_gate():
    reports = m2.muscle_traceability(CONSUMED)
    assert set(reports) == {"muscles_gait2392.yaml"}


def test_actuator_entities_represent_existing_muscles_and_hip_module_stands_alone():
    onto = AnatomyOntology([ROOT / "ontology/hip.yaml", ROOT / "ontology/lower_limb_sagittal.yaml"])
    acts = {k: v for k, v in onto.entities.items() if v["class"] == "ModelActuator"}
    assert len(acts) == 14
    for v in acts.values():
        assert onto.entities[v["represents"]]["class"] == "SkeletalMuscle"
    assert {a.entity for a in ACTS} == {v["represents"] for v in acts.values()}
    AnatomyOntology(ROOT / "ontology/hip.yaml")   # still loads without the new module


# --------------------------------------------------------------------------- SimmSpline
def test_simm_spline_reproduces_knots_and_extrapolates_linearly():
    x = [-2.0944, -1.5708, -1.0472, -0.5236, 0.0, 0.5236, 2.0944]
    y = [0.01, 0.02, 0.031, 0.036, 0.056, 0.061, 0.063]
    s = m2.SimmSpline(x, y)
    for xi, yi in zip(x, y):
        assert s.value(xi) == pytest.approx(yi, abs=1e-15)
    h = 1e-6
    for a in (-1.9, -0.8, -0.1, 0.3, 1.7):
        assert s.derivative(a) == pytest.approx((s.value(a + h) - s.value(a - h)) / (2 * h), abs=1e-7)
    assert s.value(-3.0) == pytest.approx(y[0] + (-3.0 - x[0]) * s.b[0])


# ------------------------------------------------------------------- 8a geometry vs oracle
@pytest.mark.parametrize("kind", ["d1_sample", "spline_knot", "switch_side"])
def test_lengths_and_moment_arms_match_opensim(kind):
    rows = [g for g in REF["geometry"] if g["kind"] == kind]
    assert rows
    for g in rows:
        q = np.array(g["q"])
        for name in REF["actuators"]:
            L, R, _ = m2.path(BY_NAME[name], q, JOINTS)
            assert abs(L - g["length_m"][name]) < LENGTH_TOL, (name, kind)
            assert np.max(np.abs(R - np.array(g["moment_arm_m"][name]))) < ARM_TOL, (name, kind)


def test_every_conditional_switch_in_d1_range_is_checked_on_both_sides():
    sides = [g for g in REF["geometry"] if g["kind"] == "switch_side"]
    edges = {round(g["edge_knee_angle_gait2392"], 9) for g in sides}
    assert len(edges) == 6          # 8 switch points; gastrocnemius pair and vastus medialis/lateralis share edges
    for e in edges:
        assert {g["side"] for g in sides if round(g["edge_knee_angle_gait2392"], 9) == e} == \
            {"flexion_side", "extension_side"}


def test_path_length_jumps_at_switches_are_reported_not_smoothed():
    """Amendment 2: L is piecewise continuous; the jump is the length difference of the two active sets."""
    q = None
    for g in REF["geometry"]:
        if g["kind"] == "switch_side" and abs(g["edge_knee_angle_gait2392"] + 0.785398 + 1e-5) < 1e-9:
            q = np.array(g["q"]); break
    a = BY_NAME["med_gas_r"]
    edge = 0.785398 + 1e-5                                   # D1 knee angle of the widened edge
    ratio = q / q[1]
    inside = m2.path(a, ratio * (edge - 1e-9), JOINTS)[0]
    outside = m2.path(a, ratio * (edge + 1e-9), JOINTS)[0]
    assert abs(inside - outside) > 1e-4                      # about 0.35 mm on the D1-matched geometry


def test_uniform_scaling_scales_lengths_and_moment_arms():
    s = 0.9639
    acts_s, _ = m2.load_actuators(s)
    js = m2.d1_joints(s)
    q = np.array([0.3, 0.9, 0.6])
    for a, b in zip(ACTS, acts_s):
        L1, R1, _ = m2.path(a, q, JOINTS)
        Ls, Rs, _ = m2.path(b, q, js)
        assert Ls == pytest.approx(s * L1, rel=1e-12)
        assert np.allclose(Rs, s * R1, rtol=1e-12, atol=1e-15)
        assert b.l_opt == pytest.approx(s * a.l_opt) and b.l_ts == pytest.approx(s * a.l_ts) and b.f0 == a.f0


# --------------------------------------------------------- 8b differentiation, virtual work
def _branch_safe(a, q, h):
    return m2.branch_active_set(a, q) == m2.branch_active_set(a, q + h) == m2.branch_active_set(a, q - h)


def test_moment_arms_equal_minus_dL_dq_with_step_convergence_away_from_switches():
    rng = np.random.default_rng(7)
    for _ in range(20):
        q = rng.uniform([0.0, 0.0, 0.0], [0.69, 1.74, 1.29])
        for a in ACTS:
            _, R, _ = m2.path(a, q, JOINTS)
            for j in range(3):
                e = np.zeros(3); e[j] = 1.0
                errs = []
                for h in (1e-3, 5e-4):
                    if not _branch_safe(a, q, h * e):
                        break
                    num = -(m2.path(a, q + h * e, JOINTS)[0] - m2.path(a, q - h * e, JOINTS)[0]) / (2 * h)
                    errs.append(abs(num - R[j]))
                if len(errs) == 2 and errs[0] > 1e-12:
                    assert errs[1] < errs[0] / 3.0           # central difference: error about 4x smaller
                if errs:
                    assert errs[-1] < 1e-7


def test_one_sided_differences_at_switch_sides_use_that_sides_branch():
    for g in (g for g in REF["geometry"] if g["kind"] == "switch_side"):
        q = np.array(g["q"])
        ratio = q / q[1]
        direction = 1.0 if g["side"] == "flexion_side" else -1.0
        for a in ACTS:
            _, R, _ = m2.path(a, q, JOINTS)
            h = 1e-5 * direction
            q2 = q + h * ratio
            if m2.branch_active_set(a, q) != m2.branch_active_set(a, q2):
                continue
            num = -(m2.path(a, q2, JOINTS)[0] - m2.path(a, q, JOINTS)[0]) / h
            assert num == pytest.approx(R @ ratio, abs=1e-6)


def test_virtual_work_identity_within_a_branch():
    """-F dL/dt equals the sum of joint powers F R_j qdot_j for each actuator."""
    q, qd = np.array([0.4, 1.0, 0.7]), np.array([0.3, -0.8, 0.5])
    for a in ACTS:
        _, R, _ = m2.path(a, q, JOINTS)
        h = 1e-6
        if not _branch_safe(a, q, h * qd):
            continue
        dLdt = (m2.path(a, q + h * qd, JOINTS)[0] - m2.path(a, q - h * qd, JOINTS)[0]) / (2 * h)
        F = 1000.0
        assert -F * dLdt == pytest.approx(F * (R @ qd), abs=1e-6)


# -------------------------------------------------------- 8c assembled force law vs oracle
def test_assembled_force_and_intermediates_match_opensim():
    assert {f["activation"] for f in REF["forces"]} == {0.0, 0.37, 1.0}
    assert {f["passive"] for f in REF["forces"]} == {False, True}
    shortening = lengthening = 0
    for f in REF["forces"]:
        q, qd = np.array(f["q"]), np.array(f["qdot"])
        for name, v in f["values"].items():
            a = BY_NAME[name]
            L, R, _ = m2.path(a, q, JOINTS)
            st = m2.fiber_state(a, L, -R @ qd)
            assert not st["flags"]
            F = f["activation"] * m2.unit_tendon_force(a, st)
            if f["passive"]:
                F += m2.passive_tendon_force(a, st)
            for key, mine in (("fiber_length_m", st["l_m"]), ("pennation_rad", st["alpha"]),
                              ("fiber_velocity_m_s", st["v_m"]), ("normalized_fiber_velocity", st["v_norm"]),
                              ("lengthening_speed_m_s", -R @ qd)):
                assert abs(mine - v[key]) < INTERMEDIATE_TOL, (name, key)
            assert abs(F - v["tendon_force_N"]) < FORCE_TOL, name
            if not f["passive"]:
                assert v["passive_fiber_force_N"] == 0.0          # baseline: no passive, no damping force
            shortening += st["v_norm"] < -1e-3
            lengthening += st["v_norm"] > 1e-3
    assert shortening > 0 and lengthening > 0


def test_baseline_force_is_linear_in_activation_with_one_cos_alpha():
    a = BY_NAME["vas_lat_r"]
    L, R, _ = m2.path(a, np.array([0.4, 1.0, 0.7]), JOINTS)
    st = m2.fiber_state(a, L, 0.02)
    unit = m2.unit_tendon_force(a, st)
    assert unit == pytest.approx(a.f0 * m2.f_active(st["l_norm"]) * m2.f_velocity(st["v_norm"]) * st["cos_alpha"])
    assert st["v_m"] == pytest.approx(st["cos_alpha"] * 0.02)


def _fixture_actuator():
    """ChatGPT's hand fixture (D-059 Amendment 1, item 8c): F0 1000 N, l_opt 0.1 m, alpha0 30 deg, v_max 10/s."""
    return m2.Actuator("fixture", "none", 1000.0, 0.1, 0.2, math.pi / 6, 10.0)


def test_independent_hand_fixture():
    a = _fixture_actuator()
    L = a.l_ts + a.l_opt * math.cos(a.alpha0)          # fiber at optimal length
    rest = m2.fiber_state(a, L, 0.0)
    assert 0.5 * m2.unit_tendon_force(a, rest) == pytest.approx(433.01270189221935, abs=1e-9)
    moving = m2.fiber_state(a, L, 0.05)
    assert moving["v_norm"] == pytest.approx(0.04330127018922194, abs=1e-15)
    assert 0.5 * m2.unit_tendon_force(a, moving) == pytest.approx(475.94546724506705, abs=1e-9)


@pytest.mark.parametrize("bound,flag", [("length_low", m2.FLAG_LENGTH), ("length_high", m2.FLAG_LENGTH),
                                        ("velocity_low", m2.FLAG_VELOCITY), ("velocity_high", m2.FLAG_VELOCITY),
                                        ("x", m2.FLAG_X)])
def test_domain_policy_flags_and_excludes_never_extrapolates(bound, flag):
    a = _fixture_actuator()
    h = a.l_opt * math.sin(a.alpha0)

    def L_for(l_norm):
        return a.l_ts + math.sqrt((l_norm * a.l_opt) ** 2 - h * h)
    eps = 1e-9
    cos_opt = math.cos(a.alpha0)
    cases = {"length_low": ((L_for(0.6), 0.0), None), "length_high": ((L_for(1.8 - eps), 0.0), (L_for(1.8 + eps), 0.0)),
             "velocity_low": ((L_for(1.0), -(1 - eps) * a.v_max * a.l_opt / cos_opt),
                              (L_for(1.0), -(1 + eps) * a.v_max * a.l_opt / cos_opt)),
             "velocity_high": ((L_for(1.0), (1 - eps) * a.v_max * a.l_opt / cos_opt),
                               (L_for(1.0), (1 + eps) * a.v_max * a.l_opt / cos_opt)),
             "x": ((a.l_ts + 1e-6, 0.0), (a.l_ts - 1e-6, 0.0))}
    if bound == "length_low":          # constant thickness: l_norm >= sin(alpha0) = 0.5 > 0.2, so test the rule directly
        st = m2.fiber_state(a, *cases[bound][0])
        assert not st["flags"]
        return
    inside, outside = cases[bound]
    assert not m2.fiber_state(a, *inside)["flags"]
    st = m2.fiber_state(a, *outside)
    assert flag in st["flags"]
    assert m2.unit_tendon_force(a, st) == 0.0 and m2.passive_tendon_force(a, st) == 0.0


def test_non_finite_state_fails():
    with pytest.raises(FloatingPointError):
        m2.fiber_state(_fixture_actuator(), float("nan"), 0.0)


# ------------------------------------------------------------------------ 8d optimizer
def test_two_joint_fixture_is_feasible_under_the_amended_rule():
    """ChatGPT's D2-R01 fixture: the minimum-L2 reserve is flagged; the L-inf rule finds 0.95 N m at a = 0.5."""
    rec = m2.recruit(np.array([[4.0], [-1.0]]), np.array([2.95, 0.45]))
    assert rec.t_star == pytest.approx(0.95, abs=1e-12)
    assert rec.t_star <= 1.0
    assert rec.activation[0] == pytest.approx(0.5, abs=1e-6)
    assert np.max(np.abs(rec.reserve)) <= rec.band + 1e-12


def test_fourteen_actuator_fixture_needs_no_reserve():
    rec = m2.recruit(np.full((1, 14), 0.1), np.array([1.4]))
    assert rec.t_star == pytest.approx(0.0, abs=1e-12)
    assert np.min(rec.activation) > 1 - 1e-4
    assert abs(rec.reserve[0]) <= 1e-6 + 1e-12            # within the numerical band (note D2-A2-N01)


def test_signed_shortfall_is_flagged_by_magnitude():
    rec = m2.recruit(np.zeros((2, 1)), np.array([-2.0, 0.5]))
    assert rec.t_star == pytest.approx(2.0)
    assert not rec.t_star <= 1.0
    assert rec.reserve[0] == pytest.approx(-2.0)          # a -10 or -2 N m reserve can never pass a one-sided test
    assert -10.0 <= 1.0 and not abs(-10.0) <= 1.0


def test_infeasible_case_with_known_t_star_and_disclosed_band_use():
    """One knee extensor of capacity 50 N m against 60 N m, and an ankle actuator against 5 N m.
    t* = 10 N m. Stage 2 then minimizes effort within |r| <= t*, so the non-limiting ankle carries
    its 5 N m as reserve and its actuator stays off (Amendment 2: reserves at non-limiting joints may
    rise up to t*, never above)."""
    Cm = np.array([[10.0, 0.0], [0.0, -50.0]])
    rec = m2.recruit(Cm, np.array([5.0, -60.0]))
    assert rec.t_star == pytest.approx(10.0, abs=1e-9)
    assert rec.activation[1] == pytest.approx(1.0, abs=1e-6)
    assert rec.activation[0] == pytest.approx(0.0, abs=1e-9)
    assert rec.reserve[0] == pytest.approx(5.0, abs=1e-9)
    assert np.max(np.abs(rec.reserve)) <= rec.band + 1e-12


def test_kkt_conditions_and_second_solver_on_random_problems():
    rng = np.random.default_rng(3)
    for _ in range(25):
        Cm = rng.normal(0.0, 40.0, (3, 14))
        tau = Cm @ rng.uniform(0, 1, 14) + rng.normal(0, 5, 3)
        rec = m2.recruit(Cm, tau)
        for stage in ("stage1", "stage2"):
            k = rec.kkt[stage]
            assert k["stationarity"] < 1e-8 and k["dual_feasibility"] < 1e-8
            assert k["complementarity"] < 1e-8 and k["primal"] < 1e-8
        assert rec.solvers["t_star_difference"] < 1e-7
        assert rec.solvers["activation_difference"] < 1e-5
        assert np.max(np.abs(rec.reserve)) <= rec.band + 1e-9


# ------------------------------------------------------------------ runner and page
from tools import run_phase_d2 as d2r  # noqa: E402


def test_d2_configuration_is_labeled_and_declares_the_baseline():
    cfg, params = d2r.load_config()
    assert params["epsilon_reserve"] == 1.0 and params["solver_band_delta"] == 1e-6
    assert cfg["baseline_force_law"]["fiber_damping"] == 0.0
    assert len(cfg["assumptions"]) == 15


def test_d2_configuration_rejects_an_unlabeled_or_damped_baseline(tmp_path):
    import yaml
    cfg = yaml.safe_load(d2r.CONFIG.read_text(encoding="utf-8"))
    bad = dict(cfg, baseline_force_law=dict(cfg["baseline_force_law"], fiber_damping=0.1))
    p = tmp_path / "bad.yaml"; p.write_text(yaml.safe_dump(bad), encoding="utf-8")
    with pytest.raises(ValueError):
        d2r.load_config(p)
    cfg["parameters"]["epsilon_reserve"].pop("rationale")
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(ValueError):
        d2r.load_config(p)


def test_exit_code_fails_only_on_verification_not_on_flags():
    good = {"mechanics_verification": "passed", "d1_consistency": "passed", "optimizer_verification": "passed",
            "muscle_feasibility": "flagged", "force_law_domain": "flagged", "contact_feasibility": "feasible"}
    assert d2r.exit_code({"status": good}) == 0
    for key in ("mechanics_verification", "d1_consistency", "optimizer_verification"):
        assert d2r.exit_code({"status": dict(good, **{key: "failed"})}) == 1


def test_switch_jumps_are_reported_for_every_switch_in_range():
    import numpy as np
    jumps = d2r.switch_jumps(ACTS, JOINTS, np.array([0.6981317007977318, 1.7453292519943295, 1.2915436464758039]))
    assert len(jumps) == 8
    assert all(abs(j["length_with_point_minus_without_mm"]) > 0 for j in jumps)


def test_smallest_reserve_diagnostic_identifies_the_limiting_joint():
    Cm = np.array([[10.0, 0.0], [0.0, -50.0]])
    tau = np.array([5.0, -60.0])
    rec = m2.recruit(Cm, tau)
    needed = m2.smallest_reserve_per_joint(Cm, tau, rec.band)
    assert needed[0] == pytest.approx(0.0, abs=1e-9) and needed[1] == pytest.approx(10.0, abs=1e-6)


def test_compliant_tendon_equilibrium_balances_forces():
    from tools import sensitivity_d2 as sens
    a = BY_NAME["soleus_r"]
    L = a.l_ts + 1.3 * a.l_opt
    c = sens.compliant_equilibrium(a, 0.2, L)
    assert c["compliant"]["equilibrium_residual_N"] < 1e-6
    assert c["compliant"]["normalized_fiber_length"] < c["rigid"]["normalized_fiber_length"]
    assert sens.tendon_multiplier(1.049, 0.049) == pytest.approx(1.0, abs=1e-12)
    assert sens.tendon_multiplier(1.0, 0.049) == pytest.approx(0.0, abs=1e-12)
