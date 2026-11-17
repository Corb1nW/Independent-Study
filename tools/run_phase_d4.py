"""Run a Stage D4 model specification for every configured body and variant; write one manifest (D-062).

    python -m tools.run_phase_d4 --commit-sha FULL_SHA --output results/phase_d/<date>_d4_assembled_runs_<sha>.json
    python -m tools.run_phase_d4 --config <another run configuration> --commit-sha FULL_SHA --output <file>

For each body and variant: the model assembled from the specification in the ontology (src/model_spec.py,
src/model_assembly.py), its mechanics checks and contact feasibility, and the muscles' force law and two-stage
recruitment (src/muscle_paths.py with src/muscles_d2.py). Then, once per specification: the anatomy-model consistency
checks C1-C5 (src/consistency.py), the geometry and kinematics against the OpenSim references, the regression to the
official manifests named in the configuration (criterion A2), and any pre-stated hypothesis. Exit code 1 when a
verification fails; flagged contact, muscle feasibility or force-law domain, and hypothesis outcomes, are results.

Everything model-specific comes from the specification and the configuration; this runner names no anatomy.
"""
import argparse
from decimal import Decimal
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

from src import consistency as cs
from src import model_assembly as ma
from src import muscle_paths as mp
from src import squat_d1 as sq          # its configuration loader reads the D1 motion, gravity and contact parameters
from src.model_spec import load_spec
from src.run_manifest import manifest_header, verify_inputs  # noqa: F401  (verify_inputs used by tests)
from tools import run_phase_d2 as d2r
from tools.oracle_coverage import check_reference

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "phase_d4_assembled.yaml"
REQUIRED = {"model_id", "decision", "specification", "baseline_variant", "d1_config", "d2_config", "d3_config",
            "bodies", "variants", "references", "direction_check_reference_variants", "regression", "hypotheses",
            "assumptions", "omitted_physics"}
# Data files read by the run besides the ontology, datasets, configurations, references and manifests, which come
# from the specification and the configuration. Project code is not listed one file at a time: every module of src/ and tools/
# loaded in this process is verified (ChatGPT D4-B04).
INPUTS = {name: ROOT / rel for name, rel in {
    "schema": "ontology/quantitative_schema.yaml",
    "source_degroote_header": "sources/vendor/opensim-core/DeGrooteFregly2016Muscle.h",
    "source_osim_model": "sources/vendor/opensim-models/gait2392_millard2012muscle.osim",  # read by oracle_coverage
}.items()}
CODE_DIRS = ("src", "tools")


def code_inputs(root=ROOT):
    """{input name: path} for every module of the project's src/ and tools/ loaded in this process (the active code
    dependencies of the run), relative to ROOT and re-rooted at `root`."""
    out = {}
    for mod in list(sys.modules.values()):
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        path = Path(f).resolve()
        if path.suffix != ".py" or not path.is_relative_to(ROOT):
            continue
        rel = path.relative_to(ROOT)
        if rel.parts[0] in CODE_DIRS:
            out["code_" + rel.with_suffix("").as_posix().replace("/", "_")] = Path(root) / rel
    return dict(sorted(out.items()))


def input_paths(cfg, spec, config_path, root=ROOT):
    """Every file the run reads, by name, re-rooted at `root`: data files, specification datasets and ontology
    modules, configurations, references, pinned manifests and the loaded project code."""
    def rr(p):
        return Path(root) / Path(p).resolve().relative_to(ROOT)
    paths = {k: rr(v) for k, v in INPUTS.items()}
    paths.update({f"ontology_{p.stem}": rr(p) for p in spec.schema.ontology_paths()})
    paths.update({f"dataset_{role}": rr(ROOT / "ontology" / "quantitative_data" / f)
                  for role, f in spec.dataset_files.items()})
    paths.update(config=rr(config_path), d1_config=rr(ROOT / cfg["d1_config"]), d2_config=rr(ROOT / cfg["d2_config"]),
                 d3_config=rr(ROOT / cfg["d3_config"]))
    paths.update({f"reference_{v}": rr(ROOT / r["path"]) for v, r in cfg["references"].items()})
    for v, roles in (cfg["regression"].get("manifests") or {}).items():
        paths.update({f"official_{v}_{role}": rr(ROOT / m["path"]) for role, m in roles.items()})
    for name, rule in (cfg["regression"].get("statuses") or {}).items():
        if "manifest" in rule:
            paths[f"status_{name}_manifest"] = rr(ROOT / rule["manifest"])
    paths.update({f"hypothesis_{h['id']}_comparison": rr(ROOT / h["comparison"]) for h in cfg["hypotheses"]})
    paths.update(code_inputs(root))
    return paths


