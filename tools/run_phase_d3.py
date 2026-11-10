"""Run Stage D3 (moving knee) for every configured body and write one manifest (D-060).

    python -m tools.run_phase_d3 --commit-sha FULL_SHA \\
        --d1-manifest results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json \\
        --d2-manifest results/phase_d/2026-11-10_d2_muscle_runs_7ac0f2d.json \\
        --output results/phase_d/<date>_d3_moving_knee_runs_<shortsha>.json

For each body: the D1 squat's inverse dynamics with Gait2392's moving knee (src/squat_d3.py), its
mechanics checks and contact feasibility; then D2's muscles on that knee and those torques; then a
sample-by-sample comparison with the official fixed-knee results (D1 and D2 manifests). The
kinematics are compared with the OpenSim oracle (tests/data/d3_oracle_reference.json). Exit
code 1 when a verification fails; flagged contact, muscle feasibility or force-law domain are
results. Series use the D2 manifest's names, so the D2 viewer can show both knee models.
"""
import argparse
import dataclasses
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

from src import muscles_d2 as m2
from src import squat_d1 as sq
from src import squat_d3 as d3
from src.quantitative import QuantitativeSchema
from src.run_manifest import manifest_header
from tools import run_phase_d2 as d2r

ROOT = sq.ROOT
CONFIG = ROOT / "config" / "phase_d3_moving_knee.yaml"
ORACLE = ROOT / "tests" / "data" / "d3_oracle_reference.json"
INPUTS = dict(d2r.INPUTS)
for key in ("runner", "oracle_reference"):
    INPUTS.pop(key, None)
INPUTS.update({"d2_runner": ROOT / "tools/run_phase_d2.py", "d3_config": CONFIG, "d3_model": ROOT / "src/squat_d3.py",
               "d3_oracle_reference": ORACLE, "runner": ROOT / "tools/run_phase_d3.py"})
REQUIRED = {"model_id", "decision", "d1_config", "d2_config", "bodies", "knee_model", "tolerances", "assumptions",
            "omitted_physics"}
TOLERANCES = {"newton_euler_vs_kane_N_m", "static_virtual_work_N_m", "energy_W", "newton_identity_N",
              "local_one_step_rad_at_1ms", "short_horizon_0p1s_rad_at_1ms", "mass_fraction_sum", "kinematics_oracle_m"}


def load_config(path=CONFIG):
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(cfg, dict) or set(cfg) != REQUIRED:
        raise ValueError("configuration fields must be exactly: " + ", ".join(sorted(REQUIRED)))
    if cfg["knee_model"] != "gait2392_moving":
        raise ValueError("knee_model must be 'gait2392_moving' (the only knee this runner implements)")
    tol = cfg["tolerances"]
    if set(tol) != TOLERANCES or any(type(v) not in (int, float) or not v > 0 for v in tol.values()):
        raise ValueError(f"tolerances must be exactly {sorted(TOLERANCES)}, all positive")
    if any(b not in ("female", "male", "gait2392") for b in cfg["bodies"]):
        raise ValueError("bodies must be female, male or gait2392")
    return cfg


def _r(a, digits=6):
    return [None if not math.isfinite(x) else x for x in np.round(np.asarray(a, float), digits).tolist()]


def kinematics_oracle_error(oracle):
    """Largest difference (m) between D3's Gait2392 kinematics and OpenSim's, over all D1 samples."""
    b = d3.build_body("gait2392")
    hip = m2.d1_joints(1.0).hip[:2]
    err = 0.0
    for row in oracle["kinematics"]:
        q = np.array(row["q"])[:, None]
        k = d3.kinematics(b, q, np.zeros((3, 1)), np.zeros((3, 1)))
        Rh = d3._rot((sq.B_MAP @ q[:, 0])[2])
        mine = {"knee_m": k["knee"][0][:, 0], "hip_m": k["hip"][0][:, 0], "femur_com_m": k["com_thigh"][0][:, 0],
                "tibia_com_m": k["com_shank"][0][:, 0], "pelvis_origin_m": k["hip"][0][:, 0] + Rh @ (-hip)}
        for key, v in mine.items():
            err = max(err, float(np.max(np.abs(v - np.array(row[key][:2])))))
    return err


