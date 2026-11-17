"""Build the Stage D4 squat demonstration page: SQUAT_DEMO_D4.html, one self-contained file at the repository root.

    python -m tools.build_squat_demo_d4
    python -m tools.build_squat_demo_d4 --output SQUAT_DEMO_D4.html

A presentation of Stage D4 (D-062) for technical reviewers: the squat model assembled from the ontology, played back
with 14 and 16 muscles; how the ontology states the model; the anatomy-model consistency checks C1-C5; the regression
to the official D1-D3 runs; the verification; the iliopsoas growth test and hypothesis H1; the review record; the
limits; and how the stage serves the proof-of-concept plan (D-061).

Presentation only. It changes no model, data or result, and it reads only pinned inputs, so it rebuilds byte for byte
on any later commit:
- the three run manifests: read only as the archived official files, identified by SHA-256 and archive commit in
  OFFICIAL below. A working copy that differs is ignored in favour of the archived Git blob (and the build stops if
  that is unavailable), so an edited file at a default path cannot reach the page under the official label
  (ChatGPT D4-DEMO-02). Manifests passed with --assembled, --growth or --d3 that are not the official files build a
  page marked "custom inputs" throughout, with no provenance claim;
- simulation series, statuses, checks, consistency results, regression, oracle comparisons, H1 and each body's
  actuator parameters: copied from the two official Stage D4 manifests at af21e78 (rounded for display);
- ontology content (entity names, relationships, the relationship additions, coordinate conventions, the model
  specification): read from the exact ontology files those runs used, by the Git blob IDs the manifests record;
- check tolerances: from the D3 and D2 configuration files, by the blob IDs the manifests record;
- joint positions for the stick figure: the official Stage D3 manifest's body points. D4's regression (criterion A2)
  showed they equal the assembled model's at the stored precision; the build checks that the D4 muscle drawings
  equal D3's as well, so the figure and the muscles come from the same model;
- review record, acceptance-criteria evidence and roadmap: the RECORDS below, each citing its record in docs/ or a
  pull request; the build fails if a cited review file is missing.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import yaml

from tools.build_d2_page import GROUPS as GROUPS_14, NAMES as NAMES_14

ROOT = Path(__file__).resolve().parents[1]
ASSEMBLED = "results/phase_d/2026-11-16_d4_assembled_runs_af21e78.json"
GROWTH = "results/phase_d/2026-11-16_d4_iliopsoas_runs_af21e78.json"
D3 = "results/phase_d/2026-11-11_d3_moving_knee_runs_d3efc56.json"
# The archived official manifests: path, the commit that archived them, SHA-256 of the file.
OFFICIAL = {
    "assembled": (ASSEMBLED, "ba4c9216ff00407fc3c97f4e9ddfe27745ab5a1a",
                  "e13e8654e7670a5e81e4c4ed5db8d5929ae705532020e2d1993cc67f86004758"),
    "growth": (GROWTH, "ba4c9216ff00407fc3c97f4e9ddfe27745ab5a1a",
               "6121e2e3c8220e2a7e51ea36e9abbd9a919e817196b2966fd5f2fb8b222b32ca"),
    "d3": (D3, "b5967e799fa22dcc0625d0575707d29cb19362b8",
           "d393797ec76cb89cce78073367c75a5af5bef7a2eebf41787a5a4f6006ddfa42"),
}
LABELS = {"female": "Female", "male": "Male", "gait2392": "Gait2392"}
LONG = {"female": "de Leva (1996) female reference body", "male": "de Leva (1996) male reference body",
        "gait2392": "OpenSim Gait2392 generic model"}
JOINT_LABEL = {"ankle": "LB:DOF:ANKLE_DORSI_PLANTAR_R", "knee": "LB:DOF:KNEE_FLEX_EXT_R", "hip": "LB:DOF:HIP_FLEX_EXT_R"}
NAMES = {**NAMES_14, "iliacus_r": "Iliacus", "psoas_r": "Psoas"}
GROUPS = [("Hip flexors (D4 growth)", ["iliacus_r", "psoas_r"])] + [tuple(g) for g in GROUPS_14]

# Review files that must exist; the timeline below cites them.
REVIEWS = {
    "d061": "docs/reviews/2026-11-11_ChatGPT_D061_Scope_57bfeaa.md",
    "d062a": "docs/reviews/2026-11-16_ChatGPT_D062_D061_Amendment1_ReReview_551efea.md",
    "d062b": "docs/reviews/2026-11-16_ChatGPT_D062_Amendment1_ReReview_3dcbb72.md",
    "b1": "docs/reviews/2026-11-16_ChatGPT_D4_Build_Review_d1ef9f2.md",
    "b2": "docs/reviews/2026-11-16_ChatGPT_D4_Build_ReReview_3c1623b.md",
    "b3": "docs/reviews/2026-11-16_ChatGPT_D4_Amendment5_ReReview_0a503d1.md",
    "v1": "docs/reviews/2026-11-16_ChatGPT_D4_Amendment6_Review_a40e7fb.md",
    "v2": "docs/reviews/2026-11-17_ChatGPT_D4_Amendment6_ReReview_c8839e9.md",
}

# How Stage D4 went, from DECISIONS.md (Q, A and D-062 amendments) and the review records above.
# (date, who, what happened, verdict or outcome, record)
TIMELINE = [
    ("2026-11-11", "Corbin", "Narrows the goal to one motion recreated from the ontology (Q65); agrees to the plan's next "
     "step, D4, \"where we have the ontology take the focus\" (Q66); limits the push to D4 (Q67).", "direction",
     "DECISIONS.md Q65-Q67"),
    ("2026-11-11", "Claude", "Proposes the squat proof-of-concept plan (D-061).", "proposal", "PR #43"),
    ("2026-11-11", "ChatGPT", "Reviews D-061: separate path topology from leverage (a path can cross a joint with zero "
     "moment arm), cover the deferred knee links, make validation claims conditional.", "AMEND (D061-B01 to B03)",
     REVIEWS["d061"]),
    ("2026-11-16", "ChatGPT", "Reviews the D4 scope D-062: account for the fixed-knee lateral gastrocnemius sign "
     "difference; catch symmetric missing knee links; specify the hip endpoint mapping.", "AMEND (D062-B01 to B03)",
     REVIEWS["d062a"]),
    ("2026-11-16", "Claude", "D-062 Amendment 1: direction check against the OpenSim reference, required-edge check, "
     "endpoint rule through the bony pelvis.", "amendment", "D-062 Amendment 1"),
    ("2026-11-16", "ChatGPT", "Re-reviews D-062 Amendment 1.", "AGREE", REVIEWS["d062b"]),
    ("2026-11-16", "Corbin", "\"Chat agreed and so do I so lets move on\": D-062 accepted (Q70); PRs #43 and #46 merged "
     "(A-19).", "accepted", "DECISIONS.md Q70, A-19"),
    ("2026-11-16", "Claude", "Builds D4 in four commits: ontology and schema (f949b34), generic assembler and dynamics "
     "(33f3ad6), checks, tools and runner (e81fa70), iliopsoas growth as data only (7c57224). Official runs at 31a9d3f.",
     "build", "D-062 Amendment 2; PR #47"),
    ("2026-11-16", "ChatGPT", "Build review: A2 did not compare every stored series and status; C1 checked a union of "
     "actuators; C4 lacked structural traceability; the run inventory missed active code.", "AMEND (D4-B01 to B04)",
     REVIEWS["b1"]),
    ("2026-11-16", "Claude", "D-062 Amendment 4: all four fixed; the d4-verify job added; official runs repeated at "
     "2f5c8a8 with identical series.", "amendment", "D-062 Amendment 4"),
    ("2026-11-16", "ChatGPT", "Re-review, triggering both hosted reruns itself: A2 replaced the emitted time and "
     "flattened nested structure; the manual workflow's comparison ref needed validation.", "AMEND (D4-B01 rest, B05)",
     REVIEWS["b2"]),
    ("2026-11-16", "Claude", "D-062 Amendment 5: both fixed; official runs repeated at af21e78, the runs this page "
     "shows.", "amendment", "D-062 Amendment 5"),
    ("2026-11-16", "ChatGPT", "Re-review: ran the verifier at the head (411 tests), regenerated the OpenSim references "
     "exactly and matched both D4 manifests to the official af21e78 files.", "AGREE", REVIEWS["b3"]),
    ("2026-11-16", "Corbin", "\"I agree and merged the pulls\": Stage D4 build accepted (Q74); PRs #47 and #48 merged "
     "(A-20).", "accepted", "DECISIONS.md Q74, A-20"),
    ("2026-11-16", "Claude", "D-062 Amendment 6: the verification job tolerates last-bit differences that another "
     "processor's OpenBLAS kernel produces in unrounded diagnostics (reproduced with OPENBLAS_CORETYPE=Haswell).",
     "amendment", "D-062 Amendment 6; PR #49"),
    ("2026-11-16", "ChatGPT", "The comparator exempted malformed residuals and treated a fractional sample index as "
     "rounding; the stated margin was too large.", "AMEND (D4-V01)", REVIEWS["v1"]),
    ("2026-11-17", "ChatGPT", "Re-review of the type-strict comparator: 435 tests, OpenSim references exact, both "
     "manifests matched.", "AGREE", REVIEWS["v2"]),
    ("2026-11-17", "Corbin", "\"Alright chat agreed and I merged\": PRs #49 and #50 merged.", "merged",
     "DECISIONS.md Q75, A-21"),
]

# Acceptance criteria fixed in D-062 before the build, and where the evidence is. Status for the criteria with a
# manifest field is computed from the manifests; the others cite the tests and records that carry them.
ACCEPTANCE = [
    ("A1", "Regression in process", "All bodies, all 301 poses, fixed and moving knee, against the D1-D3 modules: "
     "torques within 1e-9 N·m, lengths and moment arms within 1e-12 m, t* within 1e-7 N·m, activations within 1e-6, "
     "identical statuses.", None, "tests/test_phase_d4.py (test_a1_*); run by ChatGPT in the d4-verify job at 0a503d1 "
     "and c8839e9"),
    ("A2", "Regression to the official manifests", "D1 dd89fff, D2 7ac0f2d and D3 d3efc56: every series and status "
     "equal at the precision each stores.", "regression", "manifest field regression; section 5"),
    ("A3", "Independent checks on the assembled model", "Newton-Euler against Kane, virtual work, energy, Newton, "
     "forward steps; OpenSim oracle with coverage.", "verification", "manifest fields runs[].checks, "
     "oracle_references; section 6"),
    ("A4", "Consistency", "C1-C4 pass on the repaired ontology; on the unrepaired ontology the required-edge check "
     "and C1 flag the four muscles.", "consistency", "manifest field consistency; test_a4_on_the_unrepaired_ontology"),
    ("A5", "Deliberate errors are caught", "Deleting a crossing fails C1 naming the muscle; deleting an action fails "
     "C3; swapping a capability fails the direction check; a path through a joint centre passes C1 and C2 as "
     "negligible leverage; one-sided and two-sided deletions fail the mirror and required-edge checks.", None,
     "tests/test_phase_d4.py (test_a5_*)"),
    ("A6", "No anatomy in code", "The new modules contain no ontology IDs or anatomical terms.", None,
     "test_a6_no_anatomy_or_ontology_ids_in_the_new_modules, test_a6_scan_would_catch_a_planted_term"),
    ("A7", "Growth as data", "The iliopsoas commit (7c57224) changes no file in src/ or tools/; the new actuators match "
     "OpenSim; C1-C4 pass; the run completes and H1 is reported.", "growth", "growth manifest; test_a7_*; "
     "D-062 Amendment 2 step 4"),
    ("A8", "Nothing else breaks", "hip.yaml loads on its own; the Phase B tests pass unchanged.", None,
     "test_a8_hip_module_and_phase_b_unchanged; test_hip_module_still_loads_alone_without_knee_edges"),
    ("A9", "Standard checks", "Full test suite, integrity, probes, dataset check, provenance-verified manifests.",
     "provenance", "manifest field commit_provenance_status; d4-verify runs"),
]

# Claim B items (D-061) and what D4 shows for each.
CLAIM_B = [
    ("done", "The squat model is assembled from the ontology and its datasets by generic code that names no anatomy",
     "A1-A3 show nothing was lost; A6 scans the new modules"),
    ("done", "Anatomy added to the ontology enters the simulation as data, with no code change",
     "A7: iliacus and psoas, whose hip-switched path points the D1-D3 code could not represent"),
    ("done", "The ontology and the model check each other",
     "C1-C5 on every run; A4 caught the real knee gap; A5 catches deliberate ones"),
    ("next", "The assembled model performs the squat (muscle-driven forward simulation)", "Stage D7"),
]
CLAIM_A = [
    ("done", "Every number is sourced, derived or labelled as an assumption", "traceability gate; C4 traces 13 "
     "structural entities"),
    ("done", "Acceptance criteria written before results", "A1-A9 and H1 fixed in D-062 before the build"),
    ("done", "Computation verified by independent methods", "two dynamics formulations, OpenSim oracle, second solver"),
    ("next", "Evaluated against measured human data under preregistered criteria", "Stage D6"),
    ("done", "The other AI model reproduces the results", "ChatGPT's runs of the verifier and its manifest comparisons"),
    ("done", "Errors and corrections are on the record", "9 blocking findings in the D4 scope, build and verifier reviews (D062-B01 to B03, D4-B01 to B05, D4-V01), all fixed"),
    ("next", "A human expert reads the result", "Stage D9"),
]
ROADMAP = [
    ("done", "D1-D3", "Mechanics, muscles, moving knee"),
    ("done", "D4", "Model assembled from the ontology (this page)"),
    ("", "D5", "Gait2392's remaining leg muscles as data, through D4"),
    ("", "D6", "Measured squat; preregistered evaluation"),
    ("", "D7", "Muscle-driven forward simulation with a tracking controller"),
    ("", "D8", "Robustness and uncertainty"),
    ("", "D9", "Technical report, process audit, expert reader"),
    ("later", "E, F", "Clinical conditions and personalization"),
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


def _git_bytes(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"git {' '.join(args)} is not available ({exc}); build from a clone with history") from exc


def official_text(key, root=ROOT):
    """An official manifest exactly as archived: the working file at `root` if its SHA-256 is the recorded one,
    otherwise the file at its archive commit, checked against the same SHA-256. Never the edited working copy."""
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
    """(assembled, growth, d3), the archived official manifests."""
    return tuple(json.loads(official_text(k)) for k in ("assembled", "growth", "d3"))


def is_official(path, key):
    """True when a manifest file given on the command line is byte for byte the official file for its role."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() == OFFICIAL[key][2]


