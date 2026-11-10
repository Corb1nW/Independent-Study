"""Stage D2 sensitivity analysis (D-059 item 9, Amendment 1), one change at a time.

    python -m tools.sensitivity_d2 --commit-sha FULL_SHA --output results/phase_d/<date>_d2_sensitivity_<sha>.json \\
        --markdown results/phase_d/<date>_d2_sensitivity_<sha>.md

Cases, each against the baseline of tools/run_phase_d2.py:
  passive_on          passive fiber force on (strain 0.6, damping 0), rigid tendon; the passive torque is a known
                      offset moved to the right-hand side, so both stages keep their form
  f0_mass_scaled      female and male maximum isometric forces scaled by body mass / 75.16 kg
  exponent_3          stage 2 minimizes the sum of activation cubed (scipy SLSQP from the quadratic solution);
                      stage 1 unchanged; this case is not KKT-certified like the baseline
  unmodified_geometry Gait2392 body: lengths and moment arms from OpenSim on the UNMODIFIED model file (oracle
                      reference, every 10th sample), D1's torques unchanged; mixes geometries, so an estimate
  compliant_tendon    bottom pose only, soleus and gastrocnemius: rigid-tendon fiber state against the compliant
                      equilibrium (De Groote tendon curve, strain 0.049) at the same activation and path length,
                      passive force on in both
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, minimize

from src import muscles_d2 as m2
from src import squat_d1 as sq
from src.quantitative import QuantitativeSchema
from src.run_manifest import manifest_header
from tools import run_phase_d2 as d2r

ROOT = sq.ROOT
GAIT2392_MASS = 75.16   # kg, documented (segments_gait2392.yaml, LB-QD:G2392:BODY_MASS)
INPUTS = dict(d2r.INPUTS, sensitivity_tool=ROOT / "tools/sensitivity_d2.py")
INPUTS.pop("runner", None)
INPUTS["d2_runner"] = ROOT / "tools/run_phase_d2.py"


def coefficients(acts, joints, q, qd, f0_scale=1.0, passive=False, strain=0.6, geometry=None):
    k = len(acts)
    Cm, offset = np.zeros((3, k)), np.zeros(3)
    for j, a in enumerate(acts):
        if geometry is None:
            L, R, _ = m2.path(a, q, joints)
        else:
            L, R = geometry["length_m"][a.name], np.array(geometry["moment_arm_m"][a.name])
        st = m2.fiber_state(a, L, -R @ qd)
        Cm[:, j] = f0_scale * m2.unit_tendon_force(a, st) * R
        if passive:
            offset += f0_scale * m2.passive_tendon_force(a, st, strain) * R
    return Cm, offset


def stage2_cubic(Cm, tau, band, start):
    cons = {"type": "ineq", "fun": lambda a: np.r_[band - tau + Cm @ a, band + tau - Cm @ a],
            "jac": lambda a: np.vstack((Cm, -Cm))}
    res = minimize(lambda a: np.sum(a ** 3), start, jac=lambda a: 3 * a ** 2, bounds=[(0.0, 1.0)] * len(start),
                   constraints=cons, method="SLSQP", options={"ftol": 1e-12, "maxiter": 1000})
    return np.clip(res.x, 0, 1), bool(res.success)


def solve_case(acts, joints, q, qd, tau, delta, **kw):
    t_star = np.zeros(q.shape[1]); acts_out = np.zeros((len(acts), q.shape[1])); ok = True
    cubic = kw.pop("cubic", False)
    for i in range(q.shape[1]):
        Cm, offset = coefficients(acts, joints, q[:, i], qd[:, i], **kw)
        target = tau[:, i] - offset
        rec = m2.recruit(Cm, target, delta=delta, second_solver=False)
        a = rec.activation
        if cubic:
            a, success = stage2_cubic(Cm, target, rec.band, rec.activation)
            ok &= success
        t_star[i], acts_out[:, i] = rec.t_star, a
    return t_star, acts_out, ok


def tendon_multiplier(norm_tendon_length, strain):
    c1, c2, c3 = m2.C["c1"], m2.C["c2"], m2.C["c3"]
    kT = math.log((1.0 + c3) / c1) / (1.0 + strain - c2)
    return c1 * math.exp(kT * (norm_tendon_length - c2)) - c3


def compliant_equilibrium(a, act, L, strain=0.049, passive_strain=0.6):
    """Fiber length where fiber force along the tendon equals tendon force (static, f_v = 1)."""
    h = a.l_opt * math.sin(a.alpha0)

    def parts(l_m):
        cos_a = math.sqrt(l_m * l_m - h * h) / l_m
        ln = l_m / a.l_opt
        fiber = a.f0 * (act * float(m2.f_active(ln)) + max(0.0, float(m2.f_passive(ln, passive_strain)))) * cos_a
        tendon = a.f0 * max(0.0, tendon_multiplier((L - l_m * cos_a) / a.l_ts, strain))
        return fiber, tendon, cos_a, ln
    rigid = math.hypot(L - a.l_ts, h)
    lo = h * (1 + 1e-9)
    l_m = brentq(lambda x: parts(x)[0] - parts(x)[1], lo, rigid, xtol=1e-14)
    fiber, tendon, cos_a, ln = parts(l_m)
    rf, _, rc, rln = parts(rigid)
    return {"rigid": {"normalized_fiber_length": rln, "tendon_force_N": rf},
            "compliant": {"normalized_fiber_length": ln, "tendon_force_N": tendon,
                          "tendon_strain": (L - l_m * cos_a) / a.l_ts - 1.0,
                          "equilibrium_residual_N": abs(fiber - tendon),
                          "in_curve_domain": m2.MIN_NORM_FIBER_LENGTH <= ln <= m2.MAX_NORM_FIBER_LENGTH}}


def build(commit_sha):
    cfg, params = d2r.load_config()
    d1_cfg, d1_params = sq.load_config(ROOT / cfg["d1_config"])
    schema = QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    oracle = json.loads(d2r.ORACLE.read_text(encoding="utf-8"))
    out = manifest_header(ROOT, {k: str(v) for k, v in INPUTS.items()}, commit_sha)
    delta = params["solver_band_delta"]
    results = {}
    for name in cfg["bodies"]:
        body = sq.build_body(name, schema)
        res = sq.run(body, d1_params)
        q, qd, tau = res["q"], res["qd"], res["tau"]
        s = d2r.body_scale(body)
        acts, _ = m2.load_actuators(s, schema)
        joints = m2.d1_joints(s, schema)
        base_t, base_a, _ = solve_case(acts, joints, q, qd, tau, delta)
        cases = {"passive_on": dict(passive=True, strain=params["passive_strain_sensitivity"]),
                 "exponent_3": dict(cubic=True)}
        if name != "gait2392":
            cases["f0_mass_scaled"] = dict(f0_scale=body.body_mass / GAIT2392_MASS)
        r = {"baseline": {"t_star_max_N_m": float(base_t.max()), "t_star_max_time_s": float(res["t"][base_t.argmax()])}}
        for case, kw in cases.items():
            t_, a_, ok = solve_case(acts, joints, q, qd, tau, delta, **kw)
            r[case] = {"t_star_max_N_m": float(t_.max()), "t_star_max_time_s": float(res["t"][t_.argmax()]),
                       "flagged_samples": int(np.sum(t_ > params["epsilon_reserve"])),
                       "largest_activation_change": float(np.max(np.abs(a_ - base_a))),
                       "solver_converged_everywhere": ok}
        if "f0_mass_scaled" in r:
            r["f0_mass_scaled"]["force_scale"] = body.body_mass / GAIT2392_MASS
        if name == "gait2392":
            idx = [row["index"] for row in oracle["unmodified_geometry"]]
            t_u, t_b = [], []
            for row in oracle["unmodified_geometry"]:
                i = row["index"]
                Cm, _ = coefficients(acts, joints, q[:, i], qd[:, i], geometry=row)
                t_u.append(m2.recruit(Cm, tau[:, i], delta=delta, second_solver=False).t_star)
                t_b.append(base_t[i])
            r["unmodified_geometry"] = {
                "samples": idx, "t_star_N_m": [round(x, 6) for x in t_u],
                "baseline_t_star_at_same_samples_N_m": [round(float(x), 6) for x in t_b],
                "t_star_max_N_m": float(max(t_u)),
                "note": ("Lengths and moment arms from OpenSim on the published model (moving knee, oblique ankle); "
                         "torques still from D1's fixed-centre knee, so the case mixes geometries and is an estimate")}
        bottom = int(np.argmax(q[1]))
        comp = {}
        for a in acts:
            if a.name in ("soleus_r", "med_gas_r", "lat_gas_r"):
                L, _, _ = m2.path(a, q[:, bottom], joints)
                comp[a.name] = compliant_equilibrium(a, float(base_a[[x.name for x in acts].index(a.name), bottom]), L)
                comp[a.name]["activation"] = float(base_a[[x.name for x in acts].index(a.name), bottom])
        r["compliant_tendon"] = {"sample": bottom, "time_s": float(res["t"][bottom]),
                                 "held_fixed": "activation (rigid baseline value) and path length; passive force on in both; static (f_v = 1)",
                                 "tendon_strain_at_one_norm_force": 0.049, "by_actuator": comp}
        results[name] = r
    out.update({"decision": "D-059 item 9 (Amendment 1)", "cases": results,
                "what_it_shows": "How much each declared simplification moves the D2 results; not validation."})
    return out


def markdown(res):
    lines = [f"# Stage D2 sensitivity at `{res['commit_sha'][:7]}`", "",
             "Largest per-joint reserve t* (N·m) over the squat; baseline flagged above 1 N·m. One change at a time.", "",
             "| Body | Baseline | Passive on | Exponent 3 | Force by mass | Unmodified geometry |", "|---|---|---|---|---|---|"]
    for body, r in res["cases"].items():
        cell = lambda k: f"{r[k]['t_star_max_N_m']:.3f}" if k in r else "—"  # noqa: E731
        lines.append(f"| {body} | {cell('baseline')} | {cell('passive_on')} | {cell('exponent_3')} | "
                     f"{cell('f0_mass_scaled')} | {cell('unmodified_geometry')} |")
    lines += ["", "Compliant tendon at the bottom pose (normalized fiber length, rigid → compliant; tendon force, N):", ""]
    for body, r in res["cases"].items():
        for n, c in r["compliant_tendon"]["by_actuator"].items():
            lines.append(f"- {body} {n}: {c['rigid']['normalized_fiber_length']:.3f} → "
                         f"{c['compliant']['normalized_fiber_length']:.3f}; {c['rigid']['tendon_force_N']:.0f} → "
                         f"{c['compliant']['tendon_force_N']:.0f} N (strain {c['compliant']['tendon_strain']:.4f}, "
                         f"residual {c['compliant']['equilibrium_residual_N']:.1e} N)")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--commit-sha", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--markdown", type=Path)
    args = p.parse_args()
    res = build(args.commit_sha)
    args.output.write_text(json.dumps(res, indent=1, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.write_text(markdown(res), encoding="utf-8")
    print(markdown(res))


if __name__ == "__main__":
    sys.exit(main())
