"""Anatomy and model check each other (D-062 item 7 with Amendment 1): checks C1-C5, the required-edge check and the
mirror check (item 5).

- C1, crossings by topology: for EACH actuator, the modelled joints between the frames that carry its path points must
  equal its muscle's declared CROSSES, restricted to modelled joints. Merged joints on that route are listed as
  "crossed, not modelled".
- C2, leverage by geometry: moment arms over the whole motion, without reading CROSSES. A coordinate with
  |R| > 1e-9 m must belong to a C1 crossing or to a declared coupling; a crossing whose largest |R| is below 1 mm is
  recorded as "crosses, negligible leverage".
- C3, actions: ACTS_ON within CROSSES; every in-plane capability names a joint in ACTS_ON; out-of-plane capabilities
  recorded. Direction: where |R| >= 1 mm, the motion the actuator drives (the coordinate's positive_motion for R > 0,
  negative_motion for R < 0) must be a declared capability of a muscle it represents. A disagreement passes only when
  the specification declares it (expected_direction_deviations: actuator, coordinate, variant, the motion it drives
  and a basis) AND the OpenSim reference's own moment arm at that sample is at least 1 mm with the same sign, computed
  from the reference alone, with no ontology capability (D-063 Amendment 1, ChatGPT D5-R01). Undeclared, unconfirmed
  and stale declarations fail.
- C4, evidence: every represented muscle, every edge and capability the checks use, and every actuator resolve to a
  registered source; every consumed observation passes the D-055 traceability gate; every represented segment, joint
  and coordinate has an entity-level basis (its evidence, the sourced records that represent it, or for a coordinate
  its convention), or C4 fails naming it.
- C5, the deviation register: represented, simplified and omitted elements, every direction disagreement, the declared
  deviations with their bases, and the complete inventory of muscles without an actuator (D-063 Amendment 1).
- Required edges: a represented muscle needs its C1 crossings as CROSSES and the crossed joints its in-plane
  capabilities name as ACTS_ON; its counterpart on the other side needs the same edges, side swapped.
- Mirror: paired entities have mirrored relationships among non-computational entities (one-sided changes).

Generic: no ontology IDs or anatomical terms here (criterion A6). Side counterparts follow the ontology's ID
convention (a side suffix) and are confirmed by the entities' `side` fields.
"""
from .input_gate import require_traceable
from .model_spec import SpecError, joint_endpoints, represented

NUMERICAL_ZERO = 1e-9      # m (D-062 C2)
MATERIAL = 1e-3            # m (D-062 C2, C3)
SUFFIX = {"right": "_R", "left": "_L"}
OTHER = {"right": "left", "left": "right"}
COMPUTATIONAL = ("ModelActuator", "CoordinateFrame", "ModelJoint")


# ----------------------------------------------------------------------------------------- helpers
def counterpart(onto, eid):
    """The same entity on the other side, or None (no side, or no counterpart in the ontology)."""
    side = onto.get(eid).get("side")
    if side not in SUFFIX or not eid.endswith(SUFFIX[side]):
        return None
    other = eid[: -len(SUFFIX[side])] + SUFFIX[OTHER[side]]
    if other in onto.entities and onto.get(other).get("side") == OTHER[side]:
        return other
    return None


def mirrored(onto, eid):
    """An ID with its side swapped when a counterpart exists; otherwise the ID itself (a midline entity)."""
    return counterpart(onto, eid) or eid


def muscles(spec):
    """{muscle: [actuators]} for the specification's actuators, in their order. A lumped actuator is listed under
    every muscle it represents (D-063 item 5)."""
    out = {}
    for a in spec.actuators:
        for m in represented(spec.ontology, a):
            out.setdefault(m, []).append(a)
    return out


def capabilities(onto, actuator):
    """The mechanical capabilities of the muscles an actuator represents (their union for a lumped actuator)."""
    out = []
    for m in represented(onto, actuator):
        out += [c for c in onto.get(m).get("mechanical_capabilities", []) if c not in out]
    return out


def in_plane_motions(spec):
    """{motion name: (coordinate, +1 or -1)} for the retained coordinates' positive and negative motions."""
    out = {}
    for c, info in spec.coordinate_info.items():
        out[info.positive_motion] = (c, 1)
        out[info.negative_motion] = (c, -1)
    return out