def pinned_text(record):
    """The text of an input file exactly as a run read it: the working-tree file if its SHA-256 still matches the
    manifest's record, otherwise the Git blob the manifest records."""
    path = ROOT / record["path"]
    if path.exists():
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() == record["sha256"]:
            return data.decode("utf-8")
    data = _git_bytes("cat-file", "-p", record["git_blob_id"])
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise SystemExit(f"{record['path']}: blob {record['git_blob_id']} does not match the manifest's SHA-256")
    return data.decode("utf-8")


def ontology(manifest):
    mods = [yaml.safe_load(pinned_text(manifest["inputs"][k])) for k in ("ontology_hip", "ontology_lower_limb_sagittal")]
    ents, srcs, models, additions = {}, {}, {}, []
    for m in mods:
        ents.update(m["entities"])
        srcs.update(m.get("sources") or {})
        models.update(m.get("models") or {})
        additions += m.get("relationship_additions") or []
    return ents, srcs, models, additions


def short(i):
    return i.split(":")[-1].lower() if i.startswith("LB:ACT:G2392:") else i


# ------------------------------------------------------------------ runs
def drawing_order(manifest):
    return [short(a) for a in manifest["specification"]["actuators"]]


def check_same_drawing(d4, d3, order4, order3):
    """The D4 muscle drawings equal D3's at every sample (D3's actuator order), so the figure's joint points and the
    muscles come from the same model. Raises if not."""
    for k in range(len(d3)):
        for j, name in enumerate(order3):
            if d4[k][order4.index(name)] != d3[k][j]:
                raise SystemExit(f"D4 drawing of {name} at sample {k} differs from D3's")


