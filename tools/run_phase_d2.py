"""Run Stage D2 (muscle forces for the D1 squat) for every configured body and write one manifest (D-059).

    python -m tools.run_phase_d2 --commit-sha FULL_40_CHAR_SHA \\
        --d1-manifest results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json \\
        --output results/phase_d/<date>_d2_muscle_runs_<shortsha>.json

The motion and joint torques are recomputed with the Stage D1 model and configuration
and must equal the official D1 manifest (to its 6 stored decimals). For each sample the
14 actuators' geometry, rigid-tendon force coefficients and two-stage recruitment are
computed (src/muscles_d2.py). The manifest records the commit and every consumed file
(D-055 C1), the traceability report (C4), statuses, the declared simplifications, and the
series the page draws. Exit code 1 when a verification fails (D1 mechanics, D1
consistency, optimizer); a flagged muscle feasibility or force-law domain is a result.
Muscle forces are a demonstration under a stated criterion; physiological validity is
not claimed.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

from src import muscles_d2 as m2
from src import squat_d1 as sq
from src.quantitative import QuantitativeSchema
from src.run_manifest import manifest_header
from tools import run_phase_d1 as d1r

ROOT = sq.ROOT
CONFIG = ROOT / "config" / "phase_d2_muscles.yaml"
ORACLE = ROOT / "tests" / "data" / "d2_oracle_reference.json"
INPUTS = dict(d1r.INPUTS)
INPUTS.pop("runner")
INPUTS.update({
    "d1_runner": ROOT / "tools/run_phase_d1.py",
    "d2_config": CONFIG,
    "dataset_muscles": ROOT / "ontology/quantitative_data/muscles_gait2392.yaml",
    "source_degroote_header": m2.HEADER,
    "muscle_model": ROOT / "src/muscles_d2.py",
    "oracle_reference": ORACLE,
    "runner": ROOT / "tools/run_phase_d2.py",
})
SOURCE_VALIDATION = dict(d1r.SOURCE_VALIDATION, **{
    "muscle_values": ("Gait2392 parameters and paths read from the model file; maximum isometric forces are Delp's "
                      "values scaled upward, not uniformly (OpenSim 2.4 documentation); paths built for gait"),
    "muscle_validity": "not established; no comparison with measured muscle activity"})
# A joint is "limiting" when its smallest possible |reserve| is within this of t*. The stage-2 band lets the
# other joints exceed t* by delta (1e-6 N m), which through two-joint muscles can lower a joint by about
# 1e-4 N m at the flagged samples; 1e-3 N m keeps that numerical effect from hiding a limiting joint.
LIMITING_TOL = 1e-3
REQUIRED = {"model_id", "decision", "d1_config", "bodies", "parameters", "baseline_force_law", "assumptions",
            "omitted_physics"}


def load_config(path=CONFIG):
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(cfg, dict) or set(cfg) != REQUIRED:
        raise ValueError("configuration fields must be exactly: " + ", ".join(sorted(REQUIRED)))
    params = {}
    for name, item in cfg["parameters"].items():
        if not isinstance(item, dict) or set(item) != {"value", "unit", "kind", "rationale"}:
            raise ValueError(f"{name}: needs value, unit, kind and rationale")
        if item["kind"] not in ("demonstration_assumption", "defined_constant", "solver_tolerance"):
            raise ValueError(f"{name}: unknown kind {item['kind']}")
        if not str(item["rationale"]).strip() or type(item["value"]) not in (int, float) \
                or not math.isfinite(item["value"]) or item["value"] <= 0:
            raise ValueError(f"{name}: finite positive value and rationale required")
        params[name] = float(item["value"])
    needed = {"epsilon_reserve", "solver_band_delta", "kkt_tolerance", "second_solver_t_star_tolerance",
              "second_solver_activation_tolerance", "d1_consistency_N_m", "passive_strain_sensitivity"}
    if set(params) != needed:
        raise ValueError(f"parameters must be exactly {sorted(needed)}")
    if cfg["baseline_force_law"].get("fiber_damping") != 0.0 or cfg["baseline_force_law"].get("tendon") != "rigid":
        raise ValueError("baseline must declare a rigid tendon and fiber damping 0 (D-059 Amendment 1)")
    return cfg, params


def _r(a, digits=6):
    return [None if not math.isfinite(x) else x for x in np.round(np.asarray(a, float), digits).tolist()]


def body_scale(body):
    return 1.0 if body.name == "gait2392" else body.stature / 1.8


def d1_consistency(name, result, official):
    run = next(r for r in official["runs"] if r["body"] == name)
    off = np.array([run["series"]["tau_per_leg_N_m"][j] for j in sq.JOINTS], float)
    return float(np.max(np.abs(np.round(result["tau"], 6) - off)))


def switch_jumps(acts, joints, depth):
    """Path-length jump at each conditional switch inside the motion, at D1's depth ratios (Amendment 2)."""
    ratio = depth / depth[1]
    out = []
    for a in acts:
        for p in a.points:
            if p.kind != "conditional":
                continue
            for edge in (p.active_range[0] - m2.ACTIVITY_TOL, p.active_range[1] + m2.ACTIVITY_TOL):
                qk = -edge                                    # D1 knee flexion at the widened edge
                if not 0.0 < qk < depth[1]:
                    continue
                sides = [qk - 1e-9, qk + 1e-9]
                with_pt = [x for x in sides if p.active(-x)]
                without = [x for x in sides if not p.active(-x)]
                L_with = m2.path(a, ratio * with_pt[0], joints)[0]
                L_without = m2.path(a, ratio * without[0], joints)[0]
                out.append({"actuator": a.name, "point": p.name, "knee_flexion_deg": round(math.degrees(qk), 4),
                            "length_with_point_minus_without_mm": round(1000 * (L_with - L_without), 6)})
    return out


