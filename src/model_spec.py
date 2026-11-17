"""Executable model specifications stated in the ontology (Stage D4, D-062 items 1-4 and Amendment 1).

A specification lives in an ontology module's `models` block with `kind: executable_specification`. It names
segments, modelled and merged joints, coordinates, actuators, variants and per-body parameter rules. This module
reads it, checks every reference against the ontology and the datasets, and derives what the specification does
not restate:

- each joint's two segments, from CONNECTS endpoints resolved by the endpoint rule (D-062 Amendment 1, D062-B03);
- the parts and frames of each model segment, from merged joints and frame PART_OF;
- the segment tree, rooted at the ground segment, from the modelled joints.

Generic by design: no ontology IDs and no anatomical terms appear in this file (D-062 item 6, criterion A6).
"""
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

from .ontology import AnatomyOntology
from .quantitative import QuantitativeSchema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = ROOT / "ontology" / "quantitative_schema.yaml"
DATA = ROOT / "ontology" / "quantitative_data"

KIND = "executable_specification"
SEGMENT_CLASS, FRAME_CLASS, COMPLEX_CLASS = "RigidBodySegment", "CoordinateFrame", "SkeletalComplex"
COORDINATE_CLASS, ACTUATOR_CLASS = "JointCoordinate", "ModelActuator"
RULES = ("direct", "composite", "scaled_fraction")
SCALES = ("reference", "stature_ratio_to_reference")
EXTENDING_FIELDS = {"kind", "extends", "decision", "description", "add_actuators", "expected_direction_deviations"}
LUMPED = "lumped"   # represented_scope of an actuator that represents several muscles (D-063 item 5)
DEVIATION_FIELDS = {"actuator", "coordinate", "variants", "drives", "basis"}


def represented(onto, actuator):
    """The muscles an actuator represents, as a list: one entity, or several for a lumped actuator (D-063 item 5)."""
    rep = onto.get(actuator).get("represents")
    return list(rep) if isinstance(rep, list) else [rep]


class SpecError(ValueError):
    """A specification that cannot be assembled; the message names the offending element."""


# ---------------------------------------------------------------------------- endpoint rule
def resolve_endpoint(onto, eid):
    """The one segment a CONNECTS endpoint resolves to (D-062 Amendment 1):

    1. an endpoint that is itself a segment is that segment;
    2. otherwise its own REPRESENTED_BY segment;
    3. if it has none, the REPRESENTED_BY segment of the skeletal complex that has it as a direct HAS_PART and has a
       representation.

    Zero or several candidates at the step that applies raise SpecError naming the endpoint.
    """
    e = onto.get(eid)
    if e.get("class") == SEGMENT_CLASS:
        return eid
    own = [t for t in onto.related(eid, "REPRESENTED_BY") if onto.get(t).get("class") == SEGMENT_CLASS]
    if own:
        if len(own) > 1:
            raise SpecError(f"endpoint {eid} is ambiguous: represented by {own}")
        return own[0]
    candidates = []
    for cid, c in onto.entities.items():
        if c.get("class") == COMPLEX_CLASS and eid in onto.related(cid, "HAS_PART"):
            reps = [t for t in onto.related(cid, "REPRESENTED_BY") if onto.get(t).get("class") == SEGMENT_CLASS]
            candidates += reps
    if not candidates:
        raise SpecError(f"endpoint {eid} is unresolved: no segment represents it or a complex containing it")
    if len(set(candidates)) > 1:
        raise SpecError(f"endpoint {eid} is ambiguous: containing complexes are represented by {sorted(set(candidates))}")
    return candidates[0]


def joint_endpoints(onto, joint):
    """(segment, segment) of a joint's CONNECTS endpoints, or None when the ontology states no endpoints."""
    ends = onto.related(joint, "CONNECTS")
    if not ends:
        return None
    if len(ends) != 2:
        raise SpecError(f"joint {joint} CONNECTS {len(ends)} entities; two are required")
    return tuple(resolve_endpoint(onto, e) for e in ends)


# ----------------------------------------------------------------------------- data classes
@dataclass
class Joint:
    id: str
    modelled: bool
    location: object              # observation ID, or {variant: observation ID}
    child_frame: str
    parent_frame: str             # frame of the location record (coordinate_context.frame_id)
    endpoints: tuple = None       # resolved segments, or None if the ontology states none
    coordinate: str = None        # modelled joints
    into: str = None              # merged joints
    segments: tuple = None        # (model segment holding parent_frame, model segment holding child_frame)

    def location_id(self, variant):
        if isinstance(self.location, dict):
            if variant not in self.location:
                raise SpecError(f"joint {self.id} has no location for variant {variant!r}")
            return self.location[variant]
        return self.location