def run_body(name, schema, d1_params, d2_params, tol, d1_official, d2_official, oracle_error):
    b = d3.build_body(name, schema)
    res = d3.run(b, d1_params)
    checks = d3.check_residuals(b, d1_params, res)
    passed = {k: abs(v) <= tol[k] for k, v in checks.items() if k in tol}
    passed["newton_identity_per_leg_N"] = checks["newton_identity_per_leg_N"] <= tol["newton_identity_N"]
    passed["mass_bookkeeping_relative"] = abs(checks["mass_bookkeeping_relative"]) <= tol["mass_fraction_sum"]
    if set(passed) != set(checks):
        raise ValueError(f"checks without a tolerance: {sorted(set(checks) - set(passed))}")
    q, qd, tau = res["q"], res["qd"], res["tau"]
    s = d2r.body_scale(b.base)
    acts, consumed = m2.load_actuators(s, schema)
    joints = dataclasses.replace(m2.d1_joints(s, schema), moving_knee=b.knee)
    trace = dict(sq.traceability(b.base, schema), **m2.muscle_traceability(consumed, schema))
    n, k = q.shape[1], len(acts)
    act, force, unit = np.zeros((k, n)), np.zeros((k, n)), np.zeros((k, n))
    lnorm, vnorm = np.full((k, n), np.nan), np.full((k, n), np.nan)
    reserve, t_star, needed = np.zeros((3, n)), np.zeros(n), np.zeros((3, n))
    flags, drawing = [], []
    worst = {"kkt": 0.0, "t_star_difference": 0.0, "activation_difference": 0.0}
    for i in range(n):
        Cm = np.zeros((3, k))
        frame = []
        for j, a in enumerate(acts):
            L, R, pts = m2.path(a, q[:, i], joints)
            st = m2.fiber_state(a, L, -R @ qd[:, i])
            unit[j, i] = m2.unit_tendon_force(a, st)
            Cm[:, j] = unit[j, i] * R
            lnorm[j, i], vnorm[j, i] = st["l_norm"], st["v_norm"]
            flags += [{"sample": i, "actuator": a.name, "flag": f} for f in st["flags"]]
            frame.append([[round(float(p[0]), 5), round(float(p[1]), 5)] for p in pts])
        drawing.append(frame)
        rec = m2.recruit(Cm, tau[:, i], delta=d2_params["solver_band_delta"])
        act[:, i], reserve[:, i], t_star[i] = rec.activation, rec.reserve, rec.t_star
        force[:, i] = rec.activation * unit[:, i]
        if rec.t_star > d2_params["solver_band_delta"]:
            needed[:, i] = m2.smallest_reserve_per_joint(Cm, tau[:, i], rec.band)
        worst["kkt"] = max(worst["kkt"], *(v for st_ in rec.kkt.values() for v in st_.values()))
        worst["t_star_difference"] = max(worst["t_star_difference"], rec.solvers["t_star_difference"])
        worst["activation_difference"] = max(worst["activation_difference"], rec.solvers["activation_difference"])
    optimizer_ok = (worst["kkt"] <= d2_params["kkt_tolerance"]
                    and worst["t_star_difference"] <= d2_params["second_solver_t_star_tolerance"]
                    and worst["activation_difference"] <= d2_params["second_solver_activation_tolerance"]
                    and np.all(np.isfinite(act)) and np.all(np.isfinite(reserve)))
    eps = d2_params["epsilon_reserve"]
    flagged = np.flatnonzero(t_star > eps)
    peak = int(np.argmax(t_star))
    pts = res["points"]
    Rh = np.stack([np.stack([np.cos(res["phi"][2]), -np.sin(res["phi"][2])]),
                   np.stack([np.sin(res["phi"][2]), np.cos(res["phi"][2])])])
    hat_top = pts["hip"] + np.einsum("ijn,j->in", Rh, 2 * b.c_h)
    d1r = next(r for r in d1_official["runs"] if r["body"] == name)
    d2r_ = next(r for r in d2_official["runs"] if r["body"] == name)
    tau_fixed = np.array([d1r["series"]["tau_per_leg_N_m"][j] for j in sq.JOINTS], float)
    t_fixed = np.array(d2r_["series"]["t_star_N_m"], float)
    act_fixed = np.array([d2r_["series"]["activation"][a.name] for a in acts], float)
    status = {"mechanics_verification": "passed" if all(passed.values()) else "failed",
              "kinematics_verification": "passed" if oracle_error <= tol["kinematics_oracle_m"] else "failed",
              "contact_feasibility": "feasible" if res["contact"]["feasible"] else "flagged",
              "source_validation": d2r.SOURCE_VALIDATION["status"],
              "optimizer_verification": "passed" if optimizer_ok else "failed",
              "muscle_feasibility": "feasible" if float(np.max(t_star)) <= eps else "flagged",
              "force_law_domain": "flagged" if flags else "in_domain"}
    return {
        "body": name, "scale": s, "status": status, "body_mass_kg": b.base.body_mass, "stature_m": b.base.stature,
        "foot": {"mass_kg": b.base.foot.mass, "com_m": _r(b.base.foot.com, 9), "heel_m": _r(b.base.foot.heel, 9),
                 "ball_m": _r(b.base.foot.ball, 9), "ground_y_m": b.base.foot.ground_y},
        "input_traceability": trace,
        "checks": {"residuals": checks, "passed": passed, "all_passed": all(passed.values())},
        "contact": res["contact"],
        "verification": {"kinematics_oracle_error_m": oracle_error, "largest_kkt_residual": worst["kkt"],
                         "second_solver_t_star_difference_N_m": worst["t_star_difference"],
                         "second_solver_activation_difference": worst["activation_difference"]},
        "reserve_summary": {
            "norm": "largest absolute per-joint reserve (L-infinity), D-059 Amendment 2",
            "t_star_max_N_m": round(float(np.max(t_star)), 6), "t_star_max_time_s": float(res["t"][peak]),
            "q_at_t_star_max_deg": [round(math.degrees(x), 3) for x in q[:, peak]],
            "flagged_samples": int(flagged.size),
            "flagged_time_range_s": [float(res["t"][flagged[0]]), float(res["t"][flagged[-1]])] if flagged.size else None,
            "limiting_joints_at_t_star_max": [j for jj, j in enumerate(sq.JOINTS)
                                              if needed[jj, peak] >= t_star[peak] - d2r.LIMITING_TOL]
                                             if t_star[peak] > 0 else [],
            "epsilon_reserve_N_m": eps, "solver_band_delta_N_m": d2_params["solver_band_delta"]},
        "comparison_with_fixed_knee": {
            "d1_manifest_commit": d1_official["commit_sha"], "d2_manifest_commit": d2_official["commit_sha"],
            "largest_torque_change_N_m": {j: round(float(np.max(np.abs(tau[i] - tau_fixed[i]))), 6)
                                          for i, j in enumerate(sq.JOINTS)},
            "peak_knee_torque_N_m": {"fixed": float(np.min(tau_fixed[1])), "moving": round(float(np.min(tau[1])), 6)},
            "cop_range_m": {"fixed": [d1r["contact"]["cop_min_m"], d1r["contact"]["cop_max_m"]],
                            "moving": [res["contact"]["cop_min_m"], res["contact"]["cop_max_m"]]},
            "heel_margin_min_m": {"fixed": d1r["contact"]["cop_min_m"] - d1r["contact"]["support_heel_m"],
                                  "moving": res["contact"]["heel_margin_min_m"]},
            "t_star_max_N_m": {"fixed": float(np.max(t_fixed)), "moving": round(float(np.max(t_star)), 6)},
            "flagged_samples": {"fixed": int(np.sum(t_fixed > eps)), "moving": int(flagged.size)},
            "largest_activation_change": round(float(np.max(np.abs(act - act_fixed))), 6),
            "note": "fixed = official D1/D2 manifests (D1's fixed-centre knee); moving = this run (D-060)"},
        "force_law_domain_flags": flags,
        "path_length_jumps": d2r.switch_jumps(acts, joints, np.asarray(d1_params["depth_angles"], float)),
        "actuators": [{"name": a.name, "represents": a.entity, "max_isometric_force_N": a.f0,
                       "optimal_fiber_length_m": round(a.l_opt, 9), "tendon_slack_length_m": round(a.l_ts, 9),
                       "pennation_at_optimal_rad": a.alpha0} for a in acts],
        "series": {
            "t_s": _r(res["t"], 9), "q_rad": {j: _r(q[i], 9) for i, j in enumerate(sq.JOINTS)},
            "tau_per_leg_N_m": {j: _r(tau[i]) for i, j in enumerate(sq.JOINTS)},
            "knee_translation_term_N_m": _r(res["knee_translation_term"]),
            "grf_per_leg_N": {"x": _r(res["grf"][0]), "y": _r(res["grf"][1])}, "cop_x_m": _r(res["cop_x"], 9),
            "t_star_N_m": _r(t_star, 9),
            "reserve_per_joint_N_m": {j: _r(reserve[i], 9) for i, j in enumerate(sq.JOINTS)},
            "smallest_needed_reserve_per_joint_N_m": {j: _r(needed[i], 9) for i, j in enumerate(sq.JOINTS)},
            "activation": {a.name: _r(act[j]) for j, a in enumerate(acts)},
            "tendon_force_N": {a.name: _r(force[j], 3) for j, a in enumerate(acts)},
            "normalized_fiber_length": {a.name: _r(lnorm[j], 5) for j, a in enumerate(acts)},
            "normalized_fiber_velocity": {a.name: _r(vnorm[j], 5) for j, a in enumerate(acts)},
            "muscle_path_xy_m": drawing,
            "d1_points_m": {key: {"x": _r(v[0]), "y": _r(v[1])} for key, v in dict(pts, hat_drawing_top=hat_top).items()},
        },
    }


