"""Stage D1 (D-058, Amendments 1 and 2): data, ontology and the mechanics checks.

The mechanics checks VERIFY that the idealized model's equations are solved correctly.
They do not validate the model against measured squats (Amendment 1, A3).

Tolerances (config/phase_d1_squat.yaml) and why they are what they are: all compared
quantities are computed in double precision from the same exact (closed-form) motion,
so differences come only from rounding. Observed residuals are about 1e-13 N*m on
torques of about 100 N*m. Tolerances of 1e-8 (1e-9 for the static oracle, 1e-10 for
the closed forms) leave several orders of magnitude for platform differences while
staying far below the smallest physical term that a modeling error would change (for
example a segment's I*alpha, of order 1e-2 N*m).
"""
from copy import deepcopy
from hashlib import sha256
import math
from pathlib import Path

import numpy as np
import pytest
import yaml

from src import squat_d1 as sq
from src.ontology import AnatomyOntology
from src.quantitative import QuantitativeSchema
from tools import build_segment_datasets as bsd

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "phase_d1_squat.yaml"
SCHEMA = ROOT / "ontology" / "quantitative_schema.yaml"
G = 9.80665
CFG, PARAMS = sq.load_config(CONFIG)
TOL = CFG["tolerances"]
BODIES = ("female", "male", "gait2392")


@pytest.fixture(scope="module")
def schema():
    return QuantitativeSchema(SCHEMA)


@pytest.fixture(scope="module")
def bodies(schema):
    return {name: sq.build_body(name, schema) for name in BODIES}


@pytest.fixture(scope="module")
def motion():
    return sq.Motion(PARAMS["start_angles"], PARAMS["depth_angles"], PARAMS["period"])


def samples(motion, n=301):
    return motion(np.linspace(0, motion.period, n))


# ---------------------------------------------------------------- sources and data
def test_vendored_files_match_recorded_hashes():
    readme = (ROOT / "sources" / "vendor" / "README.md").read_text(encoding="utf-8")
    for rel in ("opensim-models/gait2392_millard2012muscle.osim", "bmc/BSPfemale_ZdeLeva.txt", "bmc/BSPmale_ZdeLeva.txt"):
        digest = sha256((ROOT / "sources" / "vendor" / rel).read_bytes()).hexdigest()
        assert digest in readme, f"{rel}: hash {digest} not recorded in sources/vendor/README.md"


def test_datasets_regenerate_exactly_from_vendored_sources():
    for name, builder in bsd.DATASETS.items():
        committed = (ROOT / "ontology" / "quantitative_data" / name).read_text(encoding="utf-8")
        assert committed == bsd.render(builder), f"{name} differs from its generator; rerun the tool"


def test_de_leva_values_equal_the_source_file(schema):
    data = schema.load_dataset(ROOT / "ontology" / "quantitative_data" / "segments_de_leva_1996.yaml")
    for sex, path in bsd.BMC.items():
        rows = bsd.read_bmc(path)
        S = sex[0].upper()
        assert data["observations"][f"LB-QD:DELEVA:{S}:THIGH:MASS_FRACTION"]["value"] == float(rows["Thigh"]["mass"])
        assert data["observations"][f"LB-QD:DELEVA:{S}:SHANK:CENTER_OF_MASS_FRACTION"]["value"] == float(rows["Shank"]["com"])
        assert data["observations"][f"LB-QD:DELEVA:{S}:THIGH:RADIUS_OF_GYRATION_FRACTION"]["value"] == float(rows["Thigh"]["rg_trans"])


def test_gait2392_values_equal_the_model_file(schema):
    import xml.etree.ElementTree as ET
    root = ET.parse(bsd.OSIM).getroot()
    femur = [b for b in root.iter("Body") if b.get("name") == "femur_r"][0]
    data = schema.load_dataset(ROOT / "ontology" / "quantitative_data" / "segments_gait2392.yaml")
    assert data["observations"]["LB-QD:G2392:FEMUR_R:MASS"]["value"] == float(femur.findtext("mass"))
    assert data["observations"]["LB-QD:G2392:JOINT:ANKLE_R"]["value"] == [0.0, -0.43, 0.0]
    knee = data["observations"]["LB-QD:G2392:JOINT:KNEE_R"]["value"]
    assert -0.3966 < knee[1] < -0.395264 and -0.005227 < knee[0] < -0.0031  # between neighbouring knots