def runs_of(manifest, d3, order3):
    order = drawing_order(manifest)
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
            "scale": round(x["scale"], 6), "foot": r(by3[b]["foot"], 4),
            "q": {j: r(list(np.degrees(s["q_rad"][c])), 2) for j, c in JOINT_LABEL.items()},
            "tau": {j: r(s["tau_per_side_N_m"][c], 2) for j, c in JOINT_LABEL.items()},
            "pts": {k: r(p3[k], 4) for k in ("knee", "hip", "hat_drawing_top")},
            "act": r(s["activation"], 3), "force": r(s["tendon_force_N"], 1),
            "paths": [[r(f[order.index(n)], 4) for n in order] for f in s["muscle_path_xy_m"]], "order": order,
            "tstar": r(s["t_star_N_m"], 4), "status": x["status"], "contact": x["contact"],
            "how_built": x["how_built"],
            "segments": {k: {"mass_kg": round(v["mass_kg"], 4), "com_m": v["com_m"], "inertia": round(v["inertia_kg_m2"], 5)}
                         for k, v in x["segments_per_side"].items()},
            "verification": x["verification"], "reserve": x["reserve_summary"],
            "params": {a["name"]: {"fmax": a["max_isometric_force_N"],
                                   "lopt_mm": round(a["optimal_fiber_length_m"] * 1000, 1),
                                   "lts_mm": round(a["tendon_slack_length_m"] * 1000, 1),
                                   "penn_deg": round(float(np.degrees(a["pennation_at_optimal_rad"])), 1)}
                       for a in x["actuators"]},
        }
    return out