def aggregate_status(runs):
    def every(key, good):
        return all(r["status"][key] == good for r in runs)
    return {"mechanics_verification": "passed" if every("mechanics_verification", "passed") else "failed",
            "kinematics_verification": "passed" if every("kinematics_verification", "passed") else "failed",
            "contact_feasibility": "feasible" if every("contact_feasibility", "feasible") else "flagged",
            "source_validation": d2r.SOURCE_VALIDATION["status"],
            "optimizer_verification": "passed" if every("optimizer_verification", "passed") else "failed",
            "muscle_feasibility": "feasible" if every("muscle_feasibility", "feasible") else "flagged",
            "force_law_domain": "in_domain" if every("force_law_domain", "in_domain") else "flagged"}


def exit_code(manifest):
    s = manifest["status"]
    ok = all(s[k] == "passed" for k in ("mechanics_verification", "kinematics_verification", "optimizer_verification"))
    return 0 if ok else 1


def build_manifest(commit_sha, d1_manifest, d2_manifest, config_path=CONFIG):
    cfg = load_config(config_path)
    d1_cfg, d1_params = sq.load_config(ROOT / cfg["d1_config"])
    d2_cfg, d2_params = d2r.load_config(ROOT / cfg["d2_config"])
    schema = QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    d1_official = json.loads(Path(d1_manifest).read_text(encoding="utf-8"))
    d2_official = json.loads(Path(d2_manifest).read_text(encoding="utf-8"))
    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    paths = dict(INPUTS, d3_config=config_path, config=ROOT / cfg["d1_config"], d2_config=ROOT / cfg["d2_config"],
                 d1_manifest=Path(d1_manifest), d2_manifest=Path(d2_manifest))
    manifest = manifest_header(ROOT, {k: str(v) for k, v in paths.items()}, commit_sha)
    err = kinematics_oracle_error(oracle)
    runs = [run_body(n, schema, d1_params, d2_params, cfg["tolerances"], d1_official, d2_official, err)
            for n in cfg["bodies"]]
    manifest.update({
        "status": aggregate_status(runs), "decision": "D-060", "model_id": cfg["model_id"], "knee_model": cfg["knee_model"],
        "d1_official_manifest": {"path": str(Path(d1_manifest)), "commit_sha": d1_official["commit_sha"]},
        "d2_official_manifest": {"path": str(Path(d2_manifest)), "commit_sha": d2_official["commit_sha"]},
        "what_the_checks_show": ("Verification that the moving-knee mechanics (two formulations, virtual work, energy, "
                                 "Newton, forward consistency; kinematics against OpenSim) and the D2 muscle model on "
                                 "that knee are computed correctly. Not validation against measured squats or muscle "
                                 "activity."),
        "configuration": cfg, "d2_configuration": d2_cfg,
        "oracle_reference": {"path": str(ORACLE.relative_to(ROOT)), **{k: oracle["provenance"][k] for k in
                             ("opensim_version", "source_model_sha256", "matched_model_sha256", "knee_mode")}},
        "runs": runs, "source_validation": d2r.SOURCE_VALIDATION,
    })
    return manifest