def test_mass_bookkeeping(bodies):
    """A1: 2 x (foot + shank + thigh) + HAT equals body mass x sum of fractions."""
    for name, b in bodies.items():
        legs = 2 * (b.foot.mass + b.segments["shank"].mass + b.segments["thigh"].mass)
        total = legs + b.whole_hat_mass
        assert math.isclose(2 * b.per_leg_mass(), total, rel_tol=1e-12)
        assert abs(total / b.body_mass - 1) <= TOL["mass_fraction_sum"], (name, total, b.body_mass)
        assert math.isclose(b.segments["hat"].mass, b.whole_hat_mass / 2, rel_tol=1e-12)


def test_every_consumed_input_passes_the_traceability_gate(bodies, schema):
    for b in bodies.values():
        reports = sq.traceability(b, schema)
        assert all(r["passed"] for r in reports.values())
        assert sum(len(r["inputs"]) for r in reports.values()) >= 20


def test_gate_stops_a_run_on_a_corrupted_input(schema, monkeypatch):
    original = schema.load_dataset

    def corrupted(path):
        d = original(path)
        if Path(path).name == "segments_de_leva_1996.yaml":
            d["observations"]["LB-QD:DELEVA:F:THIGH:MASS_FRACTION"]["provenance"]["source_claims"] = []
        return d

    monkeypatch.setattr(schema, "load_dataset", corrupted)
    body = sq.build_body("female", schema)
    with pytest.raises(ValueError, match="input traceability gate failed"):
        sq.traceability(body, schema)


def test_new_fraction_bounds(schema):
    data = schema.load_dataset(ROOT / "ontology" / "quantitative_data" / "segments_de_leva_1996.yaml")
    d = deepcopy(data["observations"]["LB-QD:DELEVA:F:THIGH:MASS_FRACTION"])
    for bad in (0.0, 1.0, 1.2):
        d["value"] = bad
        assert any("bound" in e for e in schema.validate_datum(d, data)), bad


# ---------------------------------------------------------------------- ontology
def test_ontology_modules_load_together_and_keep_existing_ids(schema):
    hip_only = AnatomyOntology(ROOT / "ontology" / "hip.yaml")
    for eid, entity in hip_only.entities.items():
        assert schema.ontology.get(eid) == entity
    assert "LB:JOINT:KNEE_R" in schema.ontology.entities
    assert schema.property_applies_to_entity("range_of_motion", "LB:JOINT:KNEE_R")  # D-031 through the hierarchy


def _module(tmp_path, extra):
    module = yaml.safe_load((ROOT / "ontology" / "lower_limb_sagittal.yaml").read_text(encoding="utf-8"))
    extra(module)
    path = tmp_path / "module.yaml"
    path.write_text(yaml.safe_dump(module), encoding="utf-8")
    return [ROOT / "ontology" / "hip.yaml", path]


def test_module_cannot_redefine_an_existing_id(tmp_path):
    paths = _module(tmp_path, lambda m: m["entities"].update({"LB:SEG:THIGH_R": {"name": "x", "class": "RigidBodySegment"}}))
    with pytest.raises(ValueError, match="already defined"):
        AnatomyOntology(paths)


def test_module_must_name_the_ontology_it_extends(tmp_path):
    paths = _module(tmp_path, lambda m: m["ontology_module"].update({"extends": "OTHER"}))
    with pytest.raises(ValueError, match="extends"):
        AnatomyOntology(paths)


def test_module_references_are_checked_across_files(tmp_path):
    paths = _module(tmp_path, lambda m: m["entities"]["LB:JOINT:KNEE_R"]["relationships"]["CONNECTS"].append("LB:BONE:PATELLA_R"))
    with pytest.raises(ValueError, match="references missing LB:BONE:PATELLA_R"):
        AnatomyOntology(paths)


# ------------------------------------------------------------- HAT and geometry
def test_hat_assembly_parallel_axis_hand_case():
    m, c, inertia = sq.assemble_hat([(2.0, [0.0, 0.0], 0.1), (1.0, [0.0, 0.3], 0.05)])
    assert m == 3.0 and np.allclose(c, [0.0, 0.1])
    assert math.isclose(inertia, 0.1 + 2 * 0.1 ** 2 + 0.05 + 1 * 0.2 ** 2, rel_tol=1e-12)