def checks_of(manifest, tol, d2p):
    """Mechanics residuals for every run (both knees), with the tolerance each was checked against."""
    rows = {}
    for x in manifest["runs"]:
        for k, v in x["checks"]["residuals"].items():
            row = rows.setdefault(k, {"worst": 0.0, "passed": True, "runs": 0})
            row["worst"] = max(row["worst"], abs(v))
            row["passed"] = row["passed"] and x["checks"]["passed"][k]
            row["runs"] += 1
    tkey = {"newton_identity_per_side_N": "newton_identity_N", "mass_bookkeeping_relative": "mass_fraction_sum"}
    for k, row in rows.items():
        row["tolerance"] = tol[tkey.get(k, k)]
    opt = {k: max(abs(x["verification"][k]) for x in manifest["runs"]) for k in manifest["runs"][0]["verification"]}
    solver = {k: {"value": d2p[k]["value"], "unit": d2p[k]["unit"]}
              for k in ("kkt_tolerance", "second_solver_t_star_tolerance", "second_solver_activation_tolerance")}
    return {"mechanics": rows, "optimizer": opt, "solver_tolerances": solver,
            "optimizer_passed": all(x["status"]["optimizer_verification"] == "passed" for x in manifest["runs"]),
            "runs": len(manifest["runs"])}


