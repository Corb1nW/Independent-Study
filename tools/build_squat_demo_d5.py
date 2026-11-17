"""Build the Stage D5 squat demonstration page: SQUAT_DEMO_D5.html, one self-contained file at the repository root.

    python -m tools.build_squat_demo_d5
    python -m tools.build_squat_demo_d5 --output SQUAT_DEMO_D5.html

A presentation of Stage D5 (D-063 with Amendment 1) for technical reviewers: the squat with all 43 of Gait2392's leg
muscles against D4's 16; the lower-limb anatomy inventory (every muscle, actuated or not); the bounded direction check
and its declared deviations; the hypotheses H2-H4 and each actuator's share of each joint's torque; the verification;
the acceptance criteria; the limits; and how the stage serves the proof-of-concept plan (D-061).

Presentation only. It changes no model, data or result, and it reads only archived official files, so it rebuilds byte
for byte on any later commit:
- the Stage D5 run manifest and the D5 report, the official D4 growth manifest (16 actuators) and the official D3
  manifest: each read exactly as archived, identified by path, archive commit and SHA-256 in OFFICIAL. A working copy
  that differs is ignored in favour of the archived Git blob, and the build stops if that is unavailable. The builder
  takes no other manifests, so no page can show other files under the official label (the D4 page's lesson,
  ChatGPT D4-DEMO-02);
- simulation series, statuses, checks, consistency results, oracle comparisons and actuator parameters: copied from
  the manifests (rounded for display); hypotheses and torque shares: from the report, which records the SHA-256 of
  both manifests it read (checked here);
- ontology content (names, relationships, capabilities, evidence, sources): from the exact module files the D5 run
  read, by the Git blob IDs its manifest records; "new in D5" compares them with the files the D4 growth run read;
- joint positions for the stick figure: the official D3 manifest's body points, as on the D4 page. The build checks
  that D3's 14 muscle drawings are reproduced exactly by both the D4 and the D5 runs, so the figure and the muscles
  come from the same model;
- review record, acceptance-criteria evidence, findings and roadmap: the RECORDS below, each citing its record in
  docs/, a commit or a pull request.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from tools.build_squat_demo_d4 import (OFFICIAL as OFFICIAL_D4, _git_bytes, check_same_drawing, pinned_text, r,
                                       short)

ROOT = Path(__file__).resolve().parents[1]
D5_ARCHIVE = "a86fbdf93088beae630286e91a58edaf483e4195"
OFFICIAL = {
    "d5": ("results/phase_d/2026-11-17_d5_runs_4c0e320.json", D5_ARCHIVE,
           "1c887873e2ce34027354d64498d9c7b0f50564ede7fb4207a8d7ebf1b52c8663"),
    "report": ("results/phase_d/2026-11-17_d5_report_4c0e320.json", D5_ARCHIVE,
               "a1850df4b31e2ece46a59dab71917d0193e73942112d4d99dbec459b28fca9dc"),
    "growth": OFFICIAL_D4["growth"],
    "d3": OFFICIAL_D4["d3"],
}
LABELS = {"female": "Female", "male": "Male", "gait2392": "Gait2392"}
LONG = {"female": "de Leva (1996) female reference body", "male": "de Leva (1996) male reference body",
        "gait2392": "OpenSim Gait2392 generic model"}
JOINT_LABEL = {"ankle": "LB:DOF:ANKLE_DORSI_PLANTAR_R", "knee": "LB:DOF:KNEE_FLEX_EXT_R", "hip": "LB:DOF:HIP_FLEX_EXT_R"}
MODULES = ("ontology_hip", "ontology_lower_limb_sagittal", "ontology_foot")

# Display names and groups for the 43 actuators (presentation only; IDs and parameters come from the manifests).
NAMES = {
    "glut_max1_r": "Gluteus max. (upper)", "glut_max2_r": "Gluteus max. (middle)", "glut_max3_r": "Gluteus max. (lower)",
    "add_long_r": "Adductor longus", "add_brev_r": "Adductor brevis", "add_mag1_r": "Adductor magnus 1",
    "add_mag2_r": "Adductor magnus 2", "add_mag3_r": "Adductor magnus 3", "pect_r": "Pectineus", "grac_r": "Gracilis",
    "glut_med1_r": "Gluteus med. (ant.)", "glut_med2_r": "Gluteus med. (mid.)", "glut_med3_r": "Gluteus med. (post.)",
    "glut_min1_r": "Gluteus min. (ant.)", "glut_min2_r": "Gluteus min. (mid.)", "glut_min3_r": "Gluteus min. (post.)",
    "tfl_r": "Tensor fasciae latae", "peri_r": "Piriformis", "gem_r": "Gemelli (lumped)",
    "quad_fem_r": "Quadratus femoris", "iliacus_r": "Iliacus", "psoas_r": "Psoas", "sar_r": "Sartorius",
    "bifemlh_r": "Biceps femoris (long)", "bifemsh_r": "Biceps femoris (short)", "semimem_r": "Semimembranosus",
    "semiten_r": "Semitendinosus", "vas_med_r": "Vastus medialis", "vas_int_r": "Vastus intermedius",
    "vas_lat_r": "Vastus lateralis", "rect_fem_r": "Rectus femoris", "med_gas_r": "Gastrocnemius (medial)",
    "lat_gas_r": "Gastrocnemius (lateral)", "soleus_r": "Soleus", "tib_post_r": "Tibialis posterior",
    "flex_dig_r": "Flexor digitorum longus", "flex_hal_r": "Flexor hallucis longus", "per_long_r": "Fibularis longus",
    "per_brev_r": "Fibularis brevis", "tib_ant_r": "Tibialis anterior", "ext_dig_r": "Extensor digitorum longus",
    "ext_hal_r": "Extensor hallucis longus", "per_tert_r": "Fibularis tertius",
}
GROUPS = [
    ("Hip extensors", ["glut_max1_r", "glut_max2_r", "glut_max3_r"]),
    ("Adductors", ["add_long_r", "add_brev_r", "add_mag1_r", "add_mag2_r", "add_mag3_r", "pect_r", "grac_r"]),
    ("Abductors and rotators (out of plane)", ["glut_med1_r", "glut_med2_r", "glut_med3_r", "glut_min1_r",
                                               "glut_min2_r", "glut_min3_r", "tfl_r", "peri_r", "gem_r",
                                               "quad_fem_r"]),
    ("Hip flexors", ["iliacus_r", "psoas_r", "sar_r"]),
    ("Hamstrings", ["bifemlh_r", "bifemsh_r", "semimem_r", "semiten_r"]),
    ("Quadriceps", ["vas_med_r", "vas_int_r", "vas_lat_r", "rect_fem_r"]),
    ("Calf and deep posterior", ["med_gas_r", "lat_gas_r", "soleus_r", "tib_post_r", "flex_dig_r", "flex_hal_r"]),
    ("Lateral leg", ["per_long_r", "per_brev_r"]),
    ("Shin", ["tib_ant_r", "ext_dig_r", "ext_hal_r", "per_tert_r"]),
]

# The D5 build, step by step (D-063 item 8): (step, commit, what, data only?).
STEPS = [
    ("1", "28a4b37", "Generic preparation: lumped actuators, the bounded direction check, recursive oracle resolution, "
     "module list from the schema, the full C5 inventory, torque shares (all of the stage's planned code)", False),
    ("1+", "ce57740", "A declared deviation is keyed by the motion it drives (some paths disagree in both directions)",
     False),
    ("2", "3728cc0", "Leg muscle anatomy, nerves and the toe interphalangeal joint, both sides, with sources", True),
    ("3-4", "1510872", "Gait2392's 27 remaining leg actuators as data; the squat_d5 specification and its declared "
     "deviations", True),
    ("5", "aaf1cf7", "The foot module: intrinsic foot muscles and the plantar nerves, both sides", True),
    ("6a", "8e572ec", "Muscle dataset label 0.4.0 (deferred from steps 3-4 to keep them data only)", False),
    ("6b", "8deaae0", "The second stage-2 solver solves a row-scaled copy of the same problem (finding F1)", False),
    ("6c", "4c0e320", "Three older tests follow the module list and D5's added edges; official runs at this commit",
     False),
    ("6d", "a86fbdf", "The official run manifest and the H2-H4 report", False),
]
A2_COMMITS = ("1510872", "aaf1cf7")           # steps 3-5 (A2: no file in src/ or tools/)

# Acceptance criteria fixed in D-063 (with Amendment 1) before the build, and where the evidence is.
ACCEPTANCE = [
    ("A1", "Geometry", "Every added actuator matches OpenSim 4.6 within D2's tolerances, with coverage OK, on both knee "
     "variants.", "oracle", "manifest field oracle_references (43 actuators each); section 6"),
    ("A2", "Data, not code", "The commits of steps 3 to 5 change no file in src/ or tools/.", "a2",
     "git diff --name-only of 1510872 and aaf1cf7 (none in src/ or tools/); section 2"),
    ("A3", "Consistency", "C1-C5, the required-edge and mirror checks pass; every direction disagreement is a declared, "
     "reference-confirmed deviation listed in C5 with its basis.", "consistency", "manifest field consistency; "
     "section 4"),
    ("A4", "Evidence", "Every new entity and edge cites a source registered as Read; every lower-limb muscle without an "
     "actuator appears in C5.", "inventory", "C5 inventory (section 3); tests/test_phase_d5.py, tests/test_sources.py"),
    ("A5", "Nothing else moves", "The D4 runs, regenerated at the build commit, match their af21e78 manifests in every "
     "series, status, regression, oracle comparison and H1 value; hip.yaml loads on its own.", None,
     "compare_manifest.py at 4c0e320 against both af21e78 manifests; build record (D-063 Amendment 2); section 6"),
    ("A6", "Deliberate errors", "ChatGPT's probe, undeclared, unconfirmed and stale declarations, the lumped-actuator "
     "errors and the nested-extends oracle case all fail as required.", None, "tests/test_phase_d5.py (step 1 tests)"),
    ("A7", "Standard checks", "Full test suite, integrity, probes, dataset check, provenance-verified manifests.",
     "provenance", "manifest field commit_provenance_status; build record"),
    ("A8", "Results reported", "43 against 16 actuators per body; each actuator's share of each joint's torque; H2-H4.",
     "report", "the D5 report (section 5)"),
]

# What the build found that the reviewers should look at (each one is in the build record, D-063 Amendment 2).
FINDINGS = [
    ("F1", "Cross-check solver accuracy",
     "The first official run failed optimizer verification: on four fixed-knee samples (male, Gait2392) the second "
     "stage-2 solver, Clarabel, stopped at reduced accuracy and differed from the certified active-set answer by up to "
     "1.3e-3 (tolerance 1e-5). Pectineus's 0.03 N·m column beside 45 N·m ones made the problem badly scaled. Clarabel "
     "now solves a row-scaled copy of the same problem; every D4 and D5 run agrees to at most 1.7e-6. The recruited "
     "activations come from the other solver and did not change.", "8deaae0"),
    ("F2", "Tensor fasciae latae extends the knee in Gait2392",
     "StatPearls says TFL flexes the knee; Gait2392's path gives it a knee-extension moment arm at every pose of the "
     "squat, on both knees. Declared as a model-source disagreement, not as a capability.", "1510872"),
    ("F3", "Adductors give hip extension in part of the squat",
     "Adductor longus and brevis have sourced hip flexion; their Gait2392 paths give hip extension in part of the "
     "motion. Declared, reference-confirmed, and reported.", "1510872"),
    ("F4", "The vasti still saturate",
     "All three vasti reach full activation near the bottom with 43 actuators, as with 16: Gait2392 adds no knee "
     "extensor, so D5 cannot relieve them. The hip extensors are relieved (H3).", "a86fbdf"),
    ("F5", "Foot chapter count",
     "The foot chapter says 19 muscles lie within the foot but describes 12 entries, treating the lumbricals and "
     "interossei as groups (20 if counted one by one). Recorded as found; one entity per named group.", "aaf1cf7"),
]
REVIEWS = {"scope": "docs/reviews/2026-11-17_ChatGPT_D063_Scope_Review_c3adca0.md",
           "rereview": "docs/reviews/2026-11-17_ChatGPT_D063_Amendment1_ReReview_9a8fc44.md"}
TIMELINE = [
    ("2026-11-17", "Corbin", "Asks for the next-step proposal after the D4 page was accepted (Q79).", "direction",
     "DECISIONS.md Q79"),
    ("2026-11-17", "Claude", "Proposes Stage D5 (D-063): Gait2392's remaining leg muscles as data.", "proposal",
     "PR #53"),
    ("2026-11-17", "Corbin", "Widens the anatomy to every lower-limb muscle, \"even if they don't offer much "
     "contribution to our simulated movement currently\", and asks for a scope review first (Q80).", "direction",
     "DECISIONS.md Q80"),
    ("2026-11-17", "ChatGPT", "Scope review: a reference exception keyed to ontology capabilities would let a wrong "
     "capability through (D5-R01); the data-only steps need more generic preparation (D5-R02).", "AMEND",
     REVIEWS["scope"]),
    ("2026-11-17", "Claude", "D-063 Amendment 1: bounded, declared and reference-confirmed direction deviations; all "
     "code changes first.", "amendment", "D-063 Amendment 1 (Q81)"),
    ("2026-11-17", "ChatGPT", "Re-reviews D-063 Amendment 1.", "AGREE", REVIEWS["rereview"]),
    ("2026-11-17", "Corbin", "\"Chat agred and I merged, start building\" (Q82): PRs #53 and #54 merged.", "accepted",
     "DECISIONS.md Q82, A-23"),
    ("2026-11-17", "Claude", "Builds D5 in the planned steps; official run at 4c0e320; this page.", "build",
     "D-063 Amendment 2; PR #55"),
    ("pending", "ChatGPT", "Build review of PR #55.", "pending", "PR #55"),
]
CLAIM_B = [
    ("done", "The squat model is assembled from the ontology by generic code that names no anatomy",
     "D4; unchanged in D5"),
    ("done", "Anatomy added to the ontology enters the simulation as data, with no code change",
     "D5 at scale: 27 actuators in data-only commits (A2), after D4's 2"),
    ("done", "The ontology and the model check each other",
     "C1-C5 on 43 actuators; every direction disagreement declared, with its basis, and confirmed by OpenSim"),
    ("next", "The assembled model performs the squat (muscle-driven forward simulation)", "Stage D7"),
]
CLAIM_A = [
    ("done", "Every number is sourced, derived or labelled as an assumption", "datasets, sources and C4 traceability"),
    ("done", "Acceptance criteria written before results", "A1-A8 and H2-H4 fixed in D-063 before the build"),
    ("done", "Computation verified by independent methods", "two dynamics formulations, OpenSim oracle, second solver "
     "(whose own accuracy problem the build found and fixed, F1)"),
    ("next", "Evaluated against measured human data under preregistered criteria", "Stage D6"),
    ("next", "The other AI model reproduces the results", "ChatGPT's build review of PR #55 (pending)"),
    ("done", "Errors and corrections are on the record", "D5-R01 and D5-R02 in the scope review; F1-F5 in the build"),
    ("next", "A human expert reads the result", "Stage D9"),
]
ROADMAP = [
    ("done", "D1-D3", "Mechanics, muscles, moving knee"),
    ("done", "D4", "Model assembled from the ontology"),
    ("now", "D5", "Every lower-limb muscle in the ontology; all 43 Gait2392 leg muscles in the squat (this page)"),
    ("", "D6", "Measured squat; preregistered evaluation"),
    ("", "D7", "Muscle-driven forward simulation with a tracking controller"),
    ("", "D8", "Passive force, tendon compliance, robustness and uncertainty"),
    ("", "D9", "Technical report, process audit, expert reader"),
    ("later", "E, F", "Clinical conditions and personalization"),
]


# ------------------------------------------------------------------ official inputs
def official_text(key, root=ROOT):
    """An official file exactly as archived: the working file if its SHA-256 is the recorded one, otherwise the file
    at its archive commit, checked against the same SHA-256. Never an edited working copy."""
    path, commit, digest = OFFICIAL[key]
    working = Path(root) / path
    if working.exists():
        data = working.read_bytes()
        if hashlib.sha256(data).hexdigest() == digest:
            return data.decode("utf-8")
    data = _git_bytes("show", f"{commit}:{path}")
    if hashlib.sha256(data).hexdigest() != digest:
        raise SystemExit(f"{path} at {commit} does not match its recorded SHA-256")
    return data.decode("utf-8")


def load_official():
    """(d5, report, growth, d3), the archived official files."""
    return tuple(json.loads(official_text(k)) for k in ("d5", "report", "growth", "d3"))


def ontology(manifest, keys=MODULES):
    ents, srcs, models, additions = {}, {}, {}, []
    for k in keys:
        if k not in manifest["inputs"]:
            continue
        m = yaml.safe_load(pinned_text(manifest["inputs"][k]))
        ents.update(m["entities"])
        srcs.update(m.get("sources") or {})
        models.update(m.get("models") or {})
        additions += m.get("relationship_additions") or []
    return ents, srcs, models, additions


def _name(ents, i):
    return ents.get(i, {}).get("name", i)


# ------------------------------------------------------------------ runs
def runs_of(manifest, d3, order3):
    order = [short(a) for a in manifest["specification"]["actuators"]]
    by3 = {x["body"]: x for x in d3["runs"]}
    out = {}
    for x in manifest["runs"]:
        if x["variant"] != "moving_knee":
            continue
        s, b = x["series"], x["body"]
        check_same_drawing(s["muscle_path_xy_m"], by3[b]["series"]["muscle_path_xy_m"], order, order3)
        p3 = by3[b]["series"]["d1_points_m"]
        out[b] = {
            "body": b, "label": LABELS[b], "long": LONG[b], "mass": x["body_mass_kg"], "stature": x["stature_m"],
            "foot": r(by3[b]["foot"], 4),
            "q": {j: r(list(np.degrees(s["q_rad"][c])), 2) for j, c in JOINT_LABEL.items()},
            "tau": {j: r(s["tau_per_side_N_m"][c], 2) for j, c in JOINT_LABEL.items()},
            "pts": {k: r(p3[k], 4) for k in ("knee", "hip", "hat_drawing_top")},
            "act": r(s["activation"], 3), "force": r(s["tendon_force_N"], 1),
            "paths": [[r(f[order.index(n)], 3) for n in order] for f in s["muscle_path_xy_m"]], "order": order,
            "tstar": r(s["t_star_N_m"], 4),
            "params": {a["name"]: {"fmax": a["max_isometric_force_N"],
                                   "lopt_mm": round(a["optimal_fiber_length_m"] * 1000, 1),
                                   "lts_mm": round(a["tendon_slack_length_m"] * 1000, 1),
                                   "penn_deg": round(float(np.degrees(a["pennation_at_optimal_rad"])), 1)}
                       for a in x["actuators"]},
        }
    return out


def share_paths(sets, growth, d5):
    """The D4 run's 16 muscle drawings equal D5's for the same actuators at every sample, as stored in the two
    manifests (same data, same generic path code). Checked here; then the D4 set reads D5's drawings, so the page
    stores them once. Drawings are rounded to 1 mm for display (0.2 px at the figure's scale)."""
    raw = {m["specification"]["name"]: {x["body"]: x for x in m["runs"] if x["variant"] == "moving_knee"}
           for m in (growth, d5)}
    for b, run4 in sets["d4"].items():
        p4, p5 = raw["squat_d4_iliopsoas"][b]["series"]["muscle_path_xy_m"], raw["squat_d5"][b]["series"]["muscle_path_xy_m"]
        o5 = sets["d5"][b]["order"]
        for k, frame in enumerate(p4):
            for j, name in enumerate(run4["order"]):
                if frame[j] != p5[k][o5.index(name)]:
                    raise SystemExit(f"D4 drawing of {name} ({b}, sample {k}) differs from D5's")
        del run4["paths"]


# ------------------------------------------------------------------ consistency and anatomy
def consistency_view(d5, ents):
    c = d5["consistency"]
    reg = c["C5_deviation_register"]
    declared = c["C3_actions"]["declared_deviations"]
    confirmed = {}
    for case, v in c["C3_actions"]["direction"].items():
        for d in v.get("declared_and_confirmed", []):
            k = (d["actuator"], d["coordinate"], d["drives"])
            row = confirmed.setdefault(k, {"cases": [], "extreme_mm": 0.0, "samples": 0})
            row["cases"].append(case)
            if abs(d["extreme_moment_arm_m"]) * 1000 > abs(row["extreme_mm"]):
                row["extreme_mm"] = round(d["extreme_moment_arm_m"] * 1000, 2)
            row["samples"] = max(row["samples"], d["samples"])
    dev = []
    for d in declared:
        k = (d["actuator"], d["coordinate"], d["drives"])
        conf = confirmed.get(k, {"cases": [], "extreme_mm": None, "samples": 0})
        dev.append({"actuator": short(d["actuator"]), "coordinate": _name(ents, d["coordinate"]),
                    "drives": d["drives"].replace("_", " "), "variants": d["variants"], "basis": d["basis"],
                    "kind": "model and source disagree" if d["basis"].startswith("Model and source disagree")
                    else "planar-model artifact" if d["basis"].startswith("Model basis") else "other",
                    "confirmed_in": sorted(conf["cases"]), "extreme_mm": conf["extreme_mm"],
                    "largest_samples": conf["samples"]})
    inv = reg["omitted"]["muscles_without_an_actuator"]
    represented = reg["represented"]["actuators"]
    return {
        "summary": [
            ("C1", "Crossings by topology", c["C1_crossings"]["passed"], len(c["C1_crossings"]["failures"])),
            ("C2", "Leverage by geometry", c["C2_leverage"]["passed"], len(c["C2_leverage"]["failures"])),
            ("C3", "Actions and bounded direction", c["C3_actions"]["passed"],
             len(c["C3_actions"]["structural_failures"]) + len(c["C3_actions"]["direction_failures"])),
            ("C4", "Evidence and traceability", c["C4_evidence"]["passed"], len(c["C4_evidence"]["failures"])),
            ("RE", "Required edges", c["required_edges"]["passed"], len(c["required_edges"]["missing"])),
            ("MI", "Left-right mirror", c["mirror"]["passed"], len(c["mirror"]["differences"])),
        ],
        "passed": c["passed"], "deviations": dev,
        "cases": sorted(c["C3_actions"]["direction"]),
        "inventory": {k: sorted(_name(ents, x) for x in v) for k, v in inv.items()},
        "actuated_muscles": sorted({_name(ents, m) for v in represented.values()
                                    for m in (v if isinstance(v, list) else [v])}),
        "crossed_not_modelled": {short(a): [_name(ents, x) for x in v]
                                 for a, v in reg["simplified"]["crossed_not_modelled"].items()},
        "negligible": c["C2_leverage"]["crosses_negligible_leverage"],
    }


def muscle_cards(d5, ents, srcs, cons):
    c = d5["consistency"]
    arms = {}
    for key, v in c["C2_leverage"]["largest_abs_moment_arm_m"].items():
        a, q = key.split(" | ")
        arms.setdefault(short(a), {})[[j for j, cc in JOINT_LABEL.items() if cc == q][0]] = v
    added = {}
    for a in (yaml.safe_load(pinned_text(d5["inputs"][k])).get("relationship_additions") or [] for k in MODULES):
        for x in a:
            added.setdefault(x["entity"], []).append(x)
    out = {}
    for a in d5["runs"][0]["actuators"]:
        reps = a["represents"] if isinstance(a["represents"], list) else [a["represents"]]
        muscles = []
        for m in reps:
            e = ents[m]
            rel = {k: list(v) for k, v in e.get("relationships", {}).items()}
            for x in added.get(m, []):
                for k, v in x["add"].items():
                    rel[k] = rel.get(k, []) + v
            muscles.append({
                "entity": m, "name": e["name"],
                "crosses": [_name(ents, j) for j in rel.get("CROSSES", [])],
                "acts_on": [_name(ents, j) for j in rel.get("ACTS_ON", [])],
                "nerves": [_name(ents, n) for n in rel.get("INNERVATED_BY", [])],
                "capabilities": [x.replace("_", " ") for x in e.get("mechanical_capabilities", [])],
                "evidence": [{"id": s, "title": srcs.get(s, {}).get("title", s), "url": srcs.get(s, {}).get("url")}
                             for s in e.get("evidence", [])]})
        c1 = c["C1_crossings"]["per_actuator"][a["id"]]
        out[a["name"]] = {"actuator": a["id"], "lumped": len(reps) > 1, "muscles": muscles,
                          "derived": [_name(ents, j) for j in c1["derived"]],
                          "crossed_not_modelled": [_name(ents, j) for j in c1["crossed_not_modelled"]],
                          "agrees": c1["agrees"], "c2": arms[a["name"]],
                          "deviations": [d for d in cons["deviations"] if d["actuator"] == a["name"]]}
    return out


def anatomy_view(d5, growth, ents):
    before, _, _, _ = ontology(growth, ("ontology_hip", "ontology_lower_limb_sagittal"))
    per_module = {}
    for k in MODULES:
        m = yaml.safe_load(pinned_text(d5["inputs"][k]))
        mus = [i for i, e in m["entities"].items() if e.get("class") == "SkeletalMuscle"]
        per_module[d5["inputs"][k]["path"].split("/")[-1]] = {
            "muscles": len(mus), "new_muscles": sum(i not in before for i in mus),
            "entities": len(m["entities"]), "new_entities": sum(i not in before for i in m["entities"])}
    new_right = sorted(_name(ents, i) for i, e in ents.items()
                       if e.get("class") == "SkeletalMuscle" and i not in before and e.get("side") == "right")
    total = sum(1 for e in ents.values() if e.get("class") == "SkeletalMuscle")
    return {"modules": per_module, "new_right": new_right, "total_muscles": total,
            "before_muscles": sum(1 for e in before.values() if e.get("class") == "SkeletalMuscle")}


# ------------------------------------------------------------------ results and checks
def checks_of(d5, tol, d2p):
    rows = {}
    for x in d5["runs"]:
        for k, v in x["checks"]["residuals"].items():
            row = rows.setdefault(k, {"worst": 0.0, "passed": True, "runs": 0})
            row["worst"] = max(row["worst"], abs(v))
            row["passed"] = row["passed"] and x["checks"]["passed"][k]
            row["runs"] += 1
    tkey = {"newton_identity_per_side_N": "newton_identity_N", "mass_bookkeeping_relative": "mass_fraction_sum"}
    for k, row in rows.items():
        row["tolerance"] = tol[tkey.get(k, k)]
    opt = {k: max(abs(x["verification"][k]) for x in d5["runs"]) for k in d5["runs"][0]["verification"]}
    solver = {k: {"value": d2p[k]["value"], "unit": d2p[k]["unit"]}
              for k in ("kkt_tolerance", "second_solver_t_star_tolerance", "second_solver_activation_tolerance")}
    return {"mechanics": rows, "optimizer": opt, "solver_tolerances": solver,
            "optimizer_passed": all(x["status"]["optimizer_verification"] == "passed" for x in d5["runs"]),
            "runs": len(d5["runs"])}


def results_view(report, groups):
    """Hypotheses, feasibility per case and torque shares by group, from the report."""
    group_of = {m: g for g, ms in groups for m in ms}
    cases = {}
    for case, c in report["cases"].items():
        shares = {}
        for coord, s in c["torque_shares_d5"].items():
            j = [k for k, v in JOINT_LABEL.items() if v == coord][0]
            shares[j] = {"top": [{**t, "peak_N_m": round(t["peak_N_m"], 2), "share": round(t["share"], 4)}
                                 for t in s["top"]],
                         "out_of_plane": round(s["out_of_plane_share"], 4)}
        cases[case] = {"feasibility": c["feasibility"], "shares": shares}
    return {"hypotheses": report["hypotheses"], "cases": cases, "out_of_plane": report["out_of_plane_actuators"],
            "group_of": group_of}


def group_shares(d5):
    """Each muscle group's share of each joint's muscle moment, per moving-knee body (from the manifest's shares)."""
    group_of = {m: g for g, ms in GROUPS for m in ms}
    out = {}
    for x in d5["runs"]:
        if x["variant"] != "moving_knee":
            continue
        out[x["body"]] = {}
        for coord, acts in x["torque_shares"].items():
            j = [k for k, v in JOINT_LABEL.items() if v == coord][0]
            g = {}
            for a, v in acts.items():
                g[group_of[a]] = g.get(group_of[a], 0.0) + v["share"]
            out[x["body"]][j] = {k: round(v, 4) for k, v in g.items() if v > 0}
    return out


def acceptance_view(d5, report, cons, a2):
    s = d5["status"]
    state = {
        "a2": all(not v["code"] for v in a2.values()),
        "oracle": s["oracle_verification"] == "passed" and all(
            len(v["actuators_compared"]) == 43 and not v["coverage_problems"] for v in d5["oracle_references"].values()),
        "consistency": s["consistency_checks"] == "passed" and d5["consistency"]["passed"]
        and all(d["confirmed_in"] for d in cons["deviations"]),
        "inventory": d5["consistency"]["C4_evidence"]["passed"],
        "provenance": d5["commit_provenance_status"] == "verified_git_head_and_inputs"
        and all(s[k] == "passed" for k in ("mechanics_verification", "optimizer_verification")),
        "report": len(report["hypotheses"]) == 3 and len(report["cases"]) == 6,
    }
    return [{"id": a, "name": n, "text": t, "from_manifest": k is not None,
             "passed": state[k] if k else None, "evidence": ev} for a, n, t, k, ev in ACCEPTANCE]


def a2_evidence():
    """For each data-only commit, the files it changed in src/ or tools/ (A2 requires none)."""
    out = {}
    for c in A2_COMMITS:
        names = _git_bytes("diff", "--name-only", f"{c}~1", c).decode("utf-8").split()
        out[c] = {"files": len(names), "code": [n for n in names if n.startswith(("src/", "tools/"))]}
    return out


# ------------------------------------------------------------------ data
def build_data(d5, report, growth, d3):
    for p in REVIEWS.values():
        if not (ROOT / p).exists():
            raise SystemExit(f"cited review record missing: {p}")
    for key, role in (("d5", "d5_manifest"), ("growth", "d4_manifest")):
        if report["inputs"][role]["sha256"] != OFFICIAL[key][2]:
            raise SystemExit(f"the report was not computed from the official {key} manifest")
    grouped = [n for _, ms in GROUPS for n in ms]
    if sorted(grouped) != sorted(short(a) for a in d5["specification"]["actuators"]):
        raise SystemExit("the display groups do not cover the 43 actuators exactly")
    ents, srcs, models, _ = ontology(d5)
    tol = yaml.safe_load(pinned_text(d5["inputs"]["d3_config"]))["tolerances"]
    d2p = yaml.safe_load(pinned_text(d5["inputs"]["d2_config"]))["parameters"]
    order3 = [a["name"] for a in d3["runs"][0]["actuators"]]
    t = d5["runs"][0]["series"]["t_s"]
    if growth["runs"][0]["series"]["t_s"] != t:
        raise SystemExit("the D4 and D5 runs have different time series")
    cons = consistency_view(d5, ents)
    a2 = a2_evidence()
    spec = models["squat_d5"]
    sets = {"d4": runs_of(growth, d3, order3), "d5": runs_of(d5, d3, order3)}
    share_paths(sets, growth, d5)
    return {
        "t": r(t, 3), "names": NAMES, "groups": GROUPS, "bodies": list(LABELS), "sets": sets,
        "muscles": muscle_cards(d5, ents, srcs, cons), "consistency": cons,
        "anatomy": anatomy_view(d5, growth, ents),
        "results": results_view(report, GROUPS), "group_shares": group_shares(d5),
        "checks": checks_of(d5, tol, d2p), "oracle": d5["oracle_references"], "status": d5["status"],
        "acceptance": acceptance_view(d5, report, cons, a2), "a2": a2,
        "steps": [{"step": s, "commit": c, "text": t_, "data_only": d} for s, c, t_, d in STEPS],
        "findings": [{"id": i, "title": ti, "text": tx, "commit": c} for i, ti, tx, c in FINDINGS],
        "timeline": [{"date": d, "who": w, "text": t_, "verdict": v, "ref": ref} for d, w, t_, v, ref in TIMELINE],
        "claim_a": CLAIM_A, "claim_b": CLAIM_B, "roadmap": ROADMAP,
        "spec": {"name": d5["specification"]["name"], "extends": spec.get("extends"),
                 "description": spec.get("description"), "actuators": len(d5["specification"]["actuators"])},
        "validity": d5["validity"], "source_validation": d5["source_validation"],
        "assumptions": d5["configuration"]["assumptions"],
        "inputs": {"files": len(d5["verified_input_files"]), "provenance": d5["commit_provenance_status"],
                   "code_modules": sum(k.startswith("code_") for k in d5["inputs"])},
        "manifests": {k: {"path": OFFICIAL[k][0], "archived_at": OFFICIAL[k][1], "sha256": OFFICIAL[k][2]}
                      for k in OFFICIAL},
        "run_commits": {"d5": d5["commit_sha"], "d4": growth["commit_sha"], "d3": d3["commit_sha"]},
    }


TEMPLATE = (Path(__file__).with_name("squat_demo_d5_template.html")).read_text(encoding="utf-8")


def render(d5, report, growth, d3):
    data = json.dumps(build_data(d5, report, growth, d3), separators=(",", ":"), allow_nan=False)
    return TEMPLATE.replace("__DATA__", data.replace("</", "<\\/"))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--output", type=Path, default=ROOT / "SQUAT_DEMO_D5.html")
    a = p.parse_args()
    html = render(*load_official())
    a.output.write_text(html, encoding="utf-8", newline="\n")
    print(f"Demo written to {a.output} ({len(html.encode()) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
