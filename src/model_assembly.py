"""A planar model assembled from an executable specification, and its mechanics (D-062 items 3 and 6).

Assembly. Every model segment gets its frames' offsets (from the merged joints' location records), its inertial
parameters by the specification's rule for the body (direct, composite or scaled fraction), and its inbound joint
from the derived tree. Geometry is scaled by the body's geometry scale. Nothing here names a segment, a joint or a
body: the specification and the datasets supply everything (criterion A6).

Frames and signs. All frames of the computational model are parallel in its default pose; motion is a rotation
about the plane normal (z). For a modelled joint with model coordinate theta = sign x q (the ontology's
`model_coordinates`), the segment holding the joint's child frame turns by +theta relative to the segment holding
its parent frame. The joint centre is the child frame's origin, located in the parent frame by the joint's location
record, which may depend on the joint's own coordinate (a moving joint centre).

Mechanics. Two formulations, coded separately:
- Newton-Euler: velocities and accelerations propagated outward from the ground; forces and moments recursed
  inward. A moving joint centre adds the work of the joint force over the relative displacement of its two
  attachment points per unit of its coordinate;
- Kane's method: generalized inertia and gravity forces projected on partial velocities (Jacobians), which also
  give the mass matrix and bias for the forward checks.

The ground segment is fixed; its static equilibrium gives the ground reaction and the centre of pressure.
"""
from dataclasses import dataclass, field
import math

import numpy as np

from .model_spec import SpecError
from .muscles_d2 import Actuator, SimmSpline


# --------------------------------------------------------------------------- functions of a coordinate
class CoordinateFunction:
    """A scaled 3-vector that is constant or a function of a model coordinate theta = sign x q (q: the ontology
    coordinate). Returns value, d/dq and d2/dq2 (3-vectors)."""

    def __init__(self, value, scale, sign=1):
        self.scale, self.sign = float(scale), int(sign)
        if isinstance(value, dict):
            self.splines = []
            for axis in "xyz":
                spec = value[axis]
                if spec["kind"] == "simm_spline":
                    self.splines.append(SimmSpline(spec["x"], spec["y"]))
                elif spec["kind"] == "constant":
                    self.splines.append(float(spec["value"]))
                else:
                    raise SpecError(f"unsupported coordinate function {spec['kind']}")
            self.constant = None
        else:
            self.constant = self.scale * np.asarray(value, float)
            self.splines = None

    @property
    def moves(self):
        return self.splines is not None

    def at(self, q):
        if self.constant is not None:
            z = np.zeros(3)
            return self.constant.copy(), z, z.copy()
        th = self.sign * float(q)
        v, d, dd = [], [], []
        for s in self.splines:
            if isinstance(s, float):
                v.append(s), d.append(0.0), dd.append(0.0)
            else:
                v.append(s.value(th)), d.append(s.derivative(th)), dd.append(s.second_derivative(th))
        sc = self.scale
        return sc * np.array(v), (sc * self.sign) * np.array(d), sc * np.array(dd)


def _rot(phi):
    c, s = math.cos(phi), math.sin(phi)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def _z(w):
    """d/dphi of R(phi) u, in terms of w = R(phi) u."""
    return np.array([-w[1], w[0], 0.0])


def _cross2(a, b):
    return a[0] * b[1] - a[1] * b[0]


# ------------------------------------------------------------------------------------- the model
@dataclass
class Inbound:
    """The modelled joint that connects a segment to the segment nearer the ground."""
    joint: str
    index: int                  # position of the joint's coordinate in q
    turn: int                   # phi_segment = phi_inner + turn x q_index
    inner: str
    inner_point: object         # callable q_index -> (value, d, dd): joint centre in the inner segment's coordinates
    outer_point: object         # same, in this segment's coordinates
    moving: bool


@dataclass
class Segment:
    id: str
    reference_frame: str
    frame_offsets: dict         # frame -> 3-vector in this segment's coordinates (scaled)
    mass: float
    com: np.ndarray             # 2-vector in this segment's coordinates
    inertia: float              # about the centre of mass, rotation in the plane
    share: float
    inbound: Inbound = None
    children: list = field(default_factory=list)
    derivation: str = ""


