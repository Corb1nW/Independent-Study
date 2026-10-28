"""Run the Stage D1 squat for every configured body and write one manifest (D-058).

    python -m tools.run_phase_d1 --commit-sha FULL_40_CHAR_SHA --output results/phase_d/<date>_d1_runs_<shortsha>.json

The manifest records the commit and every consumed file (shared manifest, D-055 C1),
the traceability report for every sourced input (C4), how each body was built, the
demonstration assumptions, the time series, the contact-feasibility results, and the
residual of every mechanics check for this run. The checks verify idealized mechanics;
they are not validation against measured squats (D-058 Amendment 1, A3).
"""
import argparse
from pathlib import Path

import numpy as np

from src import squat_d1 as sq
from src.quantitative import QuantitativeSchema
from src.run_manifest import manifest_header, serialize_manifest

ROOT = sq.ROOT
CONFIG = ROOT / "config" / "phase_d1_squat.yaml"
INPUTS = {
    "config": CONFIG,
    "dataset_gait2392": ROOT / "ontology/quantitative_data/segments_gait2392.yaml",
    "dataset_de_leva": ROOT / "ontology/quantitative_data/segments_de_leva_1996.yaml",
    "ontology_hip": ROOT / "ontology/hip.yaml",
    "ontology_lower_limb": ROOT / "ontology/lower_limb_sagittal.yaml",
    "schema": ROOT / "ontology/quantitative_schema.yaml",
    "source_gait2392_osim": ROOT / "sources/vendor/opensim-models/gait2392_millard2012muscle.osim",
    "source_bmc_female": ROOT / "sources/vendor/bmc/BSPfemale_ZdeLeva.txt",
    "source_bmc_male": ROOT / "sources/vendor/bmc/BSPmale_ZdeLeva.txt",
    "dataset_builder": ROOT / "tools/build_segment_datasets.py",
    "model": ROOT / "src/squat_d1.py",
    "validator": ROOT / "src/quantitative.py",
    "ontology_loader": ROOT / "src/ontology.py",
    "structural_model": ROOT / "src/datum_model.py",
    "input_gate": ROOT / "src/input_gate.py",
    "run_manifest": ROOT / "src/run_manifest.py",
    "runner": ROOT / "tools/run_phase_d1.py",
}


def _round(a, digits=9):
    return np.round(np.asarray(a, float), digits).tolist()


def check_residuals(body, params, result):
    """Residual of each mechanics check on this run's samples (Amendment 1, A3)."""
    g = params["gravity"]
    q, qd, qdd, tau = result["q"], result["qd"], result["qdd"], result["tau"]
    res = sq.inverse_dynamics(body, q, qd, qdd, g)
    k = res["kinematics"]
    m, _, acc = sq.whole_body_com(body, k)
    per_leg = body.foot.mass * g + sum(body.segments[n].mass * (g + k[f"com_{n}"][2][1]) for n in sq.MOVING)
    static = max(float(np.max(np.abs(sq.inverse_dynamics(body, qq[:, None], np.zeros((3, 1)), np.zeros((3, 1)), g)["tau"][:, 0]
                                      - sq.static_torques(body, qq, g)))) for qq in q[:, ::30].T)
    return {
        "newton_euler_vs_lagrange_N_m": float(np.max(np.abs(tau - sq.lagrange_torques(body, q, qd, qdd, g)))),
        "static_oracle_N_m": static,
        "energy_W": float(np.max(np.abs(np.sum(tau * qd, axis=0) - sq.energy_rate(body, q, qd, qdd, g)))),
        "newton_identity_per_leg_N": float(np.max(np.abs(res["grf"][1] - per_leg))),
        "newton_identity_whole_body_N": float(np.max(np.abs(2 * res["grf"][1] - m * (g + acc[1])))),
        "round_trip_one_step_rad_at_1ms": sq.rk4_round_trip(body, result["motion"], g, 0.001),
        "mass_bookkeeping_relative": float(2 * body.per_leg_mass() / body.body_mass - 1),
    }