def _frame_graph(spec):
    edges = {}
    for j in spec.joints.values():
        edges.setdefault(j.parent_frame, []).append((j.child_frame, j.id))
        edges.setdefault(j.child_frame, []).append((j.parent_frame, j.id))
    return edges


def _route(edges, a, b):
    """Joints on the route between two frames of the model's frame tree."""
    prev, frontier = {a: None}, [a]
    while frontier:
        cur = frontier.pop(0)
        for nxt, j in edges.get(cur, []):
            if nxt not in prev:
                prev[nxt] = (cur, j)
                frontier.append(nxt)
    if b not in prev:
        raise SpecError(f"frames {a} and {b} are not connected in the model")
    out, cur = [], b
    while prev[cur] is not None:
        cur, j = prev[cur]
        out.append(j)
    return out


# --------------------------------------------------------------------------------------------- C1
def derived_crossings(spec, actuator_frames):
    """{actuator: (modelled joints, merged joints)} on the routes between the frames carrying its path points."""
    edges = _frame_graph(spec)
    modelled = [j for j, _, _ in spec.tree]
    out = {}
    for a, frames in actuator_frames.items():
        frames = list(dict.fromkeys(frames))
        crossed = set()
        for f in frames[1:]:
            crossed |= set(_route(edges, frames[0], f))
        out[a] = ([j for j in modelled if j in crossed], [j.id for j in spec.merged_joints() if j.id in crossed])
    return out


def actuator_frames(model):
    return {a.id: [p.frame for p in a.points] for a in model.actuators}


def check_c1(spec, crossings):
    """C1 per actuator (ChatGPT D4-B02): each actuator's derived modelled crossings must equal its muscle's declared
    CROSSES restricted to modelled joints. A failure names the actuator. The per-muscle union is kept as a summary."""
    onto, modelled = spec.ontology, [j for j, _, _ in spec.tree]
    failures, per_muscle, per_actuator = [], {}, {}
    for m, acts in muscles(spec).items():
        declared = [j for j in onto.related(m, "CROSSES") if j in modelled]
        for a in acts:
            derived = crossings[a][0]
            missing, extra = set(derived) - set(declared), set(declared) - set(derived)
            if len(represented(onto, a)) == 1:
                per_actuator[a] = {"muscle": m, "derived": derived, "declared_modelled": declared,
                                   "crossed_not_modelled": crossings[a][1], "agrees": not missing and not extra}
            else:   # lumped: checked against each represented muscle (D-063 item 5)
                entry = per_actuator.setdefault(a, {"muscles": represented(onto, a), "derived": derived,
                                                    "declared_modelled_per_muscle": {},
                                                    "crossed_not_modelled": crossings[a][1], "agrees": True})
                entry["declared_modelled_per_muscle"][m] = declared
                entry["agrees"] = entry["agrees"] and not missing and not extra
            if missing or extra:
                failures.append({"actuator": a, "muscle": m, "missing_CROSSES": sorted(missing),
                                 "declared_but_not_crossed": sorted(extra)})
        per_muscle[m] = {"actuators": acts,
                         "derived": sorted({j for a in acts for j in crossings[a][0]}, key=modelled.index),
                         "declared_modelled": declared,
                         "crossed_not_modelled": sorted({j for a in acts for j in crossings[a][1]})}
    return {"passed": not failures, "failures": failures, "per_actuator": per_actuator, "per_muscle": per_muscle}


# --------------------------------------------------------------------------------------------- C2
def check_c2(spec, crossings, arms, couplings=()):
    """`arms`: {case: (actuator IDs, array actuators x coordinates x samples)} over every body and variant."""
    coords = spec.coordinates
    joint_of = {c: spec.coordinate_info[c].joint for c in coords}
    failures, largest = [], {}
    for case, (acts, R) in arms.items():
        for i, a in enumerate(acts):
            for k, c in enumerate(coords):
                peak = float(abs(R[i, k]).max())
                largest[(a, c)] = max(largest.get((a, c), 0.0), peak)
                if peak > NUMERICAL_ZERO and joint_of[c] not in crossings[a][0] and (a, c) not in couplings:
                    failures.append({"case": case, "actuator": a, "coordinate": c, "largest_abs_moment_arm_m": peak})
    negligible = [{"actuator": a, "joint": joint_of[c], "coordinate": c, "largest_abs_moment_arm_m": largest[(a, c)]}
                  for a in crossings for c in coords
                  if joint_of[c] in crossings[a][0] and largest.get((a, c), 0.0) < MATERIAL]
    return {"passed": not failures, "failures": failures, "crosses_negligible_leverage": negligible,
            "largest_abs_moment_arm_m": {f"{a} | {c}": v for (a, c), v in largest.items()}}


