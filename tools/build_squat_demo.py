"""Build the squat demonstration page: SQUAT_DEMO.html, one self-contained file at the repository root.

    python -m tools.build_squat_demo
    python -m tools.build_squat_demo --d1 <d1 manifest> --d2 <d2 manifest> --d3 <d3 manifest> --output SQUAT_DEMO.html

A presentation of Phase D so far (Stages D1-D3) for readers new to the project: the squat played back
with its muscles, what went into the model, how it was built and checked, what it leaves out, and how it
serves the project's goals.

Presentation only. It changes no model, data or result. Where the numbers come from:
- simulation series, statuses, checks, parameters and declared simplifications: copied from the three
  official run manifests (rounded for display);
- ontology entities, relationships and evidence: read from ontology/*.yaml;
- source titles and links: read from sources/SOURCES.md (the build fails if a listed source is missing);
- peak moment arms on the muscle cards: computed here with src/muscles_d2.py on the Gait2392 body with
  the moving knee, over the D3 motion (derived, labelled as such on the page);
- counts of decisions, owner answers and review records: counted from docs/;
- independent-reproduction records: quoted from PROJECT_STATE.md, with their PR numbers (RECORDS below).
"""
import argparse
import dataclasses
import json
import re
from pathlib import Path

import numpy as np
import yaml

from tools.build_d2_page import GROUPS, NAMES

ROOT = Path(__file__).resolve().parents[1]
D1 = "results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json"
D2 = "results/phase_d/2026-11-10_d2_muscle_runs_7ac0f2d.json"
D3 = "results/phase_d/2026-11-11_d3_moving_knee_runs_d3efc56.json"
FULL_VIEWER = "results/phase_d/2026-11-11_d3_muscle_viewer_d3efc56.html"
LABELS = {"female": "Female", "male": "Male", "gait2392": "Gait2392"}
LONG = {"female": "de Leva (1996) female reference body", "male": "de Leva (1996) male reference body",
        "gait2392": "OpenSim Gait2392 generic model"}
JOINT_ORDER = ["ankle", "knee", "hip"]          # manifest convention: q = (ankle, knee, hip)
ACTS_ON_MM = 1.0                                # a moment arm above this, somewhere in the squat, counts as acting

# Sources the squat depends on, as rows of sources/SOURCES.md (matched by a unique substring of the Source column).
SOURCE_ROWS = [
    ("OpenSim Gait2392 model file", "Joint centres, foot, pelvis and torso; the 14 muscles' parameters and paths; the moving knee"),
    ("OpenSim documentation (version 2.4). Gait 2392", "Where the Gait2392 muscle strengths come from"),
    ("de Leva P (1996)", "Segment mass, centre-of-mass and inertia fractions for the female and male bodies"),
    ("Duarte M. *Notes on Scientific Computing", "Machine-readable copy of de Leva's table, the source of every de Leva value"),
    ("De Groote F, Kinney AL", "Muscle force law: force-length and force-velocity curves"),
    ("OpenSim source code, opensim-core", "The curve constants and spline code, ported and checked"),
    ("OpenSim 4.6 (software", "Independent verification oracle for geometry, forces and the moving knee"),
    ("Anatomy, Bony Pelvis and Lower Limb, Hip", "Hip anatomy in the ontology"),
    ("Thigh Muscles. *StatPearls*", "Quadriceps anatomy in the ontology"),
    ("Gastrocnemius Muscle. *StatPearls*", "Calf anatomy in the ontology"),
    ("Leg Anterior Compartment. *StatPearls*", "Tibialis anterior anatomy in the ontology"),
    ("Wu G, et al. (2002)", "Joint coordinate conventions"),
]

# Independent reproduction by the other model, quoted from PROJECT_STATE.md (Validation table and notes).
RECORDS = [
    ("Stage D1", "ChatGPT re-ran the whole stage at 3b86cc4 on its own machine and compared 20,570 values with "
                 "Claude's results: 0 numeric differences.", "PR #27"),
    ("Stage D2", "ChatGPT re-ran the build at b9e96ed: the OpenSim reference (44,034 values) and the run "
                 "(153,757 values) matched the committed files exactly. It also confirmed with OpenSim that the "
                 "knee simplification explained the shortfall.", "PR #36"),
    ("Stage D3", "ChatGPT reproduced the amended moving-knee run at 9805d41. Its reviews raised four findings, "
                 "then one more; all were fixed (D-060 Amendments 2 and 3).", "PR #42"),
]