def simplification_size(acts, joints, oracle):
    """D-059 8f: moment arms on D1's geometry against the unmodified Gait2392 file (OpenSim), per actuator."""
    out = {}
    for a in acts:
        diffs = []
        for row in oracle["unmodified_geometry"]:
            _, R, _ = m2.path(a, np.array(row["q"]), joints)
            diffs.append(np.abs(R - np.array(row["moment_arm_m"][a.name])))
        d = np.max(np.array(diffs), axis=0)
        out[a.name] = {j: round(float(v) * 1000, 4) for j, v in zip(sq.JOINTS, d)}
    return {"units": "mm, largest absolute moment-arm difference over every 10th D1 sample",
            "reported_not_pass_fail": True, "by_actuator": out}


def run_body(name, schema, d1_params, d1_tolerances, params, official, oracle):
    d1 = d1r.run_body(name, schema, d1_params, d1_tolerances)           # D1 statuses and checks
    body = sq.build_body(name, schema)
    result = sq.run(body, d1_params)
    q, qd, tau = result["q"], result["qd"], result["tau"]
    s = body_scale(body)
    acts, consumed = m2.load_actuators(s, schema)
    joints = m2.d1_joints(s, schema)
    trace = m2.muscle_traceability(consumed, schema)
    n, k = q.shape[1], len(acts)
    act = np.zeros((k, n)); force = np.zeros((k, n)); unit = np.zeros((k, n))
    lnorm = np.full((k, n), np.nan); vnorm = np.full((k, n), np.nan)
    reserve = np.zeros((3, n)); t_star = np.zeros(n); needed = np.zeros((3, n))
    flags, worst = [], {"kkt": 0.0, "t_star_difference": 0.0, "activation_difference": 0.0}
    drawing = []
    for i in range(n):
        Cm = np.zeros((3, k))
        frame = []
        for j, a in enumerate(acts):
            L, R, pts = m2.path(a, q[:, i], joints)
            st = m2.fiber_state(a, L, -R @ qd[:, i])
            unit[j, i] = m2.unit_tendon_force(a, st)
            Cm[:, j] = unit[j, i] * R
            lnorm[j, i], vnorm[j, i] = st["l_norm"], st["v_norm"]
            for f in st["flags"]:
                flags.append({"sample": i, "actuator": a.name, "flag": f})
            frame.append([[round(float(p[0]), 5), round(float(p[1]), 5)] for p in pts])
        drawing.append(frame)
        rec = m2.recruit(Cm, tau[:, i], delta=params["solver_band_delta"])
        act[:, i], reserve[:, i], t_star[i] = rec.activation, rec.reserve, rec.t_star
        if rec.t_star > params["solver_band_delta"]:
            needed[:, i] = m2.smallest_reserve_per_joint(Cm, tau[:, i], rec.band)
        force[:, i] = rec.activation * unit[:, i]
        worst["kkt"] = max(worst["kkt"], *(v for st_ in rec.kkt.values() for v in st_.values()))
        worst["t_star_difference"] = max(worst["t_star_difference"], rec.solvers["t_star_difference"])
        worst["activation_difference"] = max(worst["activation_difference"], rec.solvers["activation_difference"])
    consistency = d1_consistency(name, result, official)
    optimizer_ok = (worst["kkt"] <= params["kkt_tolerance"]
                    and worst["t_star_difference"] <= params["second_solver_t_star_tolerance"]
                    and worst["activation_difference"] <= params["second_solver_activation_tolerance"]
                    and np.all(np.isfinite(act)) and np.all(np.isfinite(reserve)))
    feasible = float(np.max(t_star)) <= params["epsilon_reserve"]
    flagged_samples = np.flatnonzero(t_star > params["epsilon_reserve"])
    status = dict(d1["status"])
    status.update({"d1_consistency": "passed" if consistency <= params["d1_consistency_N_m"] else "failed",
                   "optimizer_verification": "passed" if optimizer_ok else "failed",
                   "muscle_feasibility": "feasible" if feasible else "flagged",
                   "force_law_domain": "flagged" if flags else "in_domain"})
    peak = int(np.argmax(t_star))
    return {
        "body": name, "scale": s, "status": status,
        "body_mass_kg": d1["body_mass_kg"], "stature_m": d1["stature_m"], "foot": d1["foot"],
        "input_traceability": dict(d1["input_traceability"], **trace),
        "d1_checks": d1["checks"], "d1_contact": d1["contact"],
        "verification": {"d1_torque_difference_N_m": consistency, "largest_kkt_residual": worst["kkt"],
                         "second_solver_t_star_difference_N_m": worst["t_star_difference"],
                         "second_solver_activation_difference": worst["activation_difference"],
                         "solvers": {"stage1": "scipy linprog HiGHS dual simplex; second: HiGHS interior point",
                                     "stage2": "quadprog (Goldfarb-Idnani active set); second: Clarabel (interior point)"}},
        "reserve_summary": {
            "norm": "largest absolute per-joint reserve (L-infinity), D-059 Amendment 2",
            "t_star_max_N_m": round(float(np.max(t_star)), 6),
            "t_star_max_time_s": float(result["t"][peak]),
            "q_at_t_star_max_deg": [round(math.degrees(x), 3) for x in q[:, peak]],
            "flagged_samples": int(flagged_samples.size),
            "flagged_time_range_s": ([float(result["t"][flagged_samples[0]]), float(result["t"][flagged_samples[-1]])]
                                     if flagged_samples.size else None),
            "epsilon_reserve_N_m": params["epsilon_reserve"],
            "solver_band_delta_N_m": params["solver_band_delta"],
            "limiting_joints_at_t_star_max": [j for jj, j in enumerate(sq.JOINTS)
                                              if needed[jj, peak] >= t_star[peak] - LIMITING_TOL] if t_star[peak] > 0 else [],
            "limiting_tolerance_N_m": LIMITING_TOL,
            "note": ("t* is the stage-1 optimum; stage-2 reserves are signed, per joint, and may reach t* + delta at "
                     "joints that are not limiting (D-059 Amendment 2; ChatGPT note D2-A2-N01). "
                     "smallest_needed_reserve_per_joint is a diagnostic: the least |reserve| each joint can have while "
                     "all stay within the band; a joint whose value equals t* is limiting")},
        "force_law_domain_flags": flags,
        "path_length_jumps": switch_jumps(acts, joints, np.asarray(d1_params["depth_angles"], float)),
        "actuators": [{"name": a.name, "represents": a.entity, "max_isometric_force_N": a.f0,
                       "optimal_fiber_length_m": round(a.l_opt, 9), "tendon_slack_length_m": round(a.l_ts, 9),
                       "pennation_at_optimal_rad": a.alpha0} for a in acts],
        "series": {
            "t_s": _r(result["t"], 9),
            "q_rad": {j: _r(q[i], 9) for i, j in enumerate(sq.JOINTS)},
            "tau_per_leg_N_m": {j: _r(tau[i]) for i, j in enumerate(sq.JOINTS)},
            "t_star_N_m": _r(t_star, 9),
            "reserve_per_joint_N_m": {j: _r(reserve[i], 9) for i, j in enumerate(sq.JOINTS)},
            "smallest_needed_reserve_per_joint_N_m": {j: _r(needed[i], 9) for i, j in enumerate(sq.JOINTS)},
            "activation": {a.name: _r(act[j]) for j, a in enumerate(acts)},
            "tendon_force_N": {a.name: _r(force[j], 3) for j, a in enumerate(acts)},
            "normalized_fiber_length": {a.name: _r(lnorm[j], 5) for j, a in enumerate(acts)},
            "normalized_fiber_velocity": {a.name: _r(vnorm[j], 5) for j, a in enumerate(acts)},
            "muscle_path_xy_m": drawing,
            "d1_points_m": d1["series"]["points_m"],
        },
    }