@dataclass
class Model:
    spec: object
    body: str
    variant: str
    scale: float
    body_mass: float
    stature: float
    segments: dict              # id -> Segment, in tree order (ground first)
    order: list
    coordinates: list
    B: np.ndarray               # segments x coordinates: phi = B q
    contact: dict               # label -> 3-vector in the ground segment's coordinates
    ground_y: float
    support: tuple              # (lowest x, highest x) of the contact points
    actuators: list = field(default_factory=list)
    consumed: dict = field(default_factory=dict)     # dataset file -> observation IDs
    derivations: list = field(default_factory=list)

    @property
    def ground(self):
        return self.order[0]

    @property
    def moving(self):
        return self.order[1:]

    def per_side_mass(self):
        return sum(s.mass for s in self.segments.values())


class _Reader:
    """Reads observation values through the specification and records every ID used."""

    def __init__(self, spec):
        self.spec, self.used = spec, {}

    def record(self, oid):
        role, rec = self.spec.observation(oid)
        self.used.setdefault(self.spec.dataset_files[role], []).append(oid)
        return rec

    def value(self, oid):
        return self.record(oid)["value"]

    def frame_property(self, frame, prop):
        recs = self.spec.schema.observations_for_model_entity(self.spec.datasets["geometry"], frame, prop)
        if len(recs) != 1:
            raise SpecError(f"frame {frame}: {len(recs)} records of {prop}")
        oid = next(iter(recs))
        return self.value(oid)


def _frame_offsets(spec, reader, segment, reference, scale):
    """Offsets (3-vectors) of a segment's frames from its reference frame, through its merged joints."""
    offsets = {reference: np.zeros(3)}
    merged = [j for j in spec.merged_joints() if j.into == segment]
    for j in merged:
        rec = reader.record(j.location_id(spec.variants[0]))
        if rec["value_form"] != "vector":
            raise SpecError(f"merged joint {j.id}: a locked joint needs a constant location")
    changed = True
    while changed:
        changed = False
        for j in merged:
            loc = scale * np.asarray(reader.spec.value(j.location_id(spec.variants[0])), float)
            if j.parent_frame in offsets and j.child_frame not in offsets:
                offsets[j.child_frame] = offsets[j.parent_frame] + loc
                changed = True
            elif j.child_frame in offsets and j.parent_frame not in offsets:
                offsets[j.parent_frame] = offsets[j.child_frame] - loc
                changed = True
    missing = set(spec.frames[segment]) - set(offsets)
    if missing:
        raise SpecError(f"segment {segment}: frames {sorted(missing)} are not connected to {reference}")
    return offsets


def _composite(parts):
    """Parallel-axis assembly; parts are (mass, 2-vector, inertia about own centre of mass)."""
    m = sum(p[0] for p in parts)
    c = sum(p[0] * np.asarray(p[1], float) for p in parts) / m
    inertia = sum(p[2] + p[0] * float((np.asarray(p[1]) - c) @ (np.asarray(p[1]) - c)) for p in parts)
    return m, c, inertia


def _frame_mass_properties(reader, frame, offset):
    m = float(reader.frame_property(frame, "mass"))
    c = np.asarray(reader.frame_property(frame, "center_of_mass_position"), float)[:2] + offset[:2]
    izz = float(reader.frame_property(frame, "inertia_tensor")[2][2])
    return m, c, izz


def _reference_shape(spec, reader, segment, offsets_unscaled):
    """Mass, centre of mass and inertia of a segment in the reference body (scale 1), by its reference rule."""
    ref = next(b for b, s in spec.bodies.items() if s["geometry_scale"] == "reference")
    rule = spec.bodies[ref]["segment_rules"][segment]["rule"]
    frames = spec.frames[segment]
    parts = [_frame_mass_properties(reader, f, offsets_unscaled[f]) for f in frames]
    if rule == "direct":
        return parts[0]
    if rule == "composite":
        return _composite(parts)
    raise SpecError(f"segment {segment}: the reference body's rule must be direct or composite, not {rule}")