# ------------------------------------------------------------------ ontology views
def coordinate_views(ents, spec_name, models):
    spec = models[spec_name]
    out = []
    for joint, j in spec["modelled_joints"].items():
        c = ents[j["coordinate"]]
        loc = j["location"]
        out.append({"joint": joint, "joint_name": ents[joint]["name"], "coordinate": j["coordinate"],
                    "positive": c.get("positive_motion"), "negative": c.get("negative_motion"),
                    "model": c.get("model_coordinates"), "convention": c.get("convention"),
                    "child_frame": j["child_frame"], "location": loc})
    merged = [{"joint": k, "name": ents.get(k, {}).get("name", k), **v} for k, v in spec["merged_joints"].items()]
    return out, merged, spec


def consistency_view(manifest, ents):
    c = manifest["consistency"]
    name = lambda i: ents.get(i, {}).get("name", i)  # noqa: E731
    c1 = [{"actuator": short(a), "muscle": v["muscle"], "muscle_name": name(v["muscle"]),
           "declared": [name(j) for j in v["declared_modelled"]], "derived": [name(j) for j in v["derived"]],
           "crossed_not_modelled": [name(j) for j in v["crossed_not_modelled"]], "agrees": v["agrees"]}
          for a, v in c["C1_crossings"]["per_actuator"].items()]
    coords = list(JOINT_LABEL.values())
    c2 = {}
    for key, v in c["C2_leverage"]["largest_abs_moment_arm_m"].items():
        a, q = key.split(" | ")
        c2.setdefault(short(a), {})[[j for j, cc in JOINT_LABEL.items() if cc == q][0]] = v
    direction = {}
    for case, v in c["C3_actions"]["direction"].items():
        direction[case] = {k: v[k] for k in v if not isinstance(v[k], list)}
        direction[case]["above_zero"] = [{**d, "actuator": short(d["actuator"])} for d in v["disagreements_above_numerical_zero"]]
        direction[case]["at_least_1mm"] = [{**d, "actuator": short(d["actuator"])} for d in v.get("disagreements_at_least_1mm", [])]
    reg = c["C5_deviation_register"]
    return {
        "summary": [
            ("C1", "Crossings by topology", c["C1_crossings"]["passed"], len(c["C1_crossings"]["failures"])),
            ("C2", "Leverage by geometry", c["C2_leverage"]["passed"], len(c["C2_leverage"]["failures"])),
            ("C3", "Actions and direction", c["C3_actions"]["passed"],
             len(c["C3_actions"]["structural_failures"]) + len(c["C3_actions"]["direction_failures"])),
            ("C4", "Evidence and traceability", c["C4_evidence"]["passed"], len(c["C4_evidence"]["failures"])),
            ("RE", "Required edges", c["required_edges"]["passed"], len(c["required_edges"]["missing"])),
            ("MI", "Left-right mirror", c["mirror"]["passed"], len(c["mirror"]["differences"])),
        ],
        "passed": c["passed"], "c1": c1, "c2": c2, "c2_negligible": c["C2_leverage"]["crosses_negligible_leverage"],
        "coords": coords, "direction": direction,
        "out_of_plane": {name(k): v for k, v in c["C3_actions"]["out_of_plane_capabilities"].items() if v},
        "c4_basis": [{"entity": k, "name": name(k), "kind": v["kind"], "traced": v["traced"],
                      "basis": v["basis"]} for k, v in c["C4_evidence"]["structural_basis"].items()],
        "c4_capabilities": c["C4_evidence"]["capabilities_checked"],
        "register": {
            "represented": {"actuators": {short(a): name(m) for a, m in reg["represented"]["actuators"].items()},
                            "coordinates": [name(x) for x in reg["represented"]["coordinates"]],
                            "joints": [name(x) for x in reg["represented"]["modelled_joints"]],
                            "segments": {name(k): [name(x) for x in v] for k, v in reg["represented"]["segments"].items()}},
            "simplified": {"assumptions": reg["simplified"]["assumptions"],
                           "locked": [{"joint": name(x["joint"]), "into": name(x["into"]), "state": x["state"],
                                       "note": x["note"]} for x in reg["simplified"]["locked_or_merged_joints"]],
                           "crossed_not_modelled": {name(k): [name(x) for x in v]
                                                    for k, v in reg["simplified"]["crossed_not_modelled"].items()}},
            "omitted": {"coordinates": [name(x) for x in reg["omitted"]["coordinates"]],
                        "muscles": [name(x) for x in reg["omitted"]["muscles_crossing_a_modelled_joint_without_an_actuator"]],
                        "out_of_plane": {name(k): v for k, v in reg["omitted"]["out_of_plane_capabilities"].items()}},
        },
    }