# --------------------------------------------------------------------------------------------- C3
def direction_disagreements(spec, acts, R, threshold):
    """[(actuator, coordinate, sample, sign)] where |R| >= threshold and the driven motion is not a capability."""
    onto, out = spec.ontology, []
    for i, a in enumerate(acts):
        caps = set(capabilities(onto, a))
        for k, c in enumerate(spec.coordinates):
            info = spec.coordinate_info[c]
            for n in range(R.shape[2]):
                r = R[i, k, n]
                if abs(r) >= threshold:
                    motion = info.positive_motion if r > 0 else info.negative_motion
                    if motion not in caps:
                        out.append((a, c, n, 1 if r > 0 else -1))
    return out


def _summarize(spec, entries, R_by_act):
    groups = {}
    for a, c, n, sgn in entries:
        groups.setdefault((a, c, sgn), []).append(n)
    out = []
    for (a, c, sgn), ns in groups.items():
        r = R_by_act[a][spec.coordinates.index(c)]
        extreme = max((r[n] for n in ns), key=abs)
        info = spec.coordinate_info[c]
        out.append({"actuator": a, "coordinate": c, "drives": info.positive_motion if sgn > 0 else info.negative_motion,
                    "samples": len(ns), "first_sample": min(ns), "last_sample": max(ns),
                    "extreme_moment_arm_m": float(extreme), "extreme_sample": int(ns[[r[n] for n in ns].index(extreme)])})
    return out


def declared_deviations(spec):
    """{(actuator, coordinate, variant, motion driven): declaration} from the specification (D-063 Amendment 1). The
    motion is part of the key: an actuator may drive both of a coordinate's motions against its capabilities, at
    different poses, and each is declared separately."""
    out = {}
    for d in spec.raw.get("expected_direction_deviations") or []:
        for v in d["variants"]:
            out[(d["actuator"], d["coordinate"], v, d["drives"])] = d
    return out