def test_gait2392_hat_is_pelvis_plus_torso(schema):
    g, _ = sq.gait2392_geometry(schema)
    assert math.isclose(g["HAT"]["m"], g["PELVIS"]["m"] + g["TORSO"]["m"], rel_tol=1e-12)
    expected = (g["PELVIS"]["m"] * (g["PELVIS"]["c"] - g["HIP_R"])
                + g["TORSO"]["m"] * (g["BACK"] + g["TORSO"]["c"] - g["HIP_R"])) / g["HAT"]["m"]
    assert np.allclose(g["HAT"]["c"], expected, atol=1e-15)


def test_de_leva_bodies_scale_gait2392_geometry(bodies):
    g, f = bodies["gait2392"], bodies["female"]
    scale = f.stature / g.stature
    assert np.allclose(f.foot.heel, scale * g.foot.heel)
    assert np.allclose(f.segments["shank"].upper, scale * g.segments["shank"].upper)


# ------------------------------------------------------------- mechanics checks
def test_newton_euler_matches_lagrange(bodies, motion):
    q, qd, qdd = samples(motion)
    for name, b in bodies.items():
        ne = sq.inverse_dynamics(b, q, qd, qdd, G)["tau"]
        la = sq.lagrange_torques(b, q, qd, qdd, G)
        assert np.max(np.abs(ne - la)) < TOL["newton_euler_vs_lagrange_N_m"], name
        assert np.max(np.abs(ne)) > 10  # not trivially zero


def test_static_poses_match_direct_gravity_moments(bodies):
    rng = np.random.default_rng(58)
    for b in bodies.values():
        for q in rng.uniform([-0.3, 0.0, 0.0], [0.8, 2.0, 2.0], size=(20, 3)):
            ne = sq.inverse_dynamics(b, q[:, None], np.zeros((3, 1)), np.zeros((3, 1)), G)["tau"][:, 0]
            assert np.max(np.abs(ne - sq.static_torques(b, q, G))) < TOL["static_oracle_N_m"]


def test_torque_signs(bodies):
    """Trunk leaning forward needs hip extension (negative); deep knee flexion needs knee extension."""
    b = bodies["female"]
    tau = sq.static_torques(b, np.array([0.5, 1.5, 1.4]), G)
    assert tau[2] < 0 and tau[1] < 0


def test_energy_identity(bodies, motion):
    q, qd, qdd = samples(motion)
    for b in bodies.values():
        tau = sq.inverse_dynamics(b, q, qd, qdd, G)["tau"]
        power = np.sum(tau * qd, axis=0)
        rate = sq.energy_rate(b, q, qd, qdd, G)
        assert np.max(np.abs(power - rate)) < TOL["energy_W"]
        assert np.max(np.abs(power)) > 1


def test_newton_identities(bodies, motion):
    """A1: per-leg vertical ground force and whole-body consistency, computed separately."""
    q, qd, qdd = samples(motion)
    for b in bodies.values():
        res = sq.inverse_dynamics(b, q, qd, qdd, G)
        k = res["kinematics"]
        per_leg = b.foot.mass * G + sum(b.segments[n].mass * (G + k[f"com_{n}"][2][1]) for n in sq.MOVING)
        assert np.max(np.abs(res["grf"][1] - per_leg)) < TOL["newton_identity_N"]
        m, _, acc = sq.whole_body_com(b, k)
        assert np.max(np.abs(2 * res["grf"][1] - m * (G + acc[1]))) < TOL["newton_identity_N"]
        assert np.max(np.abs(2 * res["grf"][0] - m * acc[0])) < TOL["newton_identity_N"]


def _point_mass_body(m1, l1, m2, l2):
    zero = np.zeros(2)
    segs = {"shank": sq.Segment(m1, 0.0, np.array([0.0, l1]), np.array([0.0, l1])),
            "thigh": sq.Segment(m2, 0.0, np.array([0.0, l2]), np.array([0.0, l2])),
            "hat": sq.Segment(0.0, 0.0, zero, zero)}
    foot = sq.Foot(0.0, zero, np.array([-0.1, -0.05]), np.array([0.2, -0.05]), -0.05)
    return sq.Body("double_pendulum", m1 + m2, 1.0, foot, segs, 0.0)