def additions_view(additions, ents, srcs):
    out = []
    for a in additions:
        e = ents[a["entity"]]
        out.append({"entity": a["entity"], "name": e["name"], "side": e.get("side"),
                    "add": {k: [ents[j]["name"] for j in v] for k, v in a["add"].items()},
                    "evidence": [{"id": s, "title": srcs.get(s, {}).get("title", s), "url": srcs.get(s, {}).get("url")}
                                 for s in a["evidence"]],
                    "basis": a["basis"], "decision": a["decision"]})
    return out


def muscle_cards(manifest, ents, srcs, additions, cons):
    added = {a["entity"]: a for a in additions}
    out = {}
    for a in manifest["runs"][0]["actuators"]:
        e = ents[a["represents"]]
        rel = e.get("relationships", {})
        merged = {k: list(v) for k, v in rel.items()}
        if a["represents"] in added:
            for k, v in added[a["represents"]]["add"].items():
                merged[k] = merged.get(k, []) + v
        c1 = next(x for x in cons["c1"] if x["actuator"] == a["name"])
        out[a["name"]] = {
            "entity": a["represents"], "entity_name": e["name"], "actuator": a["id"],
            "crosses": [ents[j]["name"] for j in merged.get("CROSSES", [])],
            "acts_on": [ents[j]["name"] for j in merged.get("ACTS_ON", [])],
            "added_in_d4": {k: [ents[j]["name"] for j in v] for k, v in added[a["represents"]]["add"].items()}
            if a["represents"] in added else None,
            "nerves": [ents.get(n, {}).get("name", n) for n in rel.get("INNERVATED_BY", [])],
            "capabilities": [c.replace("_", " ") for c in e.get("mechanical_capabilities", [])],
            "evidence": [{"id": s, "title": srcs.get(s, {}).get("title", s), "url": srcs.get(s, {}).get("url")}
                         for s in e.get("evidence", [])],
            "c1": c1, "c2": cons["c2"][a["name"]],
        }
    return out