def r(x, d):
    """Round nested numbers for display."""
    if isinstance(x, float):
        return round(x, d)
    if isinstance(x, list):
        return [r(v, d) for v in x]
    if isinstance(x, dict):
        return {k: r(v, d) for k, v in x.items()}
    return x


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ sources and ontology
def source_rows():
    text = (ROOT / "sources" / "SOURCES.md").read_text(encoding="utf-8")
    rows = [ln for ln in text.splitlines() if ln.startswith("| ") and not ln.startswith("| ID") and "---" not in ln]
    out = []
    for key, use in SOURCE_ROWS:
        hits = [ln for ln in rows if key in ln.strip("|").split("|")[1]]   # the Source column only
        if len(hits) != 1:
            raise SystemExit(f"sources/SOURCES.md: expected one row containing {key!r}, found {len(hits)}")
        cells = [c.strip() for c in hits[0].strip("|").split("|")]
        title = re.sub(r"\*([^*]+)\*", r"\1", cells[1]).replace("`", "")
        if len(title) > 240 and ":" in title[20:]:          # a long descriptive cell: keep its heading only
            title = title[:title.index(":", 20)]
        link = re.search(r"\[([^\]]+)\]\((https?://[^)]+)\)", cells[2])
        out.append({"id": cells[0].strip("`") if cells[0] != "—" else None, "title": title,
                    "url": link.group(2) if link else None, "use": use, "status": cells[4].split(" (")[0]})
    return out


def ontology():
    mods = [yaml.safe_load((ROOT / "ontology" / f).read_text(encoding="utf-8"))
            for f in ("hip.yaml", "lower_limb_sagittal.yaml")]
    ents, srcs = {}, {}
    for m in mods:
        ents.update(m["entities"])
        srcs.update(m.get("sources") or {})
    return mods, ents, srcs


def peak_moment_arms(d3_run):
    """Largest |moment arm| per joint over the D3 motion, Gait2392 body with the moving knee (mm)."""
    from src import muscles_d2 as m2, squat_d3 as d3
    joints = dataclasses.replace(m2.d1_joints(1.0), moving_knee=d3.load_knee(1.0)[0])
    acts, _ = m2.load_actuators(1.0)
    q = d3_run["series"]["q_rad"]
    Q = np.array([q[j] for j in JOINT_ORDER])
    out = {}
    for a in acts:
        pk = np.zeros(3)
        for i in range(Q.shape[1]):
            pk = np.maximum(pk, np.abs(m2.path(a, Q[:, i], joints)[1]))
        out[a.name] = {j: round(float(pk[k]) * 1000, 1) for k, j in enumerate(JOINT_ORDER)}
    return out


def muscles(d3_run, ents, srcs):
    arms = peak_moment_arms(d3_run)
    name = lambda i: ents.get(i, {}).get("name", i)  # noqa: E731
    joint_of = {"LB:JOINT:HIP_R": "hip", "LB:JOINT:KNEE_R": "knee", "LB:JOINT:ANKLE_R": "ankle"}
    out = {}
    for a in d3_run["actuators"]:
        e = ents[a["represents"]]
        rel = e.get("relationships", {})
        crosses = [joint_of.get(j, name(j)) for j in rel.get("CROSSES", [])]
        model = [j for j in JOINT_ORDER if arms[a["name"]][j] > ACTS_ON_MM]
        ev = []
        for s in e.get("evidence", []):
            info = srcs.get(s, {})
            ev.append({"id": s, "title": info.get("title", s), "url": info.get("url")})
        act_id = "LB:ACT:G2392:" + a["name"].upper()
        out[a["name"]] = {
            "entity": a["represents"], "entity_name": e["name"], "actuator": act_id,
            "crosses": crosses, "model_joints": model, "gap": sorted(set(model) - set(crosses)),
            "nerves": [name(n) for n in rel.get("INNERVATED_BY", [])],
            "capabilities": [c.replace("_", " ") for c in e.get("mechanical_capabilities", [])],
            "evidence": ev, "note": e.get("note"), "actuator_evidence": ents[act_id].get("evidence", []),
            "fmax": a["max_isometric_force_N"], "lopt_mm": round(a["optimal_fiber_length_m"] * 1000, 1),
            "lts_mm": round(a["tendon_slack_length_m"] * 1000, 1),
            "penn_deg": round(float(np.degrees(a["pennation_at_optimal_rad"])), 1), "arms_mm": arms[a["name"]],
        }
    return out