def test_closed_form_single_pendulum():
    m, l, inertia = 3.0, 0.4, 0.05
    zero = np.zeros(2)
    segs = {"shank": sq.Segment(m, inertia, np.array([0.0, l]), np.array([0.0, 2 * l])),
            "thigh": sq.Segment(0.0, 0.0, zero, zero), "hat": sq.Segment(0.0, 0.0, zero, zero)}
    body = sq.Body("pendulum", m, 1.0, sq.Foot(0.0, zero, zero, zero, -0.05), segs, 0.0)
    mo = sq.Motion(np.zeros(3), np.array([0.6, 0.0, 0.0]), 2.0)
    q, qd, qdd = samples(mo, 101)
    tau = sq.inverse_dynamics(body, q, qd, qdd, G)["tau"][0]
    # Inverted pendulum about the ankle, theta = q_ankle: tau = J theta'' - m g l sin(theta).
    expected = (inertia + m * l * l) * qdd[0] - m * G * l * np.sin(q[0])
    assert np.max(np.abs(tau - expected)) < TOL["closed_form_N_m"]


def test_closed_form_double_pendulum():
    """Inverted double pendulum with point masses at the knee and hip, textbook equations."""
    m1, l1, m2, l2 = 4.0, 0.43, 9.0, 0.4
    body = _point_mass_body(m1, l1, m2, l2)
    mo = sq.Motion(np.array([0.1, 0.2, 0.0]), np.array([0.5, 1.4, 0.0]), 2.5)
    q, qd, qdd = samples(mo, 151)
    p1, p2 = -q[0], -q[0] + q[1]                      # absolute angles from vertical, counter-clockwise
    d1, d2 = -qd[0], -qd[0] + qd[1]
    a1, a2 = -qdd[0], -qdd[0] + qdd[1]
    c, s = np.cos(p1 - p2), np.sin(p1 - p2)
    Q1 = (m1 + m2) * l1 ** 2 * a1 + m2 * l1 * l2 * c * a2 + m2 * l1 * l2 * s * d2 ** 2 - (m1 + m2) * G * l1 * np.sin(p1)
    Q2 = m2 * l2 ** 2 * a2 + m2 * l1 * l2 * c * a1 - m2 * l1 * l2 * s * d1 ** 2 - m2 * G * l2 * np.sin(p2)
    tau = sq.inverse_dynamics(body, q, qd, qdd, G)["tau"]
    # phi = B q, so tau = B^T Q_phi: ankle = -Q1 - Q2, knee = Q2.
    assert np.max(np.abs(tau[0] - (-Q1 - Q2))) < TOL["closed_form_N_m"]
    assert np.max(np.abs(tau[1] - Q2)) < TOL["closed_form_N_m"]


def test_local_one_step_consistency(bodies, motion):
    """Newton-Euler torques drive the Lagrange equations one RK4 step from the exact state;
    the local error falls about 32-fold per halving (order step^5); 16 is required."""
    for b in bodies.values():
        errors = [sq.local_step_error(b, motion, G, h) for h in (0.004, 0.002, 0.001)]
        assert errors[2] < TOL["local_one_step_rad_at_1ms"]
        assert errors[0] / errors[1] > 16 and errors[1] / errors[2] > 16, errors


def test_short_horizon_forward_reproduction(bodies, motion):
    """0.1 s forward runs from exact states reproduce the motion; global error falls about
    16-fold per halving (order step^4); 12 is required. Replaces whole-motion recovery
    (D-058 Amendment 3, Q47)."""
    for name in ("female", "gait2392"):
        errors = [sq.short_horizon_error(bodies[name], motion, G, h, starts=6) for h in (0.004, 0.002, 0.001)]
        assert errors[2] < TOL["short_horizon_0p1s_rad_at_1ms"]
        assert errors[0] / errors[1] > 12 and errors[1] / errors[2] > 12, errors


# ----------------------------------------------------------- contact and config
def test_demonstration_motion_is_contact_feasible(bodies):
    for name, b in bodies.items():
        c = sq.run(b, PARAMS)["contact"]
        assert c["feasible"], (name, c)
        assert c["normal_force_min_N"] > 0


def test_infeasible_motion_is_flagged_not_hidden(bodies):
    params = dict(PARAMS, depth_angles=np.array([0.2, 1.6, 0.6]))   # sitting back: centre of pressure behind the heel
    c = sq.run(bodies["female"], params)["contact"]
    assert not c["feasible"] and c["cop_outside_support_samples"] > 0
    params = dict(PARAMS, friction_coefficient=1e-4)
    c = sq.run(bodies["female"], params)["contact"]
    assert c["friction_exceeded_samples"] > 0 and not c["feasible"]