def run_body(name, schema, params, tolerances):
    body = sq.build_body(name, schema)
    trace = sq.traceability(body, schema)
    result = sq.run(body, params)
    checks = check_residuals(body, params, result)
    limits = dict(tolerances)
    passed = {key: abs(value) <= limits[key] for key, value in checks.items() if key in limits}
    passed["newton_identity_per_leg_N"] = checks["newton_identity_per_leg_N"] <= limits["newton_identity_N"]
    passed["newton_identity_whole_body_N"] = checks["newton_identity_whole_body_N"] <= limits["newton_identity_N"]
    passed["mass_bookkeeping_relative"] = abs(checks["mass_bookkeeping_relative"]) <= limits["mass_fraction_sum"]
    seg = {n: {"mass_kg": s.mass, "inertia_kg_m2": s.inertia, "com_m": _round(s.com), "upper_joint_m": _round(s.upper)}
           for n, s in body.segments.items()}
    pts = result["points"]
    hat_top = pts["hip"] + np.einsum("ijn,j->in", np.stack([
        np.stack([np.cos(result["phi"][2]), -np.sin(result["phi"][2])]),
        np.stack([np.sin(result["phi"][2]), np.cos(result["phi"][2])])]), 2 * body.segments["hat"].com)
    return {
        "body": name, "body_mass_kg": body.body_mass, "stature_m": body.stature,
        "segments_per_leg": seg,
        "foot": {"mass_kg": body.foot.mass, "com_m": _round(body.foot.com), "heel_m": _round(body.foot.heel),
                 "ball_m": _round(body.foot.ball), "ground_y_m": body.foot.ground_y},
        "how_built": body.derivations,
        "input_traceability": trace,
        "checks": {"residuals": checks, "passed": passed, "all_passed": all(passed.values())},
        "contact": result["contact"],
        "series": {
            "t_s": _round(result["t"]),
            "q_rad": {j: _round(result["q"][i]) for i, j in enumerate(sq.JOINTS)},
            "tau_per_leg_N_m": {j: _round(result["tau"][i], 6) for i, j in enumerate(sq.JOINTS)},
            "grf_per_leg_N": {"x": _round(result["grf"][0], 6), "y": _round(result["grf"][1], 6)},
            "cop_x_m": _round(result["cop_x"]),
            "points_m": {key: {"x": _round(v[0], 6), "y": _round(v[1], 6)}
                         for key, v in dict(pts, hat_drawing_top=hat_top).items()},
        },
    }


def build_manifest(commit_sha, config_path=CONFIG):
    cfg, params = sq.load_config(config_path)
    schema = QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    paths = dict(INPUTS, config=config_path)
    manifest = manifest_header(ROOT, {k: str(v) for k, v in paths.items()}, commit_sha)
    manifest.update({
        "decision": "D-058 (Amendments 1 and 2)", "model_id": cfg["model_id"],
        "what_the_checks_show": ("Verification of idealized mechanics: the equations of the stated model are solved "
                                 "correctly. Not validation against measured squats."),
        "conventions": {"frame": "Gait2392 body frames: x anterior, y superior, z right; angles counter-clockwise about z",
                        "coordinates": "q = (ankle dorsiflexion, knee flexion, hip flexion), radians, zero in the Gait2392 default pose",
                        "torque": "generalized force conjugate to each coordinate, per leg; positive acts to increase the coordinate",
                        "points": "positions relative to the ankle centre, metres"},
        "configuration": cfg,
        "runs": [run_body(name, schema, params, cfg["tolerances"]) for name in cfg["bodies"]],
        "hat_drawing_note": "hat_drawing_top = hip + 2 x HAT centre-of-mass vector: for drawing the upper body only, not a landmark",
    })
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--commit-sha", required=True)
    p.add_argument("--config", type=Path, default=CONFIG)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    manifest = build_manifest(args.commit_sha, args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialize_manifest(manifest), encoding="utf-8")
    for run in manifest["runs"]:
        print(f"{run['body']}: checks {'passed' if run['checks']['all_passed'] else 'FAILED'}, "
              f"contact {'feasible' if run['contact']['feasible'] else 'FLAGGED'}")
    print("Manifest written to", args.output, "(idealized mechanics verified; not validated against measured squats)")


if __name__ == "__main__":
    main()