def assemble(spec, body, variant):
    """The model for one body and one variant of the specification."""
    if body not in spec.bodies:
        raise SpecError(f"{spec.name}: no body {body!r}")
    if variant not in spec.variants:
        raise SpecError(f"{spec.name}: no variant {variant!r}")
    reader = _Reader(spec)
    bspec = spec.bodies[body]
    ref_body = next(b for b, s in spec.bodies.items() if s["geometry_scale"] == "reference")
    body_mass = float(reader.value(bspec["body_mass"]))
    stature = float(reader.value(bspec["stature"]))
    if bspec["geometry_scale"] == "reference":
        scale = 1.0
    else:
        scale = stature / float(reader.value(spec.bodies[ref_body]["stature"]))
    shares = spec.raw.get("bilateral_share") or {}
    coords = spec.coordinates
    derivations = [f"geometry scale = {scale:.6f}" + ("" if bspec["geometry_scale"] == "reference"
                                                     else f" (stature {stature} / reference stature)")]

    # Reference frame of each segment.
    reference = {spec.ground["segment"]: spec.ground["reference_frame"]}
    for jid, inner, outer in spec.tree:
        j = spec.joints[jid]
        reference[outer] = j.parent_frame if spec.frame_segment[j.parent_frame] == outer else j.child_frame

    segments = {}
    for sid in spec.segments:
        offsets = _frame_offsets(spec, reader, sid, reference[sid], scale)
        unscaled = _frame_offsets(spec, reader, sid, reference[sid], 1.0)
        rule = bspec["segment_rules"][sid]
        kind = rule["rule"]
        if kind == "direct":
            (frame,) = spec.frames[sid]
            m, c, inertia = _frame_mass_properties(reader, frame, offsets[frame])
            how = "direct: the frame's own mass, centre of mass and inertia"
        elif kind == "composite":
            m, c, inertia = _composite([_frame_mass_properties(reader, f, offsets[f]) for f in spec.frames[sid]])
            how = f"composite of {len(spec.frames[sid])} frames, merged joints at zero, parallel-axis theorem"
        else:
            fraction = sum(count * sum(float(reader.value(oid)) for oid in ids)
                           for count, ids in rule["mass_fraction_terms"])
            m = fraction * body_mass
            if "length_to" in rule:
                rec = reader.record(rule["length_to"])
                frame = rec["coordinate_context"]["frame_id"]
                if spec.frame_segment.get(frame) != sid:
                    raise SpecError(f"body {body} segment {sid}: length_to lies in another segment")
                vec = scale * np.asarray(rec["value"], float)[:2]
                length = float(np.hypot(*vec))
                cf = float(reader.value(rule["center_of_mass_fraction"]))
                r = float(reader.value(rule["radius_of_gyration_fraction"])) * length
                c = offsets[frame][:2] + cf * vec
                inertia = m * r * r
                how = (f"scaled fraction: mass {fraction:.6f} x body mass; centre of mass at the fraction "
                       f"{cf} of the {length:.5f} m line from the frame origin; inertia from the radius fraction")
            else:
                m_ref, c_ref, i_ref = _reference_shape(spec, reader, sid, unscaled)
                k = math.sqrt(i_ref / m_ref) * scale
                c = scale * np.asarray(c_ref, float)
                inertia = m * k ** 2
                how = (f"scaled fraction: mass {fraction:.6f} x body mass; centre of mass and radius of gyration "
                       "scaled from the reference body's shape")
        share = float(shares.get(sid, 1.0))
        segments[sid] = Segment(sid, reference[sid], offsets, share * m, np.asarray(c, float), share * inertia,
                                share, derivation=how + (f"; share {share} per side" if share != 1.0 else ""))
        derivations.append(f"{sid}: {segments[sid].derivation}")

    # Inbound joints.
    B = np.zeros((len(spec.segments), len(coords)))
    order = [spec.ground["segment"]]
    for jid, inner, outer in spec.tree:
        j = spec.joints[jid]
        info = spec.coordinate_info[j.coordinate]
        k = coords.index(j.coordinate)
        rec = reader.record(j.location_id(variant))
        sign = info.sign
        if rec["value_form"] == "function":
            driver = rec["coordinate_context"]["coordinate_id"]
            if driver != j.coordinate:
                raise SpecError(f"joint {jid}: its location depends on {driver}, not on its own coordinate")
        loc = CoordinateFunction(rec["value"], scale, sign)
        outer_holds_parent = spec.frame_segment[j.parent_frame] == outer
        turn = -sign if outer_holds_parent else sign

        def point(seg, holds_parent, j=j, loc=loc):
            off_parent = segments[seg].frame_offsets.get(j.parent_frame)
            off_child = segments[seg].frame_offsets.get(j.child_frame)
            if holds_parent:
                return lambda qk: (lambda v: (off_parent + v[0], v[1], v[2]))(loc.at(qk))
            const = off_child.copy()
            return lambda qk: (const.copy(), np.zeros(3), np.zeros(3))
        inbound = Inbound(jid, k, turn, inner, point(inner, not outer_holds_parent), point(outer, outer_holds_parent),
                          loc.moves)
        segments[outer].inbound = inbound
        segments[inner].children.append(outer)
        i_out, i_in = spec.segments.index(outer), spec.segments.index(inner)
        B[i_out] = B[i_in]
        B[i_out, k] += turn
        order.append(outer)
        derivations.append(f"{jid}: coordinate {j.coordinate} ({info.model_coordinate}, sign {sign:+d}); "
                           + ("moving centre" if loc.moves else "fixed centre") + f" from {j.location_id(variant)}")
    B = B[[spec.segments.index(s) for s in order]]

    g = segments[spec.ground["segment"]]
    contact = {label: g.frame_offsets[f].copy() for label, f in spec.ground["contact_points"].items()}
    ground_y = float(contact[spec.ground["ground_line_through"]][1])
    xs = [float(p[0]) for p in contact.values()]
    model = Model(spec, body, variant, scale, body_mass, stature, {s: segments[s] for s in order}, order, list(coords),
                  B, contact, ground_y, (min(xs), max(xs)), consumed=reader.used, derivations=derivations)
    model.actuators = load_actuators(spec, reader, scale)
    return model


