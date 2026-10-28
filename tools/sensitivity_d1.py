"""Sensitivity of the Stage D1 results to its modeling assumptions (D-058 Amendment 3, review D1-R05).

    python -m tools.sensitivity_d1 --output results/phase_d/<date>_d1_sensitivity_<shortsha>.json

Each case changes ONE assumption and reruns the same prescribed squat. The size of each
change is stated with its basis; sizes marked "demonstration" are round values chosen to
show sensitivity, not estimates of real uncertainty. Reported: signed peak torque per
joint and leg, the centre-of-pressure range, the smallest distance from the centre of
pressure to the edge of the support, and whether the squat stays contact-feasible.
"""
import argparse
import copy
import json
import math

import numpy as np

from src import squat_d1 as sq
from src.quantitative import QuantitativeSchema
from tools import build_segment_datasets as bsd

ROOT = sq.ROOT
CONFIG = ROOT / "config" / "phase_d1_squat.yaml"

# Knee centre at 100 deg flexion (the squat's depth) from the Gait2392 knee spline:
# translation2 knots (-2.0944, -0.4226) and (-1.22173, -0.4082), evaluated at -1.745329 rad.
KNEE_Y_100 = -0.4082 + (-0.4226 + 0.4082) * ((-1.7453292519943295 + 1.22173) / (-2.0944 + 1.22173))


def _with_thigh_length_change(body, delta):
    b = copy.deepcopy(body)
    s = b.segments["thigh"]
    length = float(np.hypot(*s.upper))
    new_upper = s.upper * (1 + delta / length)
    s.com = new_upper - (s.upper - s.com)   # centre of mass keeps its distance from the hip
    s.upper = new_upper
    return b


def _with_hat(body, dx=0.0, inertia_factor=1.0):
    b = copy.deepcopy(body)
    h = b.segments["hat"]
    h.com = h.com + np.array([dx, 0.0])
    h.inertia = h.inertia * inertia_factor
    return b


def _with_support(body, heel_dx=0.0, ball_dx=0.0):
    b = copy.deepcopy(body)
    b.foot.heel = b.foot.heel + np.array([heel_dx, 0.0])
    b.foot.ball = b.foot.ball + np.array([ball_dx, 0.0])
    return b


def _with_sagittal_radius(body, sex):
    b = copy.deepcopy(body)
    rows = bsd.read_bmc(bsd.BMC[sex])
    for seg, row in (("thigh", "Thigh"), ("shank", "Shank")):
        s = b.segments[seg]
        length = float(np.hypot(*s.upper))
        s.inertia = s.mass * (float(rows[row]["rg_sag"]) * length) ** 2
    return b


def cases(name, schema, base):
    yield "baseline", "as configured", base
    if name in ("female", "male"):
        yield ("gait2392_stature_1.66m",
               "scale factor uses 1.66 m (forum measurement of the model geometry) instead of the documented 1.8 m",
               sq.build_body(name, schema, gait2392_stature=1.66))
        yield ("radius_sagittal_column",
               "thigh and shank inertia from de Leva's 'sagittal' radius instead of the 'transverse' one",
               _with_sagittal_radius(base, name))
    delta = abs(KNEE_Y_100) - 0.39590120267799883
    scale = base.stature / sq.gait2392_geometry(schema)[0]["stature"] if name != "gait2392" else 1.0
    yield ("knee_centre_at_100deg",
           f"thigh {1000 * delta * scale:.1f} mm longer: Gait2392 knee centre at 100 deg flexion instead of 0 deg",
           _with_thigh_length_change(base, delta * scale))
    for dx in (-0.02, 0.02):
        yield (f"hat_com_{'+' if dx > 0 else '-'}2cm", f"HAT centre of mass {dx * 100:+.0f} cm anterior (demonstration)",
               _with_hat(base, dx=dx))
    for f in (0.8, 1.2):
        yield (f"hat_inertia_x{f}", f"HAT inertia x {f} (demonstration)", _with_hat(base, inertia_factor=f))
    yield "heel_1cm_forward", "heel edge of the support 1 cm further forward (demonstration)", _with_support(base, heel_dx=0.01)
    yield "toes_3cm", "support extended 3 cm past the MTP joint onto the toes (demonstration)", _with_support(base, ball_dx=0.03)


def summarize(body, params, ref_tau=None):
    r = sq.run(body, params)
    c = r["contact"]
    peaks = {j: float(r["tau"][i][np.argmax(np.abs(r["tau"][i]))]) for i, j in enumerate(sq.JOINTS)}
    cop = r["cop_x"][np.isfinite(r["cop_x"])]
    margin = float(min(np.min(cop - c["support_heel_m"]), np.min(c["support_ball_m"] - cop))) if cop.size else None
    change = ({j: round(float(np.max(np.abs(r["tau"][i] - ref_tau[i]))), 3) for i, j in enumerate(sq.JOINTS)}
              if ref_tau is not None else {j: 0.0 for j in sq.JOINTS})
    return {"tau": r["tau"], "peak_tau_per_leg_N_m": {k: round(v, 3) for k, v in peaks.items()},
            "largest_change_at_any_instant_N_m": change,
            "cop_range_m": [None if c["cop_min_m"] is None else round(c["cop_min_m"], 4),
                            None if c["cop_max_m"] is None else round(c["cop_max_m"], 4)],
            "min_support_margin_m": None if margin is None else round(margin, 4),
            "contact_feasible": c["feasible"]}


def analyse():
    cfg, params = sq.load_config(CONFIG)
    schema = QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    out = {"what": __doc__.strip().splitlines()[0], "bodies": {}}
    for name in cfg["bodies"]:
        base = sq.build_body(name, schema)
        rows = []
        ref = None
        for key, desc, body in cases(name, schema, base):
            s = summarize(body, params, None if ref is None else ref["tau"])
            if ref is None:
                ref = s
            # Knee torque keeps one sign through the squat, so its peak change is a fair percentage;
            # hip and ankle pass near zero, so only absolute changes are reported for them.
            s["knee_peak_change_pct"] = round(100 * (s["peak_tau_per_leg_N_m"]["knee"] / ref["peak_tau_per_leg_N_m"]["knee"] - 1), 2)
            rows.append({"case": key, "change": desc, **s})
        for row in rows:
            row.pop("tau")
        out["bodies"][name] = rows
    return out


def markdown(result):
    lines = []
    for name, rows in result["bodies"].items():
        lines += [f"**{name}**", "", "| Case | Change | Largest change at any instant, ankle / knee / hip (N·m) | Knee peak (N·m) | Knee peak change | Smallest support margin | Feasible |",
                  "|---|---|---|---|---|---|---|"]
        for r in rows:
            p = r["peak_tau_per_leg_N_m"]
            m = r["min_support_margin_m"]
            ch = r["largest_change_at_any_instant_N_m"]
            lines.append(f"| {r['case']} | {r['change']} | {ch['ankle']:.1f} / {ch['knee']:.1f} / {ch['hip']:.1f} | "
                         f"{p['knee']:.1f} | {r['knee_peak_change_pct']:+.1f}% | "
                         f"{'n/a' if m is None else f'{m * 1000:.1f} mm'} | {'yes' if r['contact_feasible'] else 'NO'} |")
        lines.append("")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--output", required=True)
    args = p.parse_args()
    result = analyse()
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, allow_nan=False)
        fh.write("\n")
    print(markdown(result))


if __name__ == "__main__":
    main()