def summary_lines(manifest):
    lines = []
    for r in manifest["runs"]:
        s, c = r["status"], r["comparison_with_fixed_knee"]
        lines.append(f"{r['body']}: mechanics {s['mechanics_verification'].upper()}, kinematics "
                     f"{s['kinematics_verification'].upper()}, optimizer {s['optimizer_verification'].upper()}; contact "
                     f"{s['contact_feasibility']}; muscles {s['muscle_feasibility'].upper()} (t* max fixed "
                     f"{c['t_star_max_N_m']['fixed']:.3f} -> moving {c['t_star_max_N_m']['moving']:.3f} N m); peak knee "
                     f"{c['peak_knee_torque_N_m']['fixed']:.2f} -> {c['peak_knee_torque_N_m']['moving']:.2f} N m")
    lines.append("A VERIFICATION FAILED: do not use." if exit_code(manifest) else
                 "Verification passed. A demonstration under stated assumptions; not validated.")
    return lines


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--commit-sha", required=True)
    p.add_argument("--d1-manifest", type=Path, required=True)
    p.add_argument("--d2-manifest", type=Path, required=True)
    p.add_argument("--config", type=Path, default=CONFIG)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    manifest = build_manifest(args.commit_sha, args.d1_manifest, args.d2_manifest, args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, sort_keys=True, allow_nan=False, separators=(",", ":")) + "\n",
                           encoding="utf-8")
    for line in summary_lines(manifest):
        print(line)
    print("Manifest written to", args.output)
    sys.exit(exit_code(manifest))


if __name__ == "__main__":
    main()