# ------------------------------------------------------------------------------------ actuators
@dataclass
class PathPoint:
    frame: str
    segment: str
    kind: str                         # fixed, conditional or moving
    location: np.ndarray = None       # fixed and conditional: scaled 3-vector in the frame
    function: object = None           # moving: CoordinateFunction
    coordinate: int = None            # conditional and moving: index in q
    sign: int = 1
    active_range: tuple = None
    name: str = ""


ACTIVITY_TOL = 1e-5   # rad, OpenSim ConditionalPathPoint::isActive (as src/muscles_d2.py)
PARAMETERS = ("maximum_isometric_force", "optimal_fiber_length", "tendon_slack_length", "pennation_angle_at_optimal",
              "maximum_contraction_velocity")


def load_actuators(spec, reader, scale):
    """The specification's actuators, read through target.model_entity_id, as src/muscles_d2.py Actuators whose
    points are PathPoints. Lengths named in `scaled_actuator_parameters` are scaled by the geometry scale."""
    if not spec.actuators:
        return []
    data = spec.datasets["actuators"]
    scaled = set(spec.raw.get("scaled_actuator_parameters") or [])
    out = []
    for aid in spec.actuators:
        recs = spec.schema.observations_for_model_entity(data, aid)
        params = {}
        for p in PARAMETERS:
            hit = [oid for oid, o in recs.items() if o["property_id"] == p]
            if len(hit) != 1:
                raise SpecError(f"actuator {aid}: {len(hit)} records of {p}")
            params[p] = float(reader.value(hit[0])) * (scale if p in scaled else 1.0)
        name = spec.ontology.model_element(aid)[1]
        act = Actuator(name, spec.ontology.get(aid)["represents"], params["maximum_isometric_force"],
                       params["optimal_fiber_length"], params["tendon_slack_length"],
                       params["pennation_angle_at_optimal"], params["maximum_contraction_velocity"])
        act.id = aid
        for k, (oid, o) in enumerate((oid, o) for oid, o in recs.items() if o["property_id"] == "attachment_position"):
            reader.record(oid)
            frame = o["coordinate_context"]["frame_id"]
            seg = spec.frame_segment.get(frame)
            if seg is None:
                raise SpecError(f"actuator {aid}: path point frame {frame} is not in the model")
            val = o["value"]
            pt = PathPoint(frame, seg, "fixed", name=f"{name}-P{k + 1}")
            if o["value_form"] == "vector":
                pt.location = scale * np.asarray(val, float)
            else:
                cid = o["coordinate_context"]["coordinate_id"]
                if cid not in spec.coordinates:
                    raise SpecError(f"actuator {aid}: point {k + 1} depends on {cid}, which the model does not retain")
                pt.coordinate, pt.sign = spec.coordinates.index(cid), spec.coordinate_info[cid].sign
                if val["kind"] == "conditional":
                    pt.kind, pt.location, pt.active_range = "conditional", scale * np.asarray(val["location"], float), \
                        tuple(val["active_range"])
                elif val["kind"] == "moving":
                    pt.kind, pt.function = "moving", CoordinateFunction(val, scale, pt.sign)
                else:
                    raise SpecError(f"actuator {aid}: unsupported path point kind {val['kind']}")
            act.points.append(pt)
        out.append(act)
    return out