def _bad_config(tmp_path, change):
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    change(cfg)
    path = tmp_path / "c.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


@pytest.mark.parametrize("change,message", [
    (lambda c: c["parameters"]["gravity"].update(kind="measured"), "kind"),
    (lambda c: c["parameters"]["period"].update(rationale=" "), "rationale"),
    (lambda c: c["parameters"]["period"].update(value=-1.0), "positive"),
    (lambda c: c["parameters"]["depth_angles"].update(value=[0.1, 0.2]), "three angles"),
    (lambda c: c["parameters"]["depth_angles"].update(value=[0.1, float("nan"), 0.2]), "finite"),
    (lambda c: c.update(bodies=["giant"]), "bodies"),
    (lambda c: c.pop("omitted_physics"), "configuration fields"),
])
def test_config_rejects_bad_input(tmp_path, change, message):
    with pytest.raises(ValueError, match=message):
        sq.load_config(_bad_config(tmp_path, change))


def test_unknown_body_rejected(schema):
    with pytest.raises(ValueError, match="unknown body"):
        sq.build_body("child", schema)


# ------------------------------------------------- review D1-R01, D1-R05, D1-R06
def test_lift_off_is_flagged_and_serializable(bodies):
    """A motion fast enough to unload the foot: no centre of pressure there, flagged, and the
    manifest series still serializes (non-finite values become null)."""
    from tools.run_phase_d1 import _round
    params = dict(PARAMS, period=0.35)
    r = sq.run(bodies["female"], params)
    c = r["contact"]
    assert c["lift_off_samples"] > 0 and not c["feasible"]
    assert c["required_friction_max"] is None
    series = _round(r["cop_x"])
    assert None in series and all(x is None or math.isfinite(x) for x in series)


def test_zero_or_reversed_support_rejected(bodies):
    b = deepcopy(bodies["female"])
    b.foot.ball = b.foot.heel.copy()
    with pytest.raises(ValueError, match="foot support"):
        sq.run(b, PARAMS)


def test_runner_fails_closed_when_a_check_fails(bodies, schema):
    from tools import run_phase_d1 as rp
    strict = {k: 0.0 for k in TOL}
    run = rp.run_body("female", schema, PARAMS, strict)
    assert run["status"]["mechanics_verification"] == "failed"
    manifest = {"runs": [run], "status": rp.aggregate_status([run])}
    assert manifest["status"]["mechanics_verification"] == "failed"
    assert rp.exit_code(manifest) == 1
    text = "\n".join(rp.summary_lines(manifest))
    assert "MECHANICS CHECKS FAILED" in text and "verified" not in text.lower().replace("verification", "")


def test_runner_statuses_are_separate(bodies, schema):
    from tools import run_phase_d1 as rp
    ok = rp.run_body("female", schema, PARAMS, TOL)
    assert ok["status"] == {"mechanics_verification": "passed", "contact_feasibility": "feasible",
                            "source_validation": "provisional"}
    flagged = rp.run_body("female", schema, dict(PARAMS, depth_angles=np.array([0.2, 1.6, 0.6])), TOL)
    assert flagged["status"]["mechanics_verification"] == "passed"
    assert flagged["status"]["contact_feasibility"] == "flagged"
    manifest = {"runs": [ok, flagged], "status": rp.aggregate_status([ok, flagged])}
    assert manifest["status"]["contact_feasibility"] == "flagged" and rp.exit_code(manifest) == 0
    assert any("Contact flagged" in line for line in rp.summary_lines(manifest))
    with pytest.raises(ValueError):
        rp.aggregate_status([])


def test_sensitivity_analysis(schema):
    from tools import sensitivity_d1 as sens
    result = sens.analyse()
    for name, rows in result["bodies"].items():
        base = rows[0]
        assert base["case"] == "baseline" and all(v == 0 for v in base["largest_change_at_any_instant_N_m"].values())
        assert all(r["contact_feasible"] for r in rows), name
    female = {r["case"]: r for r in result["bodies"]["female"]}
    assert female["gait2392_stature_1.66m"]["knee_peak_change_pct"] > 5      # shorter reference: larger body scale
    assert female["hat_com_+2cm"]["largest_change_at_any_instant_N_m"]["hip"] > 1