def check_c3(spec, arms, references=None):
    """`references`: {variant: {actuator model name: array coordinates x samples}}, the OpenSim moment arms on the
    reference body, used only to confirm declared deviations.

    Direction rule (D-063 Amendment 1, ChatGPT D5-R01), the same for every case: each disagreement of at least 1 mm must
    be declared for its actuator, coordinate and variant, drive the declared motion, and be confirmed at that sample by
    the reference's own moment arm (|r| >= 1 mm, same sign), which is read from the reference and never compared with
    an ontology capability. A declaration that matches no disagreement on any body is stale. All three fail."""
    onto = spec.ontology
    motions = in_plane_motions(spec)
    structural, out_of_plane = [], {}
    for m in muscles(spec):
        crosses, acts_on = set(onto.related(m, "CROSSES")), set(onto.related(m, "ACTS_ON"))
        if not acts_on <= crosses:
            structural.append({"muscle": m, "ACTS_ON_not_in_CROSSES": sorted(acts_on - crosses)})
        caps = onto.get(m).get("mechanical_capabilities", [])
        for cap in caps:
            if cap in motions:
                joint = spec.coordinate_info[motions[cap][0]].joint
                if joint not in acts_on:
                    structural.append({"muscle": m, "capability": cap, "joint_missing_from_ACTS_ON": joint})
        out_of_plane[m] = [cap for cap in caps if cap not in motions]
    references = references or {}
    declared = declared_deviations(spec)
    used = set()
    direction, failures = {}, []
    for (body, variant), (acts, R) in arms.items():
        R_by_act = {a: R[i] for i, a in enumerate(acts)}
        material = direction_disagreements(spec, acts, R, MATERIAL)
        all_nonzero = direction_disagreements(spec, acts, R, NUMERICAL_ZERO)
        ref = references.get(variant)
        undeclared, unconfirmed, accepted = [], [], []
        for a, c, n, sgn in material:
            info = spec.coordinate_info[c]
            drives = info.positive_motion if sgn > 0 else info.negative_motion
            d = declared.get((a, c, variant, drives))
            if d is None:
                undeclared.append((a, c, n, sgn))
                continue
            name = onto.model_element(a)[1]
            k = spec.coordinates.index(c)
            r_ref = float(ref[name][k][n]) if ref is not None and name in ref else 0.0
            if abs(r_ref) >= MATERIAL and (r_ref > 0) == (sgn > 0):
                accepted.append((a, c, n, sgn))
                used.add((a, c, variant, drives))
            else:
                unconfirmed.append({"actuator": a, "coordinate": c, "sample": n,
                                    "reference_moment_arm_m": r_ref if ref is not None and name in ref else None})
        entry = {"policy": "declared_and_reference_confirmed",
                 "disagreements_at_least_1mm": _summarize(spec, material, R_by_act),
                 "disagreements_above_numerical_zero": _summarize(spec, all_nonzero, R_by_act),
                 "declared_and_confirmed": _summarize(spec, accepted, R_by_act),
                 "reference_available": ref is not None}
        if undeclared:
            failures.append({"case": [body, variant], "undeclared": _summarize(spec, undeclared, R_by_act)})
        if unconfirmed:
            failures.append({"case": [body, variant], "unconfirmed_by_reference": unconfirmed})
        direction[f"{body} | {variant}"] = entry
    variants_run = {v for _, v in arms}
    stale = [{"actuator": a, "coordinate": c, "variant": v, "drives": m} for (a, c, v, m) in declared
             if v in variants_run and a in spec.actuators and (a, c, v, m) not in used]
    if stale:
        failures.append({"stale_declarations": stale})
    return {"passed": not structural and not failures, "structural_failures": structural,
            "direction_failures": failures, "direction": direction, "out_of_plane_capabilities": out_of_plane,
            "declared_deviations": [dict(d) for d in spec.raw.get("expected_direction_deviations") or []]}


# --------------------------------------------------------------------------------------------- C4
CONVENTION_MARK = "Declared model convention"   # how a coordinate's own convention text identifies itself


def structural_basis(spec, consumed):
    """Entity-level trace for every represented segment, joint and coordinate (ChatGPT D4-B03).

    Bases, any of which suffices:
    - evidence: the entity's own registered sources;
    - records: consumed dataset records whose target names the entity (for a segment, the entity or one of its merged
      parts), with the sources their claims cite;
    - for a coordinate, its convention: a registered convention source, or a convention text that identifies itself
      as a declared model convention.
    Merged joints also carry the specification's declared state (an assumption, listed, not a basis by itself)."""
    onto = spec.ontology
    sources = set(onto.sources)
    targets = {}
    for name, ids in consumed.items():
        role = next(r for r, f in spec.dataset_files.items() if f == name)
        data = spec.datasets[role]
        known = sources | set(data.get("sources") or {})
        for oid in sorted(set(ids)):
            rec = data["observations"][oid]
            cited = [c.get("source_id") for c in (rec.get("provenance") or {}).get("source_claims") or []]
            cited = [c for c in cited if c in known]
            if not cited:
                continue
            for e in (rec.get("target") or {}).get("entity_ids") or []:
                targets.setdefault(e, []).append({"record": oid, "sources": cited})
    out = {}
    elements = ([(x, "segment") for x in spec.segments] + [(x, "joint") for x in spec.joints]
                + [(x, "coordinate") for x in spec.coordinates])
    for eid, kind in elements:
        e = onto.get(eid)
        basis = {}
        ev = [x for x in e.get("evidence", []) if x in sources]
        if ev:
            basis["evidence"] = ev
        linked = [eid] + ([p for p in spec.parts.get(eid, []) if p != eid] if kind == "segment" else [])
        recs = [r for x in linked for r in targets.get(x, [])]
        if recs:
            basis["records"] = recs
        if kind == "coordinate":
            ref = e.get("convention_reference")
            if ref in sources:
                basis["convention_source"] = ref
            if str(e.get("convention", "")).startswith(CONVENTION_MARK):
                basis["declared_model_convention"] = e["convention"]
        entry = {"kind": kind, "basis": basis, "traced": bool(basis)}
        if kind == "joint" and eid in spec.raw.get("merged_joints", {}):
            entry["declared_state"] = spec.raw["merged_joints"][eid].get("state")
        out[eid] = entry
    return out