def point_active(pt, q):
    if pt.kind != "conditional":
        return True
    theta = pt.sign * q[pt.coordinate]
    lo, hi = pt.active_range
    return lo - ACTIVITY_TOL <= theta <= hi + ACTIVITY_TOL


# ----------------------------------------------------------------------------- positions, Jacobians
def segment_frames(model, q):
    """Per segment: angle, origin (3-vector), d(origin)/dq (3 x n) and rotation, at one configuration."""
    q = np.asarray(q, float)
    n = len(q)
    phi = model.B @ q
    out = {}
    for i, sid in enumerate(model.order):
        s = model.segments[sid]
        R = _rot(phi[i])
        if s.inbound is None:
            out[sid] = (phi[i], np.zeros(3), np.zeros((3, n)), R)
            continue
        ib = s.inbound
        _, Oi, Ji, Ri = out[ib.inner]
        i_in = model.order.index(ib.inner)
        a_in, da_in, _ = ib.inner_point(q[ib.index])
        a_out, da_out, _ = ib.outer_point(q[ib.index])
        wi, wo = Ri @ a_in, R @ a_out
        O = Oi + wi - wo
        J = Ji + np.outer(_z(wi), model.B[i_in]) - np.outer(_z(wo), model.B[i])
        J[:, ib.index] += Ri @ da_in - R @ da_out
        out[sid] = (phi[i], O, J, R)
    return out


def point_in_world(model, frames, segment, local):
    """Position and d/dq (3 x n) of a point fixed in a segment, given in its coordinates (3-vector)."""
    phi, O, J, R = frames[segment]
    w = R @ local
    return O + w, J + np.outer(_z(w), model.B[model.order.index(segment)])



# ------------------------------------------------------------------------- Newton-Euler (propagation)
def kinematics(model, q, qd, qdd):
    """Propagated outward from the ground: per segment, origin position, velocity and acceleration (2 x n), angle,
    angular velocity and acceleration, centre of mass position, velocity, acceleration, and inbound joint centre."""
    q, qd, qdd = (np.atleast_2d(np.asarray(x, float)) for x in (q, qd, qdd))
    n = q.shape[1]
    phi, w, al = model.B @ q, model.B @ qd, model.B @ qdd
    out = {sid: {k: np.zeros((2, n)) for k in ("o", "vo", "ao", "c", "vc", "ac", "joint")} for sid in model.order}
    for i in range(n):
        state = {}
        for r, sid in enumerate(model.order):
            s = model.segments[sid]
            R = _rot(phi[r, i])
            if s.inbound is None:
                o = vo = ao = np.zeros(3)
                joint = np.zeros(3)
            else:
                ib = s.inbound
                ri = model.order.index(ib.inner)
                oi, voi, aoi, Ri = state[ib.inner]
                qk, qkd, qkdd = q[ib.index, i], qd[ib.index, i], qdd[ib.index, i]
                terms = []
                for Rm, row, pt, sgn in ((Ri, ri, ib.inner_point, 1.0), (R, r, ib.outer_point, -1.0)):
                    a, da, dda = pt(qk)
                    p, dp, ddp = Rm @ a, Rm @ da, Rm @ dda
                    om, alpha = w[row, i], al[row, i]
                    terms.append((sgn * p, sgn * (om * _z(p) + dp * qkd),
                                  sgn * (alpha * _z(p) - om * om * p + 2 * om * qkd * _z(dp) + ddp * qkd * qkd
                                         + dp * qkdd)))
                o = oi + terms[0][0] + terms[1][0]
                vo = voi + terms[0][1] + terms[1][1]
                ao = aoi + terms[0][2] + terms[1][2]
                joint = oi + terms[0][0]
            state[sid] = (o, vo, ao, R)
            c = R @ np.r_[s.com, 0.0]
            vals = {"o": o, "vo": vo, "ao": ao, "joint": joint, "c": o + c, "vc": vo + w[r, i] * _z(c),
                    "ac": ao + al[r, i] * _z(c) - w[r, i] ** 2 * c}
            for key, v in vals.items():
                out[sid][key][:, i] = v[:2]
    out["_phi"], out["_omega"], out["_alpha"] = phi, w, al
    return out