def aggregate_status(runs):
    def all_are(key, good):
        return all(r["status"][key] == good for r in runs)
    return {"mechanics_verification": "passed" if all_are("mechanics_verification", "passed") else "failed",
            "contact_feasibility": "feasible" if all_are("contact_feasibility", "feasible") else "flagged",
            "source_validation": SOURCE_VALIDATION["status"],
            "d1_consistency": "passed" if all_are("d1_consistency", "passed") else "failed",
            "optimizer_verification": "passed" if all_are("optimizer_verification", "passed") else "failed",
            "muscle_feasibility": "feasible" if all_are("muscle_feasibility", "feasible") else "flagged",
            "force_law_domain": "in_domain" if all_are("force_law_domain", "in_domain") else "flagged"}


def build_manifest(commit_sha, d1_manifest, config_path=CONFIG):
    cfg, params = load_config(config_path)
    d1_cfg, d1_params = sq.load_config(ROOT / cfg["d1_config"])
    schema = QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    official = json.loads(Path(d1_manifest).read_text(encoding="utf-8"))
    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    paths = dict(INPUTS, d2_config=config_path, config=ROOT / cfg["d1_config"], d1_manifest=Path(d1_manifest))
    manifest = manifest_header(ROOT, {k: str(v) for k, v in paths.items()}, commit_sha)
    runs = [run_body(name, schema, d1_params, d1_cfg["tolerances"], params, official, oracle) for name in cfg["bodies"]]
    acts, _ = m2.load_actuators(1.0, schema)
    manifest.update({
        "status": aggregate_status(runs), "decision": "D-059 (Amendments 1 and 2)", "model_id": cfg["model_id"],
        "d1_official_manifest": {"path": str(Path(d1_manifest)), "commit_sha": official["commit_sha"]},
        "what_the_checks_show": ("Verification that the stated muscle model and recruitment rule are computed correctly "
                                 "(geometry and force law against OpenSim in the test suite; KKT and a second solver "
                                 "here). Muscle forces are a demonstration under a stated criterion; physiological "
                                 "validity is not claimed and no comparison with measured muscle activity is made."),
        "conventions": {"coordinates": "q = (ankle dorsiflexion, knee flexion, hip flexion), radians",
                        "moment_arm": "R = -dL/dq; positive R with positive force increases q",
                        "reserve": "signed, per joint, N m; tau = sum(force x moment arm) + reserve",
                        "fiber_velocity": "lengthening positive; normalized by v_max x l_opt",
                        "muscle_path_xy_m": "active path points per sample and actuator, sagittal projection, metres "
                                            "relative to the ankle centre (same frame as D1's points)"},
        "configuration": cfg,
        "oracle_reference": {"path": str(ORACLE.relative_to(ROOT)), **{k: oracle["provenance"][k] for k in
                             ("opensim_version", "source_model_sha256", "matched_model_sha256")}},
        "d1_simplification_size_gait2392": simplification_size(acts, m2.d1_joints(1.0, schema), oracle),
        "runs": runs,
        "source_validation": SOURCE_VALIDATION,
    })
    return manifest