def load_config(path=CONFIG):
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(cfg, dict) or set(cfg) != REQUIRED:
        raise ValueError("configuration fields must be exactly: " + ", ".join(sorted(REQUIRED)))
    if cfg["baseline_variant"] not in cfg["variants"]:
        raise ValueError("baseline_variant must be one of the variants")
    for v in cfg["direction_check_reference_variants"]:
        if v not in cfg["references"]:
            raise ValueError(f"variant {v}: a direction check against a reference needs that reference")
    for h in cfg["hypotheses"]:
        if set(h) != {"id", "statement", "measure", "groups", "windows_s", "removed_if_at_most", "comparison"}:
            raise ValueError("a hypothesis needs id, statement, measure, groups, windows_s, removed_if_at_most and "
                             "comparison")
        if h["measure"] != "smaller_of_group_maxima" or len(h["groups"]) != 2:
            raise ValueError("the only hypothesis measure is smaller_of_group_maxima over two actuator groups")
    if not all(isinstance(a, str) and a.strip() for a in cfg["assumptions"]):
        raise ValueError("assumptions must be non-empty text")
    return cfg


def _r(a, digits=6):
    return np.round(np.asarray(a, float), digits).tolist()


def _decimals(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return max(0, -Decimal(repr(float(value))).as_tuple().exponent)


def _flatten(x):
    if isinstance(x, (list, tuple, np.ndarray)):
        return [y for item in x for y in _flatten(item)]
    return [x]


def _is_sequence(x):
    return isinstance(x, (list, tuple)) or (isinstance(x, np.ndarray) and x.ndim > 0)


def shape_difference(stored, new, path=""):
    """Where the nesting of `new` first differs from `stored` (a sequence against a value, or a different length at
    any level, including each frame and actuator of a ragged muscle path), or None when they have the same shape
    (ChatGPT D4-B01: flattening alone would accept two frames merged into one)."""
    if _is_sequence(stored) != _is_sequence(new):
        return f"{path or '/'}: {'sequence' if _is_sequence(stored) else 'value'} stored, " \
               f"{'sequence' if _is_sequence(new) else 'value'} new"
    if _is_sequence(stored):
        if len(stored) != len(new):
            return f"{path or '/'}: length {len(stored)} stored, {len(new)} new"
        for i, (a, b) in enumerate(zip(stored, new)):
            d = shape_difference(a, b, f"{path}[{i}]")
            if d:
                return d
    return None


def stored_precision_difference(stored, new, rounded_to=0):
    """Largest excess of |new - stored| over half a unit of the series' last stored decimal, in units of that half
    unit. The decimals are those the producing runner rounded to (`rounded_to`), or more if the stored values show
    more. 0 means equal at the stored precision. An entry with no stored value (null) must have no new value either;
    a stored number must have a finite new number; a shape difference or a non-numeric entry is infinite excess
    (ChatGPT D4-B01). The nested shapes must agree before the values are compared leaf by leaf."""
    if shape_difference(stored, new) is not None:
        return float("inf"), rounded_to
    flat_s = _flatten(stored)
    try:
        n = [float(x) for x in _flatten(new)]
    except (TypeError, ValueError):
        return float("inf"), rounded_to
    digits = max([rounded_to] + [d for d in map(_decimals, flat_s) if d is not None])
    half = 0.5 * 10.0 ** (-digits)
    if len(flat_s) != len(n):
        return float("inf"), digits
    worst = 0.0
    for a, b in zip(flat_s, n):
        if a is None or (isinstance(a, float) and math.isnan(a)):
            if not math.isnan(b):
                return float("inf"), digits
            continue
        if isinstance(a, bool) or not isinstance(a, (int, float)) or not math.isfinite(a) or not math.isfinite(b):
            return float("inf"), digits
        excess = abs(float(a) - b) - half * (1 + 1e-9) - 1e-15
        worst = max(worst, excess / half if excess > 0 else 0.0)
    return worst, digits


# --------------------------------------------------------------------------------------------- one run
def run_case(spec, body, variant, d1p, d2p, tol, full_series):
    model = ma.assemble(spec, body, variant)
    res = ma.run(model, d1p)
    checks = ma.check_residuals(model, d1p, res)
    passed = {k: abs(v) <= tol[k] for k, v in checks.items() if k in tol}
    passed["newton_identity_per_side_N"] = checks["newton_identity_per_side_N"] <= tol["newton_identity_N"]
    passed["mass_bookkeeping_relative"] = abs(checks["mass_bookkeeping_relative"]) <= tol["mass_fraction_sum"]
    if set(passed) != set(checks):
        raise ValueError(f"checks without a tolerance: {sorted(set(checks) - set(passed))}")
    q, qd, tau = res["q"], res["qd"], res["tau"]
    mus = mp.recruit_series(model, q, qd, tau, d2p["solver_band_delta"])
    w = mus["worst"]
    optimizer_ok = (w["kkt"] <= d2p["kkt_tolerance"] and w["t_star_difference"] <= d2p["second_solver_t_star_tolerance"]
                    and w["activation_difference"] <= d2p["second_solver_activation_tolerance"]
                    and np.all(np.isfinite(mus["activation"])) and np.all(np.isfinite(mus["reserve"])))
    eps = d2p["epsilon_reserve"]
    t_star = mus["t_star"]
    status = {"mechanics_verification": "passed" if all(passed.values()) else "failed",
              "contact_feasibility": "feasible" if res["contact"]["feasible"] else "flagged",
              "optimizer_verification": "passed" if optimizer_ok else "failed",
              "muscle_feasibility": "feasible" if float(np.max(t_star)) <= eps else "flagged",
              "force_law_domain": "flagged" if mus["flags"] else "in_domain",
              "source_validation": d2r.SOURCE_VALIDATION["status"]}
    peak = int(np.argmax(t_star))
    names = [a.name for a in model.actuators]
    coords = model.coordinates
    out = {
        "body": body, "variant": variant, "scale": model.scale, "status": status, "body_mass_kg": model.body_mass,
        "stature_m": model.stature, "how_built": model.derivations,
        "segments_per_side": {s: {"mass_kg": seg.mass, "com_m": _r(seg.com, 9), "inertia_kg_m2": seg.inertia}
                              for s, seg in model.segments.items()},
        "contact_points_m": {k: _r(v[:2], 9) for k, v in model.contact.items()},
        "checks": {"residuals": checks, "passed": passed, "all_passed": all(passed.values())},
        "contact": res["contact"],
        "verification": {"largest_kkt_residual": w["kkt"], "second_solver_t_star_difference_N_m": w["t_star_difference"],
                         "second_solver_activation_difference": w["activation_difference"]},
        "reserve_summary": {
            "norm": "largest absolute per-coordinate reserve (L-infinity), D-059 Amendment 2",
            "t_star_max_N_m": round(float(np.max(t_star)), 6), "t_star_max_time_s": float(res["t"][peak]),
            "q_at_t_star_max_deg": [round(math.degrees(x), 3) for x in q[:, peak]],
            "flagged_samples": int(np.sum(t_star > eps)), "epsilon_reserve_N_m": eps,
            "solver_band_delta_N_m": d2p["solver_band_delta"]},
        "force_law_domain_flags": mus["flags"],
        "path_length_jumps": path_length_jumps(model, d1p),
        "actuators": [{"name": a.name, "id": a.id, "represents": a.entity, "max_isometric_force_N": a.f0,
                       "optimal_fiber_length_m": round(a.l_opt, 9), "tendon_slack_length_m": round(a.l_ts, 9),
                       "pennation_at_optimal_rad": a.alpha0} for a in model.actuators],
    }
    series = {
        "t_s": _r(res["t"], 9), "q_rad": {c: _r(q[i], 9) for i, c in enumerate(coords)},
        "tau_per_side_N_m": {c: _r(tau[i]) for i, c in enumerate(coords)},
        "moving_centre_terms_N_m": {j: _r(v) for j, v in res["moving_centre_terms"].items()},
        "grf_per_side_N": {"x": _r(res["grf"][0]), "y": _r(res["grf"][1])}, "cop_x_m": _r(res["cop_x"], 9),
        "t_star_N_m": _r(t_star, 9),
        "reserve_per_coordinate_N_m": {c: _r(mus["reserve"][i], 9) for i, c in enumerate(coords)},
        "smallest_needed_reserve_per_coordinate_N_m": {c: _r(mus["needed"][i], 9) for i, c in enumerate(coords)},
        "activation": {n: _r(mus["activation"][j]) for j, n in enumerate(names)},
        "tendon_force_N": {n: _r(mus["force"][j], 3) for j, n in enumerate(names)},
        "normalized_fiber_length": {n: _r(mus["l_norm"][j], 5) for j, n in enumerate(names)},
        "normalized_fiber_velocity": {n: _r(mus["v_norm"][j], 5) for j, n in enumerate(names)},
        "muscle_path_xy_m": mus["drawing"],
    }
    raw = {"t": res["t"], "kin": res["kinematics"],
           "joint_segment": {seg.inbound.joint: sid for sid, seg in model.segments.items() if seg.inbound},
           "q": q, "tau": tau, "grf": res["grf"], "cop": res["cop_x"], "terms": res["moving_centre_terms"],
           "activation": mus["activation"], "t_star": t_star, "reserve": mus["reserve"], "needed": mus["needed"],
           "force": mus["force"], "l_norm": mus["l_norm"], "v_norm": mus["v_norm"], "drawing": mus["drawing"],
           "names": names, "status": status, "contact": res["contact"]}
    if full_series:
        out["series"] = series
    return model, out, raw


def path_length_jumps(model, d1p):
    """Path-length jump at each conditional switch inside the motion, in proportion along the motion (D-059
    Amendment 2), for whichever coordinate drives the point."""
    depth = np.asarray(d1p["depth_angles"], float)
    out = []
    for a in model.actuators:
        for p in a.points:
            if p.kind != "conditional":
                continue
            c = p.coordinate
            ratio = depth / depth[c]
            for edge in (p.active_range[0] - ma.ACTIVITY_TOL, p.active_range[1] + ma.ACTIVITY_TOL):
                qc = p.sign * edge
                if not 0.0 < qc < depth[c]:
                    continue
                sides = [ratio * (qc - 1e-9), ratio * (qc + 1e-9)]
                with_pt = [x for x in sides if ma.point_active(p, x)]
                without = [x for x in sides if not ma.point_active(p, x)]
                L_with = mp.path(model, a, with_pt[0])[0]
                L_without = mp.path(model, a, without[0])[0]
                out.append({"actuator": a.name, "point": p.name, "coordinate": model.coordinates[c],
                            "coordinate_deg": round(math.degrees(qc), 4),
                            "length_with_point_minus_without_mm": round(1000 * (L_with - L_without), 6)})
    return out


# ------------------------------------------------------------------------------------------- OpenSim
def reference_comparison(model, ref, kinematics_map=None):
    """Largest length and moment-arm differences (m) against an OpenSim reference's geometry rows, for the
    reference's actuators that the model has; and kinematics where the reference has them."""
    by_name = {a.name: a for a in model.actuators}
    names = [n for n in ref["actuators"] if n in by_name]
    dl = dr = 0.0
    for g in ref["geometry"]:
        q = np.array(g["q"])
        frames = ma.segment_frames(model, q)
        for n in names:
            L, R, _ = mp.path(model, by_name[n], q, frames)
            dl = max(dl, abs(L - g["length_m"][n]))
            dr = max(dr, float(np.max(np.abs(R - np.array(g["moment_arm_m"][n])))))
    out = {"actuators_compared": names, "largest_length_difference_m": dl, "largest_moment_arm_difference_m": dr}
    if ref.get("kinematics") and kinematics_map:
        zero = np.zeros((len(model.coordinates), 1))
        err = 0.0
        for row in ref["kinematics"]:
            k = ma.kinematics(model, np.array(row["q"])[:, None], zero, zero)
            for key, (quantity, segment) in kinematics_map.items():
                v = k[segment]["o" if quantity == "origin" else "c"][:, 0]
                err = max(err, float(np.max(np.abs(v - np.array(row[key][:2])))))
        out["largest_kinematics_difference_m"] = err
    return out


# ---------------------------------------------------------------------------------------- regression
def _point(raw, rule):
    """A position series (2 x n) under a legacy label: a joint centre, a centre of mass, or the drawing point
    joint centre + 2 x (centre of mass - joint centre) of a segment (D1's upper-body drawing convention)."""
    kin = raw["kin"]
    if rule["quantity"] == "joint_centre":
        return kin[raw["joint_segment"][rule["joint"]]]["joint"]
    if rule["quantity"] == "centre_of_mass":
        return kin[rule["segment"]]["c"]
    if rule["quantity"] == "drawing_point":
        k = kin[rule["segment"]]
        return k["joint"] + 2 * (k["c"] - k["joint"])
    raise ValueError(f"unknown point quantity {rule['quantity']}")


def _quantity(raw, rule, reg):
    """The new values for one official series, arranged as the official manifest stores it: (values, keys) where
    keys name the manifest's sub-series in the order of the values' first axis, or None for a plain list."""
    q = rule["quantity"]
    if q == "moving_centre_term":
        return raw["terms"][rule["joint"]], None
    if q == "points":
        labels = list(reg["point_labels"])
        return [_point(raw, reg["point_labels"][k]) for k in labels], labels
    values = raw[q]
    index = rule.get("index")
    if index == "coordinate":
        return values, [reg["coordinate_labels"][c] for c in reg["coordinate_labels"]]
    if index == "actuator":
        return values, list(raw["names"])
    if index == "component":
        return values, list(rule["components"])
    return values, None


def _stored(series, name, keys, components=None):
    """The stored values in the order of `keys`; a points series is stored as {label: {x: [...], y: [...]}}."""
    s = series[name]
    if keys is None:
        return s
    if set(s) != set(keys):
        raise KeyError(f"{name}: stored keys {sorted(s)} differ from {sorted(keys)}")
    out = [s[k] for k in keys]
    if out and isinstance(out[0], dict):
        out = [[v[c] for c in ("x", "y")] for v in out]
    return out


def _derived_status(name, rule, raw, context):
    """A status of an earlier stage whose meaning differs from D4's per-case statuses, mapped as the configuration
    states it."""
    kind = rule["derived"]
    if kind == "torque_agreement":
        official = json.loads((ROOT / rule["manifest"]).read_text(encoding="utf-8"))
        run = next(r for r in official["runs"] if r["body"] == raw["body"])
        stored = np.array([run["series"][rule["series"]][context["reg"]["coordinate_labels"][c]]
                           for c in context["reg"]["coordinate_labels"]], float)
        diff = float(np.max(np.abs(np.round(raw["tau"], rule["decimals"]) - stored)))
        return "passed" if diff <= context["d2p"][rule["tolerance_parameter"]] else "failed"
    if kind == "reference_kinematics":
        o = (context.get("oracle") or {}).get(rule["reference_variant"], {})
        err = o.get("largest_kinematics_difference_m")
        return "passed" if err is not None and err < context["tol"]["kinematics_oracle_m"] else "failed"
    raise ValueError(f"{name}: unknown derived status {kind}")


def regression(raw, case_cfg, reg, context=None):
    """A2 (ChatGPT D4-B01): for each pinned manifest, the run's series and status key sets must equal the
    configured required sets; every required series must equal this run at the stored precision and every required
    status must equal this run's, directly or through a stated mapping. A missing, extra or unmapped field fails."""
    context = dict(context or {}, reg=reg)
    out, worst, problems = {}, 0.0, []
    for role, m in case_cfg.items():
        official = json.loads((ROOT / m["path"]).read_text(encoding="utf-8"))
        runs = [r for r in official["runs"] if r["body"] == raw["body"]]
        if len(runs) != 1:
            problems.append(f"{role}: {len(runs)} runs for body {raw['body']}")
            continue
        run = runs[0]
        s, st = run.get("series", {}), run.get("status", {})
        for kind, have, want in (("series", set(s), set(m["series"])), ("status", set(st), set(m["statuses"]))):
            for k in sorted(want - have):
                problems.append(f"{role}: required {kind} {k} missing from the manifest")
            for k in sorted(have - want):
                problems.append(f"{role}: manifest {kind} {k} is not in the required set")
        result, statuses = {}, {}
        for name in m["series"]:
            rule = reg["series"].get(name)
            if rule is None:
                problems.append(f"{role}: series {name} has no mapping")
                continue
            if name not in s:
                continue
            try:
                new, keys = _quantity(raw, rule, reg)
                stored = _stored(s, name, keys)
            except (KeyError, ValueError) as exc:
                problems.append(f"{role}: series {name}: {exc}")
                continue
            excess, digits = stored_precision_difference(_nan_list(stored), new, rule["decimals"])
            result[name] = {"stored_decimals": digits, "excess_over_half_unit": excess}
            shape = shape_difference(stored, new)
            if shape:
                result[name]["shape_difference"] = shape
            worst = max(worst, excess)
        for name in m["statuses"]:
            rule = reg["statuses"].get(name)
            if rule is None:
                problems.append(f"{role}: status {name} has no mapping")
                continue
            if name not in st:
                continue
            mine = raw["status"].get(rule["same"]) if "same" in rule else _derived_status(name, rule, raw, context)
            statuses[name] = {"manifest": st[name], "this_run": mine, "equal": st[name] == mine,
                              "mapping": rule}
        out[role] = {"manifest": m["path"], "commit_sha": official["commit_sha"], "series": result,
                     "statuses": statuses}
    ok = (not problems and worst == 0.0
          and all(v["equal"] for o in out.values() for v in o["statuses"].values()))
    return {"passed": ok, "largest_excess": worst, "problems": problems, "by_manifest": out}


def _nan_list(stored):
    def conv(x):
        if isinstance(x, list):
            return [conv(y) for y in x]
        return float("nan") if x is None else x
    return conv(stored)


# ---------------------------------------------------------------------------------------- hypotheses
def hypothesis(h, runs_raw, baseline):
    """Smaller of the two groups' largest activations at each sample, maximized over the stated windows."""
    def measure(act_by_name, t):
        mask = np.zeros_like(t, dtype=bool)
        for lo, hi in h["windows_s"]:
            mask |= (t >= lo - 1e-12) & (t <= hi + 1e-12)
        g = [np.max(np.array([act_by_name[n] for n in group], float), axis=0) for group in h["groups"]]
        return round(float(np.max(np.minimum(g[0], g[1])[mask])), 6)
    official = json.loads((ROOT / h["comparison"]).read_text(encoding="utf-8"))
    values = {}
    for (body, variant), raw in runs_raw.items():
        if variant != baseline:
            continue
        t = raw["t"]
        acts = {n: raw["activation"][j] for j, n in enumerate(raw["names"])}
        names = {n for g in h["groups"] for n in g}
        if not names <= set(acts):
            raise ValueError(f"{h['id']}: actuators {sorted(names - set(acts))} are not in the model")
        run = next(r for r in official["runs"] if r["body"] == body)
        before = measure(run["series"]["activation"], np.array(run["series"]["t_s"], float))
        values[body] = {"this_run": measure(acts, t), "comparison": before}
    removed = all(v["this_run"] <= h["removed_if_at_most"] for v in values.values())
    return {"id": h["id"], "statement": h["statement"], "measure": h["measure"], "groups": h["groups"],
            "windows_s": h["windows_s"], "removed_if_at_most": h["removed_if_at_most"],
            "comparison_manifest": h["comparison"], "values": values,
            "outcome": "supported" if removed else "not supported",
            "note": "Pre-stated (D-062 item 9); reported either way, not an acceptance criterion."}


# ------------------------------------------------------------------------------------------- manifest
def run_cases(spec, cfg, d1p, d2p, tol):
    """Every body and variant of the configuration: (runs, raws, models). The raw output keeps the time the run
    emitted, the same array its published `t_s` comes from (ChatGPT D4-B01: A2 compares what the run produced)."""
    runs, raws, models = [], {}, []
    for body in cfg["bodies"]:
        for variant in cfg["variants"]:
            model, out, raw = run_case(spec, body, variant, d1p, d2p, tol, variant == cfg["baseline_variant"])
            raw["body"] = body
            models.append(model)
            raws[(body, variant)] = raw
            runs.append(out)
    return runs, raws, models


def run_regressions(cfg, raws, context):
    """A2 for every body and every variant that has pinned manifests."""
    reg_cfg = cfg["regression"]
    out = {}
    for v, roles in (reg_cfg.get("manifests") or {}).items():
        for body in cfg["bodies"]:
            out[f"{body} | {v}"] = regression(raws[(body, v)], roles, reg_cfg, context)
    return out


def build_manifest(commit_sha, config_path=CONFIG):
    cfg = load_config(config_path)
    d1_cfg, d1p = sq.load_config(ROOT / cfg["d1_config"])
    d2_cfg, d2p = d2r.load_config(ROOT / cfg["d2_config"])
    tol = yaml.safe_load((ROOT / cfg["d3_config"]).read_text(encoding="utf-8"))["tolerances"]
    spec = load_spec(cfg["specification"])
    refs = {v: json.loads((ROOT / r["path"]).read_text(encoding="utf-8")) for v, r in cfg["references"].items()}
    paths = input_paths(cfg, spec, config_path)
    manifest = manifest_header(ROOT, {k: str(v) for k, v in paths.items()}, commit_sha)
    runs, raws, models = run_cases(spec, cfg, d1p, d2p, tol)
    # Consistency (C1-C5) over every body and variant.
    q = raws[(cfg["bodies"][0], cfg["variants"][0])]["q"]
    arms = {(m.body, m.variant): mp.moment_arm_series(m, q) for m in models}
    ref_arms = {}
    for v in cfg["direction_check_reference_variants"]:
        rows = sorted((g for g in refs[v]["geometry"] if g["kind"] == "d1_sample"), key=lambda g: g["index"])
        ref_arms[v] = {n: np.array([g["moment_arm_m"][n] for g in rows]).T for n in refs[v]["actuators"]}
    consistency = cs.run_checks(spec, models, arms, ref_arms)
    # OpenSim references (A3), on the reference body.
    ref_body = next(b for b, s in spec.bodies.items() if s["geometry_scale"] == "reference")
    oracle = {}
    for v, ref in refs.items():
        model = next(m for m in models if m.body == ref_body and m.variant == v)
        mode = cfg["references"][v]["coverage_mode"]
        oracle[v] = {"path": cfg["references"][v]["path"], "coverage_problems": check_reference(ref, mode),
                     "model_specification": ref["provenance"].get("model_specification"),
                     **reference_comparison(model, ref, cfg["references"][v].get("kinematics"))}
    oracle_ok = all(not o["coverage_problems"] and o["largest_length_difference_m"] < 1e-9
                    and o["largest_moment_arm_difference_m"] < 1e-9
                    and o.get("largest_kinematics_difference_m", 0.0) < tol["kinematics_oracle_m"]
                    for o in oracle.values())
    # Regression to the official manifests (A2).
    regressions = run_regressions(cfg, raws, {"oracle": oracle, "tol": tol, "d2p": d2p})
    reg_ok = all(r["passed"] for r in regressions.values())
    hyps = [hypothesis(h, raws, cfg["baseline_variant"]) for h in cfg["hypotheses"]]
    late = sorted(set(code_inputs()) - set(paths))
    if late:     # fail closed: code loaded after the provenance check was not verified
        raise ValueError(f"project modules loaded after input verification: {late}")
    statuses = [r["status"] for r in runs]
    status = {
        "mechanics_verification": "passed" if all(s["mechanics_verification"] == "passed" for s in statuses) else "failed",
        "optimizer_verification": "passed" if all(s["optimizer_verification"] == "passed" for s in statuses) else "failed",
        "oracle_verification": "passed" if oracle_ok else "failed",
        "consistency_checks": "passed" if consistency["passed"] else "failed",
        "regression_to_official_manifests": ("not_applicable" if not regressions else "passed" if reg_ok else "failed"),
        "contact_feasibility": "feasible" if all(s["contact_feasibility"] == "feasible" for s in statuses) else "flagged",
        "muscle_feasibility": {f"{r['body']} | {r['variant']}": r["status"]["muscle_feasibility"] for r in runs},
        "force_law_domain": "in_domain" if all(s["force_law_domain"] == "in_domain" for s in statuses) else "flagged",
        "source_validation": d2r.SOURCE_VALIDATION["status"]}
    manifest.update({
        "status": status, "decision": cfg["decision"], "model_id": cfg["model_id"],
        "specification": {"name": spec.name, "extends": spec.raw.get("extends"), "actuators": spec.actuators,
                          "coordinates": spec.coordinates, "segments": spec.segments,
                          "tree": [list(t) for t in spec.tree], "endpoint_resolution": spec.endpoint_log},
        "what_the_checks_show": ("Verification that the model assembled from the ontology reproduces the accepted "
                                 "Stage D1-D3 results and computes its mechanics and muscles correctly (two dynamics "
                                 "formulations, virtual work, energy, Newton, forward consistency; geometry and "
                                 "kinematics against OpenSim), and that anatomy and model agree (C1-C4, with the "
                                 "deviations listed in C5). Not validation against measured squats or muscle activity."),
        "configuration": cfg, "d2_configuration": d2_cfg,
        "consistency": consistency, "oracle_references": oracle, "regression": regressions, "hypotheses": hyps,
        "runs": runs, "source_validation": d2r.SOURCE_VALIDATION,
    })
    return manifest


def exit_code(manifest):
    s = manifest["status"]
    ok = (s["mechanics_verification"] == "passed" and s["optimizer_verification"] == "passed"
          and s["oracle_verification"] == "passed" and s["consistency_checks"] == "passed"
          and s["regression_to_official_manifests"] in ("passed", "not_applicable"))
    return 0 if ok else 1


def summary_lines(manifest):
    s = manifest["status"]
    lines = [f"{manifest['specification']['name']}: mechanics {s['mechanics_verification'].upper()}, optimizer "
             f"{s['optimizer_verification'].upper()}, OpenSim {s['oracle_verification'].upper()}, consistency "
             f"{s['consistency_checks'].upper()}, regression {s['regression_to_official_manifests'].upper()}; contact "
             f"{s['contact_feasibility']}; force-law domain {s['force_law_domain']}"]
    for r in manifest["runs"]:
        lines.append(f"  {r['body']} | {r['variant']}: muscles {r['status']['muscle_feasibility']} "
                     f"(t* max {r['reserve_summary']['t_star_max_N_m']:.3f} N m)")
    for h in manifest["hypotheses"]:
        vals = ", ".join(f"{b} {v['comparison']:.3f} -> {v['this_run']:.3f}" for b, v in h["values"].items())
        lines.append(f"  {h['id']}: {h['outcome']} ({vals})")
    lines.append("A VERIFICATION FAILED: do not use." if exit_code(manifest) else
                 "Verification passed. A demonstration under stated assumptions; not validated.")
    return lines


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--commit-sha", required=True)
    p.add_argument("--config", type=Path, default=CONFIG)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    manifest = build_manifest(args.commit_sha, args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, sort_keys=True, allow_nan=False, separators=(",", ":"),
                                      default=_jsonable) + "\n", encoding="utf-8")
    for line in summary_lines(manifest):
        print(line)
    print("Manifest written to", args.output)
    sys.exit(exit_code(manifest))


def _jsonable(x):
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, tuple):
        return list(x)
    raise TypeError(type(x))


if __name__ == "__main__":
    main()