@dataclass
class Coordinate:
    id: str
    joint: str
    model_coordinate: str
    sign: int
    positive_motion: str
    negative_motion: str


@dataclass
class ModelSpec:
    name: str
    raw: dict
    ontology: AnatomyOntology
    schema: QuantitativeSchema
    datasets: dict                          # role -> loaded dataset
    dataset_files: dict                     # role -> file name
    segments: list                          # model segments, ground first, then outward along the tree
    parts: dict                             # model segment -> ontology segments merged into it
    frames: dict                            # model segment -> frames
    frame_segment: dict                     # frame -> model segment
    joints: dict                            # joint ID -> Joint (modelled and merged)
    tree: list                              # [(joint, inner segment, outer segment)], ground outward
    coordinates: list                       # retained coordinate IDs, specification order
    coordinate_info: dict                   # coordinate ID -> Coordinate
    actuators: list
    variants: list
    bodies: dict
    endpoint_log: list = field(default_factory=list)

    @property
    def ground(self):
        return self.raw["ground"]

    @property
    def model(self):
        return self.raw["computational_model"]

    def observation(self, oid):
        """(role, record) of an observation in one of the specification's datasets."""
        hits = [(role, d["observations"][oid]) for role, d in self.datasets.items() if oid in d["observations"]]
        if len(hits) != 1:
            raise SpecError(f"observation {oid} found in {len(hits)} of the specification's datasets")
        return hits[0]

    def value(self, oid):
        return self.observation(oid)[1]["value"]

    def modelled_joints(self):
        return [self.joints[j] for j, _, _ in self.tree]

    def merged_joints(self):
        return [j for j in self.joints.values() if not j.modelled]


# --------------------------------------------------------------------------------- loading
def default_ontology():
    """The ontology modules the quantitative schema names (its `ontology` field), loaded together."""
    return AnatomyOntology(QuantitativeSchema(SCHEMA_FILE, ontology=False).ontology_paths())


def default_schema(ontology=None):
    return QuantitativeSchema(SCHEMA_FILE, ontology=ontology)


def raw_specification(onto, name):
    """The specification's fields, with `extends` resolved: a specification that extends another adds actuators and
    may restate its decision and description; it changes nothing else (D-062 item 8)."""
    models = onto.data["models"]
    if name not in models:
        raise SpecError(f"no model specification {name!r}")
    raw = deepcopy(models[name])
    if raw.get("kind") != KIND:
        raise SpecError(f"{name} is not an {KIND}")
    if "extends" not in raw:
        return raw
    extra = set(raw) - EXTENDING_FIELDS
    if extra:
        raise SpecError(f"{name}: a specification that extends another may only add actuators; unsupported fields {sorted(extra)}")
    base = raw_specification(onto, raw["extends"])     # recursive: any depth of `extends`
    base["expected_direction_deviations"] = (list(base.get("expected_direction_deviations") or [])
                                             + list(raw.get("expected_direction_deviations") or []))
    added = list(raw.get("add_actuators") or [])
    clash = set(added) & set(base["actuators"])
    if clash:
        raise SpecError(f"{name}: actuators {sorted(clash)} are already in {raw['extends']}")
    base["actuators"] = list(base["actuators"]) + added
    base["extends"] = raw["extends"]
    for key in ("decision", "description"):
        if key in raw:
            base[key] = raw[key]
    return base


