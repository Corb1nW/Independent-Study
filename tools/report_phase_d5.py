"""Stage D5 results report (D-063 item 9 and A8), computed only from two committed run manifests.

Reads the official squat_d5 manifest (43 actuators) and the official D4 manifest it is compared with (squat_d4_iliopsoas,
16 actuators) and reports, per body and knee variant:
  - feasibility and the largest reserve t* in each run;
  - on the moving knee (the variant whose series are stored), each actuator's peak activation and its time, side by side
    for the 16 actuators the two runs share, and for the 27 actuators only D5 has;
  - each actuator's share of each coordinate's muscle moment (D5 only), and the summed share of the hip abductors and
    rotators that D-063 item 4 names as acting sagittally only because the model is planar;
  - the pre-stated hypotheses H2-H4, reported either way. They are not acceptance criteria.

Nothing is re-simulated: every number comes from the two manifests, whose SHA-256 the report records.

    python -m tools.report_phase_d5 --d5 results/phase_d/<d5 manifest> --d4 results/phase_d/<d4 manifest> \
        --output results/phase_d/<report>.json
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# D-063 item 4: hip abductors and rotators included although their sagittal action is a planar-model artifact.
OUT_OF_PLANE = ("glut_med1_r", "glut_med2_r", "glut_med3_r", "glut_min1_r", "glut_min2_r", "glut_min3_r",
                "peri_r", "gem_r", "quad_fem_r", "tfl_r")
H3_BODIES = ("male", "gait2392")
H3_ACTUATORS = ("glut_max2_r", "glut_max3_r")      # middle and lower gluteus maximus (D-063 item 9)
H4_BODIES = ("male", "gait2392")
FULL = 1.0
TOP = 5                                            # actuators listed per coordinate in the share summary


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _runs(manifest):
    return {(r["body"], r["variant"]): r for r in manifest["runs"]}


def _peaks(run):
    """{actuator name: (peak activation, time s)} from a run's stored series (moving knee only)."""
    s = run.get("series")
    if not s:
        return None
    t = s["t_s"]
    out = {}
    for name, a in s["activation"].items():
        i = max(range(len(a)), key=lambda k: a[k])
        out[name] = {"peak": a[i], "time_s": t[i]}
    return out


def _feasibility(run, band):
    rs = run["reserve_summary"]
    return {"t_star_max_N_m": rs["t_star_max_N_m"], "t_star_max_time_s": rs["t_star_max_time_s"],
            "flagged_samples": rs["flagged_samples"], "feasible_throughout": rs["t_star_max_N_m"] <= band,
            "muscle_feasibility": run["status"]["muscle_feasibility"]}


def _shares(run):
    out = {}
    for coord, acts in run["torque_shares"].items():
        ranked = sorted(acts.items(), key=lambda kv: -kv[1]["share"])
        out[coord] = {"top": [{"actuator": a, **v} for a, v in ranked[:TOP]],
                      "out_of_plane_share": sum(v["share"] for a, v in acts.items() if a in OUT_OF_PLANE),
                      "out_of_plane_by_actuator": {a: acts[a]["share"] for a in OUT_OF_PLANE if a in acts}}
    return out