# ------------------------------------------------------------------ regression, growth
def regression_view(manifest):
    out = []
    for case, v in manifest["regression"].items():
        body, variant = case.split(" | ")
        for role, m in v["by_manifest"].items():
            series = m["series"]
            statuses = m["statuses"]
            out.append({"body": body, "variant": variant, "role": role, "manifest": m["manifest"],
                        "commit": m["commit_sha"], "series": len(series),
                        "largest_excess": max(s["excess_over_half_unit"] for s in series.values()),
                        "decimals": sorted({s["stored_decimals"] for s in series.values()}),
                        "series_names": sorted(series), "statuses": len(statuses),
                        "statuses_equal": all(s["equal"] for s in statuses.values())})
    return {"rows": out, "passed": manifest["status"]["regression_to_official_manifests"],
            "largest_excess": max(v["largest_excess"] for v in manifest["regression"].values())}


def growth_view(growth, assembled, models, ents):
    h = growth["hypotheses"][0]
    spec = models["squat_d4_iliopsoas"]
    a14 = {x["body"]: x for x in assembled["runs"] if x["variant"] == "moving_knee"}
    peaks = {}
    for x in growth["runs"]:
        if x["variant"] != "moving_knee":
            continue
        b = x["body"]
        before, after = a14[b]["series"]["activation"], x["series"]["activation"]
        peaks[b] = {n: [round(max(before[n]), 3) if n in before else None, round(max(after[n]), 3)] for n in after}
    added = [{"actuator": short(a), "id": a, "represents": ents[a]["represents"],
              "muscle_name": ents[ents[a]["represents"]]["name"], "note": ents[a].get("note")}
             for a in spec["add_actuators"]]
    return {"hypothesis": h, "spec": {"extends": spec["extends"], "description": spec["description"]},
            "added": added, "oracle": growth["oracle_references"], "status": growth["status"],
            "consistency_passed": growth["consistency"]["passed"], "peaks": peaks,
            "provenance": growth["commit_provenance_status"], "input_files": len(growth["verified_input_files"])}


def acceptance_view(assembled, growth):
    s = assembled["status"]
    state = {
        "regression": s["regression_to_official_manifests"] == "passed",
        "verification": all(s[k] == "passed" for k in ("mechanics_verification", "optimizer_verification",
                                                        "oracle_verification")),
        "consistency": s["consistency_checks"] == "passed" and assembled["consistency"]["passed"],
        "growth": all(growth["status"][k] == "passed" for k in ("mechanics_verification", "optimizer_verification",
                                                                "oracle_verification", "consistency_checks")),
        "provenance": all(m["commit_provenance_status"] == "verified_git_head_and_inputs" for m in (assembled, growth)),
    }
    return [{"id": a, "name": n, "text": t, "from_manifest": k is not None,
             "passed": state[k] if k else None, "evidence": ev} for a, n, t, k, ev in ACCEPTANCE]