def inverse_dynamics(model, q, qd, qdd, gravity):
    """Newton-Euler recursion inward. Returns generalized forces (coordinates x n), the ground reaction (2 x n), the
    centre of pressure x, joint forces and couples on each segment from its inner neighbour, and the moving-centre
    terms."""
    q, qd, qdd = (np.atleast_2d(np.asarray(x, float)) for x in (q, qd, qdd))
    n = q.shape[1]
    k = kinematics(model, q, qd, qdd)
    gvec = np.array([0.0, -gravity])[:, None]
    force, couple = {}, {}
    tau = np.zeros((len(model.coordinates), n))
    trans = {}
    for sid in reversed(model.moving):
        s = model.segments[sid]
        r = model.order.index(sid)
        c, a = k[sid]["c"], k[sid]["ac"]
        p_low = k[sid]["joint"]
        f = s.mass * (a - gvec)
        m = s.inertia * k["_alpha"][r]
        for ch in s.children:
            f = f + force[ch]
            m = m + couple[ch] + _cross2(k[ch]["joint"] - c, force[ch])
        m = m - _cross2(p_low - c, f)
        force[sid], couple[sid] = f, m
        ib = s.inbound
        t = np.zeros(n)
        if ib.moving:
            ri = model.order.index(ib.inner)
            for i in range(n):
                _, da_in, _ = ib.inner_point(q[ib.index, i])
                _, da_out, _ = ib.outer_point(q[ib.index, i])
                disp = _rot(k["_phi"][ri, i]) @ da_in - _rot(k["_phi"][r, i]) @ da_out
                t[i] = f[:, i] @ disp[:2]
        trans[ib.joint] = t
        tau[ib.index] = ib.turn * m + t
    g = model.segments[model.ground]
    grf = -g.mass * gvec + sum(force[ch] for ch in g.children)
    moment = sum(couple[ch] + _cross2(k[ch]["joint"], force[ch]) for ch in g.children)
    h = -model.ground_y
    with np.errstate(divide="ignore", invalid="ignore"):
        cop = (moment + g.mass * gravity * g.com[0] - h * grf[0]) / grf[1]
    return {"tau": tau, "grf": grf, "cop_x": cop, "joint_forces": force, "joint_couples": couple,
            "moving_centre_terms": trans, "kinematics": k}


# ----------------------------------------------------------------------------------- Kane's method
def _com_jacobians(model, q):
    """Per moving segment: centre-of-mass position (3), Jacobian (3 x n) and bias acceleration as a function of qdot,
    built from second derivatives of the segment-origin chain."""
    q = np.asarray(q, float)
    n = len(q)
    out = {}
    chain = {}
    for r, sid in enumerate(model.order):
        s = model.segments[sid]
        R = _rot(model.B[r] @ q)
        if s.inbound is None:
            chain[sid] = (np.zeros(3), np.zeros((3, n)), [], R)
            continue
        ib = s.inbound
        ri = model.order.index(ib.inner)
        Oi, Ji, bias_i, Ri = chain[ib.inner]
        parts = list(bias_i)
        O, J = Oi.copy(), Ji.copy()
        for Rm, row, pt, sgn in ((Ri, ri, ib.inner_point, 1.0), (R, r, ib.outer_point, -1.0)):
            a, da, dda = pt(q[ib.index])
            p, dp, ddp = sgn * (Rm @ a), sgn * (Rm @ da), sgn * (Rm @ dda)
            O = O + p
            J = J + np.outer(_z(p), model.B[row])
            J[:, ib.index] += dp
            parts.append((p, dp, ddp, model.B[row], ib.index))
        chain[sid] = (O, J, parts, R)
        c = R @ np.r_[s.com, 0.0]
        Jc = J + np.outer(_z(c), model.B[r])
        out[sid] = (O + c, Jc, parts + [(c, np.zeros(3), np.zeros(3), model.B[r], None)])

    def bias(parts, qd):
        acc = np.zeros(3)
        for p, dp, ddp, Brow, idx in parts:
            om = Brow @ qd
            acc += -om * om * p
            if idx is not None:
                acc += 2 * om * qd[idx] * _z(dp) + ddp * qd[idx] * qd[idx]
        return acc
    return {sid: (p, J, (lambda qd, parts=parts: bias(parts, qd))) for sid, (p, J, parts) in out.items()}