def load_spec(name, ontology=None, schema=None):
    """Read, check and derive a specification. Raises SpecError listing what is wrong."""
    onto = ontology or default_ontology()
    schema = schema or default_schema(onto)
    raw = raw_specification(onto, name)
    errors = []

    def need(cond, message):
        if not cond:
            errors.append(message)
        return cond

    def entity(eid, cls, what):
        ok = need(eid in onto.entities, f"{what} {eid} does not exist in the ontology")
        if ok and cls:
            ok = need(onto.get(eid).get("class") == cls, f"{what} {eid} has class {onto.get(eid).get('class')}, not {cls}")
        return ok

    for key in ("computational_model", "datasets", "segments", "ground", "variants", "modelled_joints",
                "merged_joints", "retained_coordinates", "actuators", "bodies"):
        need(key in raw, f"{name}: missing field {key}")
    if errors:
        raise SpecError("\n".join(errors))

    files = dict(raw["datasets"])
    datasets = {role: schema.load_dataset(DATA / f) for role, f in files.items()}

    def obs(oid, what):
        hits = [r for r, d in datasets.items() if oid in d["observations"]]
        need(len(hits) == 1, f"{what}: observation {oid} found in {len(hits)} datasets")
        return datasets[hits[0]]["observations"][oid] if len(hits) == 1 else None

    segments = list(raw["segments"])
    for s in segments:
        entity(s, SEGMENT_CLASS, "segment")
    variants = list(raw["variants"])
    need(bool(variants), f"{name}: at least one variant is required")

    # Joints: endpoints by the rule, location records, frames.
    joints = {}
    log = []
    for kind, block in (("modelled", raw["modelled_joints"]), ("merged", raw["merged_joints"])):
        for jid, j in block.items():
            if not entity(jid, None, f"{kind} joint"):
                continue
            locs = j.get("location")
            loc_ids = list(locs.values()) if isinstance(locs, dict) else [locs]
            if isinstance(locs, dict):
                need(set(locs) <= set(variants), f"joint {jid}: location variants {sorted(set(locs) - set(variants))} "
                                                 "are not declared")
            parents = set()
            for oid in loc_ids:
                rec = obs(oid, f"joint {jid} location")
                if rec is not None:
                    parents.add((rec.get("coordinate_context") or {}).get("frame_id"))
            need(len(parents) == 1, f"joint {jid}: its location records must share one frame, found {sorted(map(str, parents))}")
            parent = parents.pop() if len(parents) == 1 else None
            child = j.get("child_frame")
            entity(child, FRAME_CLASS, f"joint {jid} child frame")
            if parent:
                entity(parent, FRAME_CLASS, f"joint {jid} location frame")
            try:
                ends = joint_endpoints(onto, jid)
            except SpecError as exc:
                errors.append(str(exc))
                ends = None
                if kind == "modelled":
                    continue
            log.append({"joint": jid, "endpoints": list(ends) if ends else None,
                        "note": None if ends else "merged; endpoints not stated in the ontology"})
            joints[jid] = Joint(jid, kind == "modelled", locs, child, parent, ends,
                                coordinate=j.get("coordinate"), into=j.get("into"))
            if kind == "modelled":
                need(ends is not None, f"modelled joint {jid} states no endpoints in the ontology")
            else:
                need(j.get("into") in segments, f"merged joint {jid}: into {j.get('into')} is not a model segment")

    # Parts of each model segment: itself plus the endpoints of the joints merged into it.
    parts = {s: [s] for s in segments}
    for j in joints.values():
        if not j.modelled and j.into in parts and j.endpoints:
            for e in j.endpoints:
                if e not in parts[j.into]:
                    parts[j.into].append(e)
    owner = {}
    for s, ps in parts.items():
        for p in ps:
            need(p not in owner or owner[p] == s, f"segment {p} is merged into both {owner.get(p)} and {s}")
            owner[p] = s
    for j in joints.values():
        if not j.modelled and j.endpoints:
            for e in j.endpoints:
                need(owner.get(e) == j.into, f"merged joint {j.id}: endpoint {e} does not lie in {j.into}")
                need(e == j.into or e not in segments, f"merged joint {j.id}: endpoint {e} is itself a model segment")

    # Frames: the computational model's frames (model_element) that are PART_OF one of a model segment's parts.
    frames, frame_segment = {s: [] for s in segments}, {}
    for fid, f in onto.entities.items():
        if f.get("class") != FRAME_CLASS or (f.get("model_element") or {}).get("model") != raw["computational_model"]:
            continue
        for target in onto.related(fid, "PART_OF"):
            if target in owner:
                frames[owner[target]].append(fid)
                frame_segment[fid] = owner[target]
    for s in segments:
        need(bool(frames[s]), f"model segment {s} has no frames")

    # Modelled joints: two distinct model segments; frames on the matching sides.
    for j in joints.values():
        if j.modelled and j.endpoints:
            segs = tuple(owner.get(e) for e in j.endpoints)
            if not need(None not in segs, f"modelled joint {j.id}: endpoints {j.endpoints} are not in the model"):
                continue
            need(segs[0] != segs[1], f"modelled joint {j.id} resolves to one segment {segs[0]}; two are required")
            sides = (frame_segment.get(j.parent_frame), frame_segment.get(j.child_frame))
            need(set(sides) == set(segs), f"modelled joint {j.id}: frames lie in {sides}, endpoints in {segs}")
            j.segments = sides
        elif not j.modelled:
            sides = (frame_segment.get(j.parent_frame), frame_segment.get(j.child_frame))
            need(sides == (j.into, j.into), f"merged joint {j.id}: frames lie in {sides}, not both in {j.into}")
            j.segments = sides

    # Frames inside each model segment must form one tree through the merged joints.
    for s in segments:
        inner = [j for j in joints.values() if not j.modelled and j.into == s]
        children = [j.child_frame for j in inner]
        roots = [f for f in frames[s] if f not in children]
        need(len(roots) == 1, f"model segment {s}: frames {frames[s]} need one root, found {roots}")
        need(len(set(children)) == len(children), f"model segment {s}: a frame is the child of two merged joints")

    # Ground and the segment tree.
    ground = raw["ground"]
    need(ground.get("segment") in segments, f"ground segment {ground.get('segment')} is not a model segment")
    need(ground.get("reference_frame") in frames.get(ground.get("segment"), []),
         f"ground reference frame {ground.get('reference_frame')} is not in the ground segment")
    for label, fid in (ground.get("contact_points") or {}).items():
        need(fid in frames.get(ground.get("segment"), []), f"contact point {label}: frame {fid} is not in the ground segment")
    need(ground.get("ground_line_through") in (ground.get("contact_points") or {}),
         "ground_line_through must name a contact point")
    tree, reached, frontier = [], [ground.get("segment")], [ground.get("segment")]
    modelled = [j for j in joints.values() if j.modelled and j.segments]
    while frontier:
        cur = frontier.pop(0)
        for j in modelled:
            if cur in j.segments:
                other = j.segments[1] if j.segments[0] == cur else j.segments[0]
                if other not in reached:
                    tree.append((j.id, cur, other))
                    reached.append(other)
                    frontier.append(other)
    need(set(reached) == set(segments), f"segments {sorted(set(segments) - set(reached))} are not reached from the ground")
    need(len(tree) == len(modelled), "the modelled joints do not form a tree (a loop or a duplicate joint)")

    # Coordinates.
    coords = list(raw["retained_coordinates"])
    info = {}
    joint_coord = {j.coordinate: j.id for j in joints.values() if j.modelled}
    need(set(coords) == set(joint_coord), f"retained coordinates {coords} must be exactly the modelled joints' "
                                          f"coordinates {sorted(joint_coord)}")
    for c in coords:
        if not entity(c, COORDINATE_CLASS, "coordinate"):
            continue
        e = onto.get(c)
        need(joint_coord.get(c) in onto.related(c, "PART_OF"), f"coordinate {c} is not PART_OF {joint_coord.get(c)}")
        try:
            mc, sign = onto.model_coordinate(c, raw["computational_model"])
        except KeyError as exc:
            errors.append(str(exc))
            continue
        need(bool(e.get("positive_motion")) and bool(e.get("negative_motion")),
             f"coordinate {c} needs positive_motion and negative_motion")
        info[c] = Coordinate(c, joint_coord.get(c), mc, sign, e.get("positive_motion"), e.get("negative_motion"))
    for c in raw.get("omitted_coordinates") or []:
        entity(c, COORDINATE_CLASS, "omitted coordinate")
        need(c not in coords, f"coordinate {c} is both retained and omitted")

    # Actuators: entities, model elements, records found through target.model_entity_id.
    actuators = list(raw["actuators"])
    need(len(set(actuators)) == len(actuators), f"{name}: an actuator is listed twice")
    for a in actuators:
        if not entity(a, ACTUATOR_CLASS, "actuator"):
            continue
        try:
            model, _ = onto.model_element(a)
            need(model == raw["computational_model"], f"actuator {a} belongs to model {model}")
        except KeyError as exc:
            errors.append(str(exc))
        rep, scope = onto.get(a).get("represents"), onto.get(a).get("represented_scope")
        if isinstance(rep, list):
            need(scope == LUMPED and len(rep) > 1 and len(set(rep)) == len(rep),
                 f"actuator {a}: a list in represents needs represented_scope {LUMPED!r} and two or more distinct entities")
        else:
            need(scope != LUMPED, f"actuator {a}: represented_scope {LUMPED!r} needs a list of represented entities")
        for m in represented(onto, a):
            need(m in onto.entities, f"actuator {a} represents no known entity ({m})")
        if "actuators" in datasets:
            recs = schema.observations_for_model_entity(datasets["actuators"], a)
            need(bool(recs), f"actuator {a} has no records with target.model_entity_id in {files['actuators']}")

    # Expected direction deviations (D-063 Amendment 1): declared, each with a basis, checked by C3 against a reference.
    deviations = list(raw.get("expected_direction_deviations") or [])
    motions = {m: c for c, i in info.items() for m in (i.positive_motion, i.negative_motion)}
    seen = set()
    for d in deviations:
        if not need(isinstance(d, dict) and set(d) == DEVIATION_FIELDS,
                    f"an expected direction deviation needs exactly {sorted(DEVIATION_FIELDS)}: {d}"):
            continue
        need(d["actuator"] in actuators, f"expected deviation: {d['actuator']} is not an actuator of {name}")
        need(d["coordinate"] in coords, f"expected deviation: {d['coordinate']} is not a retained coordinate")
        need(motions.get(d["drives"]) == d["coordinate"],
             f"expected deviation: {d['drives']} is not a motion of {d['coordinate']}")
        need(isinstance(d["variants"], list) and bool(d["variants"]) and set(d["variants"]) <= set(raw["variants"]),
             f"expected deviation: variants {d['variants']} must be variants of {name}")
        need(isinstance(d["basis"], str) and len(d["basis"].strip()) >= 20,
             f"expected deviation {d['actuator']} {d['coordinate']}: a basis (source or model basis) is required")
        for v in d.get("variants") or []:
            key = (d["actuator"], d["coordinate"], v, d["drives"])   # an actuator may disagree both ways at different poses
            need(key not in seen, f"expected deviation declared twice: {key}")
            seen.add(key)

    # Per-segment share (bilateral symmetry).
    for s, share in (raw.get("bilateral_share") or {}).items():
        need(s in segments and isinstance(share, (int, float)) and 0 < share <= 1,
             f"bilateral_share {s}: {share} must be in (0, 1] for a model segment")

    # Bodies and their rules.
    bodies = raw["bodies"]
    refs = [b for b, spec in bodies.items() if spec.get("geometry_scale") == "reference"]
    need(len(refs) == 1, f"{name}: exactly one body must be the geometry reference, found {refs}")
    for b, spec in bodies.items():
        need(spec.get("geometry_scale") in SCALES, f"body {b}: geometry_scale must be one of {SCALES}")
        for key in ("body_mass", "stature"):
            obs(spec.get(key), f"body {b} {key}")
        rules = spec.get("segment_rules") or {}
        need(set(rules) == set(segments), f"body {b}: rules for {sorted(rules)}, segments {sorted(segments)}")
        for s, r in rules.items():
            rule = r.get("rule")
            if not need(rule in RULES, f"body {b} segment {s}: rule {rule!r} is not one of {RULES}"):
                continue
            n_frames = len(frames.get(s, []))
            if rule == "direct":
                need(n_frames == 1, f"body {b} segment {s}: direct needs one frame, the segment has {n_frames}")
            if rule == "scaled_fraction":
                need(spec.get("geometry_scale") != "reference", f"body {b}: the reference body cannot use scaled_fraction")
                terms = r.get("mass_fraction_terms") or []
                need(bool(terms), f"body {b} segment {s}: mass_fraction_terms required")
                for term in terms:
                    ok = isinstance(term, list) and len(term) == 2 and isinstance(term[0], int) and term[0] > 0
                    if need(ok, f"body {b} segment {s}: a mass-fraction term is [count, [observation, ...]]"):
                        for oid in term[1]:
                            obs(oid, f"body {b} segment {s} mass fraction")
                has_length = "length_to" in r
                need(has_length != (r.get("shape") == "scaled_reference"),
                     f"body {b} segment {s}: give either length_to (with centre-of-mass and radius fractions) or "
                     "shape: scaled_reference")
                if has_length:
                    for key in ("center_of_mass_fraction", "radius_of_gyration_fraction", "length_to"):
                        obs(r.get(key), f"body {b} segment {s} {key}")
    if errors:
        raise SpecError(f"{name}:\n" + "\n".join(errors))
    order = [ground["segment"]] + [outer for _, _, outer in tree]
    return ModelSpec(name, raw, onto, schema, datasets, files, order, parts, frames, frame_segment, joints, tree,
                     coords, info, actuators, variants, bodies, log)


def executable_specifications(onto):
    return [n for n, m in onto.data["models"].items() if m.get("kind") == KIND]