def check_c4(spec, consumed):
    onto, failures = spec.ontology, []
    sources = set(onto.sources)
    motions = in_plane_motions(spec)
    for m in muscles(spec):
        ev = [s for s in onto.get(m).get("evidence", []) if s in sources]
        if not ev:
            failures.append({"entity": m, "problem": "no registered evidence"})
        for pred in ("CROSSES", "ACTS_ON"):
            for t in onto.related(m, pred):
                if not [s for s in onto.edge_evidence(m, pred, t) if s in sources]:
                    failures.append({"entity": m, "edge": [pred, t], "problem": "no registered evidence"})
    for a in spec.actuators:
        if not [s for s in onto.get(a).get("evidence", []) if s in sources]:
            failures.append({"entity": a, "problem": "no registered evidence"})
    gate = {}
    for name, ids in consumed.items():
        role = next(r for r, f in spec.dataset_files.items() if f == name)
        try:
            gate[name] = require_traceable(spec.schema, spec.datasets[role], sorted(set(ids)))
        except ValueError as exc:
            failures.append({"dataset": name, "problem": str(exc)})
    structure = structural_basis(spec, consumed)
    for eid, entry in structure.items():
        if not entry["traced"]:
            failures.append({"entity": eid, "problem": f"represented {entry['kind']} has no traceable basis"})
    return {"passed": not failures, "failures": failures, "traceability": gate,
            "capabilities_checked": sorted(motions), "structural_basis": structure}


# ---------------------------------------------------------------------------------- required edges
def required_edges(spec, crossings):
    """{entity: {predicate: [joints]}} required on both sides (D-062 Amendment 1, D062-B02)."""
    onto, motions = spec.ontology, in_plane_motions(spec)
    req = {}
    for m, acts in muscles(spec).items():
        crossed = sorted({j for a in acts for j in crossings[a][0]})
        named = {spec.coordinate_info[motions[cap][0]].joint for cap in onto.get(m).get("mechanical_capabilities", [])
                 if cap in motions}
        req[m] = {"CROSSES": crossed, "ACTS_ON": [j for j in crossed if j in named]}
        other = counterpart(onto, m)
        if other is None:
            raise SpecError(f"muscle {m} has no counterpart on the other side")
        req[other] = {p: [mirrored(onto, j) for j in js] for p, js in req[m].items()}
    return req


def check_required_edges(spec, crossings):
    onto, missing = spec.ontology, []
    for e, preds in required_edges(spec, crossings).items():
        for p, js in preds.items():
            for j in js:
                if j not in onto.related(e, p):
                    missing.append({"entity": e, "predicate": p, "target": j})
    return {"passed": not missing, "missing": missing}


def check_mirror(onto):
    """Paired entities have mirrored relationships, ignoring computational elements (one-sided by design)."""
    def anatomical(t):
        return onto.get(t).get("class") not in COMPUTATIONAL

    differences = []
    for eid, e in onto.entities.items():
        if e.get("side") != "right":
            continue
        other = counterpart(onto, eid)
        if other is None:
            continue
        a = {p: sorted(mirrored(onto, t) for t in ts if anatomical(t)) for p, ts in e.get("relationships", {}).items()}
        b = {p: sorted(t for t in ts if anatomical(t)) for p, ts in onto.get(other).get("relationships", {}).items()}
        a, b = {p: v for p, v in a.items() if v}, {p: v for p, v in b.items() if v}
        if a != b:
            differences.append({"pair": [eid, other],
                                "predicates": sorted(p for p in set(a) | set(b) if a.get(p) != b.get(p))})
    return {"passed": not differences, "differences": differences}