def build_report(d5_path, d4_path):
    d5, d4 = (json.loads(Path(p).read_text(encoding="utf-8")) for p in (d5_path, d4_path))
    if d5["specification"]["name"] != "squat_d5" or d4["specification"]["name"] != "squat_d4_iliopsoas":
        raise ValueError("expected a squat_d5 manifest and a squat_d4_iliopsoas manifest")
    for name, m in (("d5", d5), ("d4", d4)):
        if m["commit_provenance_status"] != "verified_git_head_and_inputs":
            raise ValueError(f"{name} manifest is not an official run: {m['commit_provenance_status']}")
    band = d5["d2_configuration"]["parameters"]["solver_band_delta"]["value"]
    r5, r4 = _runs(d5), _runs(d4)
    if set(r5) != set(r4):
        raise ValueError("the two manifests do not cover the same bodies and variants")
    names4 = {a["name"] for r in d4["runs"] for a in r["actuators"]}
    names5 = {a["name"] for r in d5["runs"] for a in r["actuators"]}
    if not names4 < names5:
        raise ValueError("the D4 actuators are not a subset of the D5 actuators")

    cases = {}
    for key in sorted(r5):
        body, variant = key
        case = {"actuators": {"d4": len(r4[key]["actuators"]), "d5": len(r5[key]["actuators"])},
                "feasibility": {"d4": _feasibility(r4[key], band), "d5": _feasibility(r5[key], band)},
                "torque_shares_d5": _shares(r5[key])}
        p4, p5 = _peaks(r4[key]), _peaks(r5[key])
        if p4 is not None and p5 is not None:
            case["peak_activation"] = {
                "shared": {n: {"d4": p4[n], "d5": p5[n]} for n in sorted(names4)},
                "added_in_d5": {n: p5[n] for n in sorted(names5 - names4)}}
        cases[f"{body} | {variant}"] = case

    moving = [k for k in r5 if k[1] == "moving_knee"]
    h2_values = {b: r5[(b, v)]["reserve_summary"]["t_star_max_N_m"] for b, v in sorted(moving)}
    h2 = {"id": "H2", "statement": "On the moving knee, all three bodies stay feasible with 43 actuators (t* = 0 "
                                   "throughout).",
          "measure": f"largest t* per body, compared with the solver band delta {band} N m",
          "values_N_m": h2_values, "outcome": "supported" if all(v <= band for v in h2_values.values())
          else "not supported"}

    h3_values = {}
    for b in H3_BODIES:
        p4, p5 = _peaks(r4[(b, "moving_knee")]), _peaks(r5[(b, "moving_knee")])
        h3_values[b] = {a: {"d4": p4[a], "d5": p5[a]} for a in H3_ACTUATORS}
    full_in_d4 = all(v["d4"]["peak"] >= FULL - 1e-6 for b in h3_values.values() for v in b.values())
    below_in_d5 = all(v["d5"]["peak"] < FULL - 1e-6 for b in h3_values.values() for v in b.values())
    h3 = {"id": "H3", "statement": "For the male and Gait2392 bodies, whose middle and lower gluteus maximus reach full "
                                   "activation near the bottom in D4, those parts' peak activation falls below 1.0 "
                                   "once the adductor magnus and the other hip extensors are available.",
          "measure": "peak activation over the whole moving-knee squat (a full-run peak, stricter than 'near the "
                     "bottom'); full means within 1e-6 of 1.0",
          "premise_holds_in_d4": full_in_d4, "values": h3_values,
          "outcome": "supported" if (full_in_d4 and below_in_d5) else "not supported"}

    h4_values = {b: {"d4": r4[(b, "fixed_knee")]["reserve_summary"]["t_star_max_N_m"],
                     "d5": r5[(b, "fixed_knee")]["reserve_summary"]["t_star_max_N_m"]} for b in H4_BODIES}
    decreased = all(v["d5"] < v["d4"] for v in h4_values.values())
    h4 = {"id": "H4", "statement": "The fixed-knee shortfall of the male and Gait2392 bodies (largest reserve 5.815 and "
                                   "6.362 N m in D2 and D4) decreases. Whether it reaches zero is reported.",
          "measure": "largest t* on the fixed knee, D4 against D5",
          "values_N_m": h4_values, "outcome": "supported" if decreased else "not supported",
          "reaches_zero": {b: v["d5"] <= band for b, v in h4_values.items()}}

    return {
        "report": "PHASE_D5_RESULTS",
        "decision": "D-063 (item 9, A8)",
        "note": "Pre-stated hypotheses, reported either way; not acceptance criteria. A demonstration under stated "
                "assumptions; physiological validity not established.",
        "inputs": {"d5_manifest": {"path": str(d5_path), "sha256": _sha256(d5_path), "commit_sha": d5["commit_sha"]},
                   "d4_manifest": {"path": str(d4_path), "sha256": _sha256(d4_path), "commit_sha": d4["commit_sha"]}},
        "out_of_plane_actuators": list(OUT_OF_PLANE),
        "hypotheses": [h2, h3, h4],
        "cases": cases,
    }


def summary_lines(rep):
    lines = []
    for h in rep["hypotheses"]:
        lines.append(f"{h['id']}: {h['outcome'].upper()}")
    for h in rep["hypotheses"]:
        if h["id"] == "H2":
            lines += [f"  H2 {b}: t* max {v:.3f} N m" for b, v in h["values_N_m"].items()]
        if h["id"] == "H3":
            for b, acts in h["values"].items():
                lines += [f"  H3 {b} {a}: peak {v['d4']['peak']:.3f} (D4) -> {v['d5']['peak']:.3f} (D5)"
                          for a, v in acts.items()]
        if h["id"] == "H4":
            lines += [f"  H4 {b}: t* max {v['d4']:.3f} -> {v['d5']:.3f} N m" for b, v in h["values_N_m"].items()]
    for case, c in rep["cases"].items():
        for coord, s in c["torque_shares_d5"].items():
            if s["out_of_plane_share"] > 0:
                lines.append(f"  {case} {coord.split(':')[-1]}: out-of-plane share {s['out_of_plane_share']:.3f}")
    return lines


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--d5", type=Path, required=True)
    p.add_argument("--d4", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    rep = build_report(args.d5, args.d4)
    args.output.write_text(json.dumps(rep, sort_keys=True, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    for line in summary_lines(rep):
        print(line)
    print("Report written to", args.output)


if __name__ == "__main__":
    sys.exit(main())