# ------------------------------------------------------------------ data
def build_data(assembled, growth, d3, paths=(ASSEMBLED, GROWTH, D3), official=True):
    for p in REVIEWS.values():
        if not (ROOT / p).exists():
            raise SystemExit(f"cited review record missing: {p}")
    ents, srcs, models, additions = ontology(assembled)
    if ontology(growth)[0] != ents:
        raise SystemExit("the two D4 manifests read different ontology files")
    tol = yaml.safe_load(pinned_text(assembled["inputs"]["d3_config"]))["tolerances"]
    d2p = yaml.safe_load(pinned_text(assembled["inputs"]["d2_config"]))["parameters"]
    order3 = [a["name"] for a in d3["runs"][0]["actuators"]]
    cons = consistency_view(assembled, ents)
    coords, merged, spec = coordinate_views(ents, "squat_d4", models)
    sets = {"d4": runs_of(assembled, d3, order3), "growth": runs_of(growth, d3, order3)}
    t = assembled["runs"][0]["series"]["t_s"]
    if growth["runs"][0]["series"]["t_s"] != t:
        raise SystemExit("the two D4 runs have different time series")
    return {
        "t": r(t, 3), "names": NAMES, "groups": GROUPS, "bodies": list(LABELS), "sets": sets,
        "muscles": muscle_cards(growth, ents, srcs, additions, consistency_view(growth, ents)),
        "spec": {"name": spec_name(assembled), "segments": [ents[s]["name"] for s in assembled["specification"]["segments"]],
                 "segment_ids": assembled["specification"]["segments"],
                 "tree": [[ents[j]["name"], ents[a]["name"], ents[b]["name"]] for j, a, b in assembled["specification"]["tree"]],
                 "endpoints": [{"joint": ents.get(e["joint"], {}).get("name", e["joint"]),
                                "endpoints": [ents.get(x, {}).get("name", x) for x in e["endpoints"]] if e["endpoints"] else None,
                                "note": e["note"]} for e in assembled["specification"]["endpoint_resolution"]],
                 "ground": spec["ground"], "description": spec["description"], "datasets": spec["datasets"],
                 "coordinates": coords, "merged": merged, "variants": spec["variants"],
                 "actuators": len(assembled["specification"]["actuators"])},
        "consistency": cons, "additions": additions_view(additions, ents, srcs),
        "regression": regression_view(assembled), "checks": checks_of(assembled, tol, d2p),
        "oracle": assembled["oracle_references"], "growth": growth_view(growth, assembled, models, ents),
        "status": assembled["status"], "acceptance": acceptance_view(assembled, growth),
        "timeline": [{"date": d, "who": w, "text": t, "verdict": v, "ref": ref} for d, w, t, v, ref in TIMELINE],
        "claim_a": CLAIM_A, "claim_b": CLAIM_B, "roadmap": ROADMAP,
        "validity": assembled["validity"], "source_validation": assembled["source_validation"],
        "what_checks_show": assembled["what_the_checks_show"], "assumptions": assembled["configuration"]["assumptions"],
        "inputs": {"assembled": len(assembled["verified_input_files"]),
                   "code_modules": sum(k.startswith("code_") for k in assembled["inputs"]),
                   "provenance": assembled["commit_provenance_status"]},
        "manifests": {"assembled": [str(paths[0]), assembled["commit_sha"]], "growth": [str(paths[1]), growth["commit_sha"]],
                      "d3": [str(paths[2]), d3["commit_sha"]]},
        "official": official,
    }


def spec_name(manifest):
    return manifest["specification"]["name"]


TEMPLATE = (Path(__file__).with_name("squat_demo_d4_template.html")).read_text(encoding="utf-8")


def render(assembled, growth, d3, paths=(ASSEMBLED, GROWTH, D3), official=True):
    data = json.dumps(build_data(assembled, growth, d3, paths, official), separators=(",", ":"), allow_nan=False)
    return TEMPLATE.replace("__DATA__", data.replace("</", "<\\/"))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--assembled", help="a D4 manifest other than the official one (the page is marked custom)")
    p.add_argument("--growth", help="a growth manifest other than the official one (the page is marked custom)")
    p.add_argument("--d3", help="a D3 manifest other than the official one (the page is marked custom)")
    p.add_argument("--output", type=Path, default=ROOT / "SQUAT_DEMO_D4.html")
    a = p.parse_args()
    given = (a.assembled, a.growth, a.d3)
    official = load_official()
    if all(g is None or is_official(g, k) for g, k in zip(given, ("assembled", "growth", "d3"))):
        html = render(*official)
    else:
        chosen = tuple(json.loads(Path(g).read_text(encoding="utf-8")) if g else m for g, m in zip(given, official))
        paths = tuple(g or d for g, d in zip(given, (ASSEMBLED, GROWTH, D3)))
        html = render(*chosen, paths, official=False)
        print("Custom inputs: the page is marked as not built from the official records")
    a.output.write_text(html, encoding="utf-8", newline="\n")
    print(f"Demo written to {a.output} ({len(html.encode()) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