def kane(model, q, qd, qdd, gravity):
    """Generalized forces by Kane's method; also the mass matrix M and bias h (tau = M qdd + h)."""
    q, qd, qdd = (np.atleast_2d(np.asarray(x, float)) for x in (q, qd, qdd))
    nq, n = q.shape
    tau, Ms, hs = np.zeros((nq, n)), np.zeros((n, nq, nq)), np.zeros((nq, n))
    g = np.array([0.0, -gravity, 0.0])
    for i in range(n):
        M, h = np.zeros((nq, nq)), np.zeros(nq)
        for sid, (p, J, quad) in _com_jacobians(model, q[:, i]).items():
            s = model.segments[sid]
            Jw = model.B[model.order.index(sid)]
            M += s.mass * J.T @ J + s.inertia * np.outer(Jw, Jw)
            h += s.mass * J.T @ (quad(qd[:, i]) - g)
        Ms[i], hs[:, i] = M, h
        tau[:, i] = M @ qdd[:, i] + h
    return {"tau": tau, "M": Ms, "h": hs}


def potential(model, q, gravity):
    return sum(model.segments[sid].mass * gravity * p[1] for sid, (p, _, _) in
               _com_jacobians(model, np.asarray(q, float)).items())


def kinetic(model, q, qd):
    M = kane(model, q[:, None], qd[:, None], np.zeros((len(q), 1)), 0.0)["M"][0]
    return 0.5 * qd @ M @ qd


def _d5(f, h):
    return (-f(2 * h) + 8 * f(h) - 8 * f(-h) + f(-2 * h)) / (12 * h)


def static_torques(model, q, gravity, h=1e-3):
    """Held still, the generalized force balances gravity: tau = dV/dq (virtual work), by fourth-order differences."""
    q = np.asarray(q, float)
    return np.array([_d5(lambda s, e=e: potential(model, q + s * e, gravity), h) for e in np.eye(len(q))])


def forward_accel(model, q, qd, tau, gravity):
    k = kane(model, q[:, None], qd[:, None], np.zeros((len(q), 1)), gravity)
    return np.linalg.solve(k["M"][0], tau - k["h"][:, 0])


# ------------------------------------------------------------------------------- motion and checks
@dataclass
class Motion:
    """Each coordinate goes from `start` to `depth` and back: q = start + (depth - start)(1 - cos(2 pi t / T)) / 2."""
    start: np.ndarray
    depth: np.ndarray
    period: float

    def __call__(self, t):
        t = np.asarray(t, float)
        w = 2 * math.pi / self.period
        amp = (np.asarray(self.depth, float) - np.asarray(self.start, float))[:, None] / 2
        q = np.asarray(self.start, float)[:, None] + amp * (1 - np.cos(w * t))
        return q, amp * w * np.sin(w * t), amp * w * w * np.cos(w * t)


def _rk4(rhs, t, y, step):
    k1 = rhs(t, y)
    k2 = rhs(t + step / 2, y + step / 2 * k1)
    k3 = rhs(t + step / 2, y + step / 2 * k2)
    k4 = rhs(t + step, y + step * k3)
    return y + step / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


def _driven_rhs(model, motion, gravity):
    nq = len(model.coordinates)

    def rhs(t, y):
        qq, qqd, qqdd = motion(np.array([t]))
        tau = inverse_dynamics(model, qq, qqd, qqdd, gravity)["tau"][:, 0]
        return np.concatenate([y[nq:], forward_accel(model, y[:nq], y[nq:], tau, gravity)])
    return rhs


def _exact(motion, t):
    q, qd, _ = motion(np.array([t]))
    return np.concatenate([q[:, 0], qd[:, 0]])


def local_step_error(model, motion, gravity, step, starts=30):
    """One RK4 step of Kane's equations driven by the Newton-Euler forces, from exact states."""
    rhs, nq, err = _driven_rhs(model, motion, gravity), len(model.coordinates), 0.0
    for t in np.linspace(0.0, motion.period - step, starts):
        y = _rk4(rhs, t, _exact(motion, t), step)
        err = max(err, float(np.max(np.abs(y[:nq] - _exact(motion, t + step)[:nq]))))
    return err


def short_horizon_error(model, motion, gravity, step, horizon=0.1, starts=6):
    rhs, nq, err = _driven_rhs(model, motion, gravity), len(model.coordinates), 0.0
    steps = int(round(horizon / step))
    for t0 in np.linspace(0.0, motion.period - horizon, starts):
        y, t = _exact(motion, t0), t0
        for _ in range(steps):
            y = _rk4(rhs, t, y, step)
            t += step
            err = max(err, float(np.max(np.abs(y[:nq] - _exact(motion, t)[:nq]))))
    return err