def summary_lines(manifest):
    lines = []
    for r in manifest["runs"]:
        s, rs = r["status"], r["reserve_summary"]
        lines.append(f"{r['body']}: optimizer {s['optimizer_verification'].upper()}; D1 consistency "
                     f"{s['d1_consistency'].upper()}; muscles {s['muscle_feasibility'].upper()} "
                     f"(t* max {rs['t_star_max_N_m']:.3f} N m at {rs['t_star_max_time_s']:.2f} s); "
                     f"force-law domain {s['force_law_domain'].upper()}; D1 mechanics {s['mechanics_verification']}, "
                     f"contact {s['contact_feasibility']}")
    if exit_code(manifest):
        lines.append("A VERIFICATION FAILED: this manifest must not be used as a result.")
    else:
        lines.append("Verification passed. Muscle forces are a demonstration under a stated criterion, not validated.")
    return lines


def exit_code(manifest):
    s = manifest["status"]
    ok = (s["mechanics_verification"] == "passed" and s["d1_consistency"] == "passed"
          and s["optimizer_verification"] == "passed")
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--commit-sha", required=True)
    p.add_argument("--d1-manifest", type=Path, required=True)
    p.add_argument("--config", type=Path, default=CONFIG)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    manifest = build_manifest(args.commit_sha, args.d1_manifest, args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Compact JSON (one line): the per-sample muscle paths make an indented file about five times larger.
    args.output.write_text(json.dumps(manifest, sort_keys=True, allow_nan=False, separators=(",", ":")) + "\n",
                           encoding="utf-8")
    for line in summary_lines(manifest):
        print(line)
    print("Manifest written to", args.output)
    sys.exit(exit_code(manifest))


if __name__ == "__main__":
    main()