# --------------------------------------------------------------------------------------------- C5
def deviation_register(spec, c1, c2, c3):
    onto = spec.ontology
    modelled = [j for j, _, _ in spec.tree]
    represented_muscles = set(muscles(spec))
    omitted_muscles = sorted(m for m, e in onto.entities.items()
                             if e.get("class") == "SkeletalMuscle" and m not in represented_muscles
                             and set(onto.related(m, "CROSSES")) & set(modelled))
    inventory = {"crossing_a_modelled_joint": [], "crossing_only_joints_the_model_does_not_have": [],
                 "crossing_no_joint": []}
    for m, e in sorted(onto.entities.items()):     # every muscle without an actuator (D-063 Amendment 1, D5-R02)
        if e.get("class") != "SkeletalMuscle" or m in represented_muscles:
            continue
        crosses = set(onto.related(m, "CROSSES"))
        key = ("crossing_a_modelled_joint" if crosses & set(modelled)
               else "crossing_only_joints_the_model_does_not_have" if crosses else "crossing_no_joint")
        inventory[key].append(m)
    owner = {p: s for s, ps in spec.parts.items() for p in ps}
    omitted_joints = []
    for j, e in onto.entities.items():
        if j in spec.joints or not onto.related(j, "CONNECTS"):
            continue
        try:
            ends = joint_endpoints(onto, j)
        except SpecError:
            continue
        if ends and all(x in owner for x in ends):
            omitted_joints.append(j)
    merged = [{"joint": j.id, "into": j.into, "state": spec.raw["merged_joints"][j.id].get("state"),
               "endpoints": list(j.endpoints) if j.endpoints else None,
               "note": None if j.endpoints else "merged; endpoints not stated in the ontology"}
              for j in spec.merged_joints()]
    simplified_elements = [{"entity": e, "simplifications": onto.get(e)["simplifications"]}
                           for e in list(spec.actuators) + list(spec.segments) + list(spec.joints)
                           if onto.get(e).get("simplifications")]
    return {
        "represented": {"segments": {s: spec.parts[s] for s in spec.segments}, "modelled_joints": modelled,
                        "coordinates": spec.coordinates, "actuators": {a: onto.get(a)["represents"] for a in spec.actuators}},
        "simplified": {"merged_segments": {s: ps for s, ps in spec.parts.items() if len(ps) > 1},
                       "locked_or_merged_joints": merged,
                       "crossed_not_modelled": {m: v["crossed_not_modelled"] for m, v in c1["per_muscle"].items()
                                                if v["crossed_not_modelled"]},
                       "elements": simplified_elements,
                       "assumptions": list(spec.raw.get("assumptions") or [])},
        "omitted": {"coordinates": list(spec.raw.get("omitted_coordinates") or []), "joints": sorted(omitted_joints),
                    "muscles_crossing_a_modelled_joint_without_an_actuator": omitted_muscles,
                    "muscles_without_an_actuator": inventory,
                    "out_of_plane_capabilities": {m: v for m, v in c3["out_of_plane_capabilities"].items() if v}},
        "crosses_negligible_leverage": c2["crosses_negligible_leverage"],
        "direction_disagreements": {case: e["disagreements_above_numerical_zero"] for case, e in c3["direction"].items()
                                    if e["disagreements_above_numerical_zero"]},
        "declared_direction_deviations": c3["declared_deviations"],
    }


# ------------------------------------------------------------------------------------------- all
def run_checks(spec, models, arms, references=None, couplings=()):
    """All checks for a specification. `models`: assembled models (any body and variant; the first gives the
    actuators' frames). `arms`: {(body, variant): (actuator IDs, moment arms actuators x coordinates x samples)}."""
    crossings = derived_crossings(spec, actuator_frames(models[0]))
    c1 = check_c1(spec, crossings)
    c2 = check_c2(spec, crossings, arms, couplings)
    c3 = check_c3(spec, arms, references)
    consumed = {}
    for m in models:
        for name, ids in m.consumed.items():
            consumed.setdefault(name, []).extend(ids)
    c4 = check_c4(spec, consumed)
    req = check_required_edges(spec, crossings)
    mirror = check_mirror(spec.ontology)
    return {"C1_crossings": c1, "C2_leverage": c2, "C3_actions": c3, "C4_evidence": c4,
            "required_edges": req, "mirror": mirror, "C5_deviation_register": deviation_register(spec, c1, c2, c3),
            "passed": all(x["passed"] for x in (c1, c2, c3, c4, req, mirror))}