def run(model, params):
    """The prescribed motion: generalized forces, ground reaction, centre of pressure and contact checks."""
    motion = Motion(params["start_angles"], params["depth_angles"], params["period"])
    t = np.linspace(0.0, params["period"], int(params["samples"]))
    q, qd, qdd = motion(t)
    g = params["gravity"]
    lo, hi = model.support
    if not hi > lo:
        raise SpecError("the contact points must span a positive support length")
    res = inverse_dynamics(model, q, qd, qdd, g)
    grf, cop = res["grf"], res["cop_x"]
    in_contact = grf[1] > 0
    cop = np.where(in_contact & np.isfinite(cop), cop, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        friction = np.where(in_contact, np.abs(grf[0]) / grf[1], np.inf)
    outside = ~np.isfinite(cop) | (cop < lo) | (cop > hi)
    finite = cop[np.isfinite(cop)]
    contact = {
        "normal_force_min_N": float(np.min(grf[1])), "lift_off_samples": int(np.sum(~in_contact)),
        "cop_min_m": float(np.min(finite)) if finite.size else None,
        "cop_max_m": float(np.max(finite)) if finite.size else None,
        "support_min_m": float(lo), "support_max_m": float(hi),
        "support_margin_min_m": float(min(np.min(finite) - lo, hi - np.max(finite))) if finite.size else None,
        "cop_outside_support_samples": int(np.sum(outside)),
        "required_friction_max": float(np.max(friction)) if np.all(np.isfinite(friction)) else None,
        "friction_coefficient_assumed": params["friction_coefficient"],
        "friction_exceeded_samples": int(np.sum(friction > params["friction_coefficient"])),
    }
    contact["feasible"] = (contact["lift_off_samples"] == 0 and contact["cop_outside_support_samples"] == 0
                           and contact["friction_exceeded_samples"] == 0)
    return {"t": t, "q": q, "qd": qd, "qdd": qdd, "tau": res["tau"], "grf": grf, "cop_x": cop,
            "kinematics": res["kinematics"], "moving_centre_terms": res["moving_centre_terms"],
            "contact": contact, "motion": motion}


def check_residuals(model, params, result, energy_dt=1e-3, static_every=30):
    """Residual of each mechanics check (D-062 A3; the D1-D3 set): Newton-Euler against Kane, virtual work, energy,
    the Newton identity, one-step and short-horizon forward reproduction, and mass bookkeeping."""
    g = params["gravity"]
    q, qd, qdd, tau = result["q"], result["qd"], result["qdd"], result["tau"]
    kn = kane(model, q, qd, qdd, g)
    motion, t = result["motion"], result["t"]
    nq = len(model.coordinates)

    def E(shift):
        qq, qqd, _ = motion(t + shift)
        return np.array([kinetic(model, qq[:, i], qqd[:, i]) + potential(model, qq[:, i], g) for i in range(qq.shape[1])])
    dEdt = _d5(E, energy_dt)
    k = result["kinematics"]
    per_side = model.segments[model.ground].mass * g + sum(model.segments[s].mass * (g + k[s]["ac"][1])
                                                          for s in model.moving)
    sides = 2 if model.spec.raw.get("bilateral_share") else 1
    zero = np.zeros((nq, 1))
    static = max(float(np.max(np.abs(inverse_dynamics(model, qq[:, None], zero, zero, g)["tau"][:, 0]
                                     - static_torques(model, qq, g)))) for qq in q[:, ::static_every].T)
    return {
        "newton_euler_vs_kane_N_m": float(np.max(np.abs(tau - kn["tau"]))),
        "static_virtual_work_N_m": static,
        "energy_W": float(np.max(np.abs(np.sum(tau * qd, axis=0) - dEdt))),
        "newton_identity_per_side_N": float(np.max(np.abs(result["grf"][1] - per_side))),
        "local_one_step_rad_at_1ms": local_step_error(model, motion, g, 0.001),
        "short_horizon_0p1s_rad_at_1ms": short_horizon_error(model, motion, g, 0.001),
        "mass_bookkeeping_relative": float(sides * model.per_side_mass() / model.body_mass - 1),
    }