# ------------------------------------------------------------------ records in docs/
def process_counts():
    dec = (ROOT / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
    reviews = [p.name for p in (ROOT / "docs" / "reviews").glob("*.md")]
    return {"decisions": len(set(re.findall(r"^### (D-\d{3})", dec, re.M))),
            "owner_answers": len(set(re.findall(r"^\| \*\*(Q\d+)\*\*", dec, re.M))),
            "reviews_chatgpt": sum("_ChatGPT_" in n for n in reviews),
            "reviews_claude": sum("_Claude_" in n for n in reviews)}


# ------------------------------------------------------------------ data
def build_data(d1, d2, d3, paths=(D1, D2, D3)):
    mods, ents, srcs = ontology()
    by = lambda m: {x["body"]: x for x in m["runs"]}  # noqa: E731
    r1, r2 = by(d1), by(d2)
    runs = []
    for x in d3["runs"]:
        b, s = x["body"], x["series"]
        seg = r1[b]["segments_per_leg"]
        runs.append({
            "body": b, "label": LABELS[b], "long": LONG[b], "mass": x["body_mass_kg"], "stature": x["stature_m"],
            "scale": round(x["scale"], 4), "foot": r(x["foot"], 4),
            "seg_mass": {k: round(seg[k]["mass_kg"], 2) for k in ("shank", "thigh", "hat")},
            "q": {j: r(list(np.degrees(s["q_rad"][j])), 2) for j in JOINT_ORDER},
            "tau": r(s["tau_per_leg_N_m"], 2),
            "pts": {k: r(s["d1_points_m"][k], 4) for k in ("knee", "hip", "hat_drawing_top")},
            "act": r(s["activation"], 3), "force": r(s["tendon_force_N"], 1), "paths": r(s["muscle_path_xy_m"], 4),
            "tstar_fixed": r(r2[b]["series"]["t_star_N_m"], 3), "tstar_moving": r(s["t_star_N_m"], 3),
            "cmp": x["comparison_with_fixed_knee"], "status": x["status"], "verification": x["verification"],
            "residuals": x["checks"]["residuals"], "contact": x["contact"],
            "d2_summary": r2[b]["reserve_summary"],
        })
    traced = len({(ds, i["observation_id"]) for m in (d1, d3) for x in m["runs"]
                  for ds, v in x["input_traceability"].items() for i in v["inputs"] if i["passed"]})
    tol = dict(d3["configuration"]["tolerances"])
    params = d1["configuration"]["parameters"]
    classes = {}
    for e in ents.values():
        classes[e.get("class")] = classes.get(e.get("class"), 0) + 1
    return {
        "t": r(d3["runs"][0]["series"]["t_s"], 3), "names": NAMES, "groups": GROUPS,
        "runs": runs, "muscles": muscles(next(x for x in d3["runs"] if x["body"] == "gait2392"), ents, srcs),
        "motion": {"depth_deg": [round(float(np.degrees(v)), 1) for v in params["depth_angles"]["value"]],
                   "depth_why": params["depth_angles"]["rationale"], "period": params["period"]["value"],
                   "samples": params["samples"]["value"], "gravity": params["gravity"]["value"],
                   "friction": params["friction_coefficient"]["value"]},
        "pipeline": {"entities": len(ents), "muscle_entities": classes.get("SkeletalMuscle", 0),
                     "actuators": classes.get("ModelActuator", 0), "modules": len(mods),
                     "traced": traced, "input_files": len(d3["verified_input_files"]),
                     "provenance": d3["commit_provenance_status"]},
        "tolerances": tol, "epsilon": d3["runs"][0]["reserve_summary"]["epsilon_reserve_N_m"],
        "assumptions": [{"label": f"{a['source']}-{a['number']}", "text": a["text"]} for a in d3["declared_assumptions"]],
        "omitted": {**d1["configuration"]["omitted_physics"], **{"knee": d3["configuration"]["omitted_physics"]["knee"]}},
        "validity": d3["validity"], "source_validation": d3["source_validation"],
        "what_checks_show": d3["what_the_checks_show"],
        "ankle_foot": d3["ankle_foot_simplification_size_gait2392"]["largest_by_coordinate"],
        "sources": source_rows(), "records": [{"stage": a, "text": b, "ref": c} for a, b, c in RECORDS],
        "process": process_counts(),
        "manifests": {k: [str(p), m["commit_sha"], m["decision"]] for k, p, m in zip(("d1", "d2", "d3"), paths, (d1, d2, d3))},
        "full_viewer": FULL_VIEWER,
    }


TEMPLATE = (Path(__file__).with_name("squat_demo_template.html")).read_text(encoding="utf-8")


def render(d1, d2, d3, paths=(D1, D2, D3)):
    data = json.dumps(build_data(d1, d2, d3, paths), separators=(",", ":"), allow_nan=False)
    return TEMPLATE.replace("__DATA__", data.replace("</", "<\\/"))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--d1", default=D1)
    p.add_argument("--d2", default=D2)
    p.add_argument("--d3", default=D3)
    p.add_argument("--output", type=Path, default=ROOT / "SQUAT_DEMO.html")
    a = p.parse_args()
    html = render(load(a.d1), load(a.d2), load(a.d3), (a.d1, a.d2, a.d3))
    a.output.write_text(html, encoding="utf-8", newline="\n")
    print(f"Demo written to {a.output} ({len(html.encode()) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
