"""Stage D1: planar inverse-dynamics squat (D-058, Amendments 1 and 2).

Model. Sagittal plane, one leg carrying half of the head-arms-trunk (HAT): a foot
fixed flat on the ground, then shank, thigh and half-HAT linked by revolute ankle,
knee and hip joints with fixed centres. The motion is prescribed (a demonstration);
inverse dynamics returns the joint torques, the ground reaction force and the centre
of pressure that the motion needs. Nothing here is validated against measured squats;
the checks verify that the idealized mechanics are solved correctly (Amendment 1, A3).

Frames and signs. All geometry is in Gait2392 body frames: x anterior, y superior,
z to the right, with angles positive counter-clockwise about z (seen from the right).
Generalized coordinates q = (ankle, knee, hip), in radians, zero in the Gait2392
default pose:
    ankle  dorsiflexion positive   phi_shank = -q_ankle
    knee   flexion positive        phi_thigh = phi_shank + q_knee
    hip    flexion positive        phi_hat   = phi_thigh - q_hip
where phi is the absolute angle of each segment frame (the foot does not rotate).
A joint torque tau_j is the generalized force conjugate to q_j: positive tau_j acts
to increase q_j, and joint power is tau_j * qdot_j.

Bodies. 'gait2392' is the OpenSim Gait2392 model as published. 'female' and 'male'
take segment masses, centre-of-mass fractions and radii of gyration from de Leva
(1996), with joint positions, foot points and the HAT geometry scaled from Gait2392
by stature (Amendment 2). Every number comes from the two segment datasets or the
configuration; this module adds none.
"""
from dataclasses import dataclass, field
from functools import lru_cache
import math
from pathlib import Path

import numpy as np
import sympy as sp
import yaml

from .input_gate import require_traceable
from .quantitative import QuantitativeSchema

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "ontology" / "quantitative_data"
G2392 = "segments_gait2392.yaml"
DELEVA = "segments_de_leva_1996.yaml"
JOINTS = ("ankle", "knee", "hip")
MOVING = ("shank", "thigh", "hat")


# ----------------------------------------------------------------------------- body
@dataclass
class Segment:
    """A moving segment in a frame whose origin is its LOWER joint (closer to the ground)."""
    mass: float          # kg (for the HAT: half of it, per leg)
    inertia: float       # kg m^2 about the centre of mass, rotation in the sagittal plane
    com: np.ndarray      # centre of mass, m
    upper: np.ndarray    # next joint up (knee for the shank, hip for the thigh); zeros for the HAT


@dataclass
class Foot:
    mass: float
    com: np.ndarray      # relative to the ankle centre, m
    heel: np.ndarray     # heel ground point relative to the ankle
    ball: np.ndarray     # ball of the foot (metatarsophalangeal joint) relative to the ankle
    ground_y: float      # height of the ground relative to the ankle (negative)


@dataclass
class Body:
    name: str
    body_mass: float
    stature: float
    foot: Foot
    segments: dict       # shank, thigh, hat -> Segment
    whole_hat_mass: float
    derivations: list = field(default_factory=list)   # how every number was obtained
    consumed: dict = field(default_factory=dict)       # dataset file -> observation IDs used

    def per_leg_mass(self):
        return self.foot.mass + sum(s.mass for s in self.segments.values())


def _rot(phi):
    c, s = math.cos(phi), math.sin(phi)
    return np.array([[c, -s], [s, c]])


def _load(schema, name):
    return schema.load_dataset(DATA / name)


def _val(dataset, oid, consumed):
    consumed.append(oid)
    return dataset["observations"][oid]["value"]


def _xy(v):
    return np.array([float(v[0]), float(v[1])])


def _zz(tensor):
    return float(tensor[2][2])


def gait2392_geometry(schema):
    """Per-leg Gait2392 quantities in metres and kilograms, with the IDs they came from."""
    d = _load(schema, G2392)
    used = []
    v = lambda oid: _val(d, oid, used)  # noqa: E731
    g = {}
    for body in ("FEMUR_R", "TIBIA_R", "TALUS_R", "CALCN_R", "TOES_R", "PELVIS", "TORSO"):
        g[body] = {"m": v(f"LB-QD:G2392:{body}:MASS"), "c": _xy(v(f"LB-QD:G2392:{body}:COM")),
                   "I": _zz(v(f"LB-QD:G2392:{body}:INERTIA"))}
    for j in ("HIP_R", "KNEE_R", "ANKLE_R", "SUBTALAR_R", "MTP_R", "BACK"):
        g[j] = _xy(v(f"LB-QD:G2392:JOINT:{j}"))
    g["body_mass"] = v("LB-QD:G2392:BODY_MASS")
    g["stature"] = v("LB-QD:G2392:STATURE")
    # HAT = pelvis + torso with the low-back joint locked at zero, relative to the hip centre.
    hip = g["HIP_R"]
    parts = [(g["PELVIS"]["m"], g["PELVIS"]["c"] - hip, g["PELVIS"]["I"]),
             (g["TORSO"]["m"], g["BACK"] + g["TORSO"]["c"] - hip, g["TORSO"]["I"])]
    m = sum(p[0] for p in parts)
    c = sum(p[0] * p[1] for p in parts) / m
    inertia = sum(p[2] + p[0] * float((p[1] - c) @ (p[1] - c)) for p in parts)
    g["HAT"] = {"m": m, "c": c, "I": inertia}
    # Foot points relative to the ankle (talus origin): heel = calcaneus origin, ball = MTP joint.
    s, mtp = g["SUBTALAR_R"], g["MTP_R"]
    foot_parts = [(g["TALUS_R"]["m"], g["TALUS_R"]["c"]), (g["CALCN_R"]["m"], s + g["CALCN_R"]["c"]),
                  (g["TOES_R"]["m"], s + mtp + g["TOES_R"]["c"])]
    fm = sum(p[0] for p in foot_parts)
    g["FOOT"] = {"m": fm, "c": sum(p[0] * p[1] for p in foot_parts) / fm, "heel": s, "ball": s + mtp}
    return g, used


def assemble_hat(parts):
    """Parallel-axis assembly: parts are (mass, com 2-vector, inertia about own com)."""
    m = sum(p[0] for p in parts)
    c = sum(p[0] * np.asarray(p[1], float) for p in parts) / m
    inertia = sum(p[2] + p[0] * float((np.asarray(p[1]) - c) @ (np.asarray(p[1]) - c)) for p in parts)
    return m, c, inertia


def build_body(name, schema=None):
    """Return the per-leg Body for 'gait2392', 'female' or 'male'."""
    schema = schema or QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    g, g_used = gait2392_geometry(schema)
    knee, ankle = g["KNEE_R"], g["ANKLE_R"]
    if name == "gait2392":
        thigh = Segment(g["FEMUR_R"]["m"], g["FEMUR_R"]["I"], g["FEMUR_R"]["c"] - knee, -knee)
        shank = Segment(g["TIBIA_R"]["m"], g["TIBIA_R"]["I"], g["TIBIA_R"]["c"] - ankle, -ankle)
        hat = Segment(g["HAT"]["m"] / 2, g["HAT"]["I"] / 2, g["HAT"]["c"], np.zeros(2))
        f = g["FOOT"]
        foot = Foot(f["m"], f["c"], f["heel"], f["ball"], float(f["heel"][1]))
        body = Body(name, g["body_mass"], g["stature"], foot,
                    {"shank": shank, "thigh": thigh, "hat": hat}, g["HAT"]["m"],
                    consumed={G2392: g_used})
        body.derivations = [
            "Gait2392 as published: masses, centres of mass and Izz from the model file",
            "HAT = pelvis + torso, low-back joint locked at zero; parallel-axis theorem",
            "per leg: half the HAT mass and inertia (bilateral symmetry)",
            "knee centre fixed at its knee-angle-zero location",
            "heel = calcaneus origin, ball = MTP joint, ground through the heel point (demonstration assumptions)"]
        return body
    if name not in ("female", "male"):
        raise ValueError(f"unknown body {name!r}; use 'female', 'male' or 'gait2392'")
    d = _load(schema, DELEVA)
    used = []
    S = name[0].upper()
    v = lambda oid: _val(d, oid, used)  # noqa: E731
    mass, stature = v(f"LB-QD:DELEVA:{S}:BODY_MASS"), v(f"LB-QD:DELEVA:{S}:STATURE")
    scale = stature / g["stature"]
    frac = lambda seg, prop: v(f"LB-QD:DELEVA:{S}:{seg}:{prop}")  # noqa: E731

    def limb(seg, distal):
        """Segment from its proximal joint (origin) to `distal`, re-expressed from the distal joint."""
        vec = scale * distal                       # proximal -> distal joint, scaled
        length = float(np.hypot(*vec))
        m = frac(seg, "MASS_FRACTION") * mass
        c = frac(seg, "CENTER_OF_MASS_FRACTION")  # from the proximal endpoint
        r = frac(seg, "RADIUS_OF_GYRATION_FRACTION") * length
        return Segment(m, m * r * r, c * vec - vec, -vec), length

    thigh, l_thigh = limb("THIGH", knee)
    shank, l_shank = limb("SHANK", ankle)
    hat_fraction = (frac("HEAD", "MASS_FRACTION") + frac("TRUNK", "MASS_FRACTION")
                    + 2 * (frac("UPPER_ARM", "MASS_FRACTION") + frac("FOREARM", "MASS_FRACTION")
                           + frac("HAND", "MASS_FRACTION")))
    hat_mass = hat_fraction * mass
    k_hat = math.sqrt(g["HAT"]["I"] / g["HAT"]["m"]) * scale
    hat = Segment(hat_mass / 2, hat_mass / 2 * k_hat ** 2, scale * g["HAT"]["c"], np.zeros(2))
    f = g["FOOT"]
    foot = Foot(frac("FOOT", "MASS_FRACTION") * mass, scale * f["c"], scale * f["heel"], scale * f["ball"],
                float(scale * f["heel"][1]))
    body = Body(name, mass, stature, foot, {"shank": shank, "thigh": thigh, "hat": hat}, hat_mass,
                consumed={G2392: g_used, DELEVA: used})
    body.derivations = [
        f"scale = stature / Gait2392 stature = {stature} / {g['stature']} = {scale:.6f}",
        "segment mass = de Leva mass fraction x body mass",
        f"thigh: HJC->KJC vector = scale x Gait2392 knee location (length {l_thigh:.5f} m); "
        "COM at de Leva fraction from the hip; I = m (radius fraction x length)^2",
        f"shank: KJC->AJC vector = scale x Gait2392 ankle location (length {l_shank:.5f} m); "
        "COM at de Leva fraction from the knee; I = m (radius fraction x length)^2",
        f"HAT mass = (head + trunk + 2 x (upper arm + forearm + hand)) fractions x body mass = {hat_fraction:.4f} x M",
        "HAT centre of mass = scale x Gait2392 HAT centre of mass; HAT radius of gyration = scale x Gait2392 value "
        "(assumption: the de Leva bodies share Gait2392's HAT shape)",
        "foot mass = de Leva foot fraction x body mass; foot points and centre of mass = scale x Gait2392 foot",
        "per leg: half the HAT (bilateral symmetry)"]
    return body


def traceability(body, schema=None):
    """Run the D-055 C4 gate on every observation the body consumed; raise on failure."""
    schema = schema or QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    reports = {}
    for name, ids in body.consumed.items():
        reports[name] = require_traceable(schema, _load(schema, name), sorted(set(ids)))
    return reports


# --------------------------------------------------------------------------- motion
@dataclass
class Motion:
    """Each joint goes from `start` to `depth` and back: q = start + (depth - start)(1 - cos(2 pi t / T)) / 2."""
    start: np.ndarray
    depth: np.ndarray
    period: float

    def __call__(self, t):
        t = np.asarray(t, float)
        w = 2 * math.pi / self.period
        amp = (self.depth - self.start)[:, None] / 2
        q = self.start[:, None] + amp * (1 - np.cos(w * t))
        qd = amp * w * np.sin(w * t)
        qdd = amp * w * w * np.cos(w * t)
        return q, qd, qdd


def absolute_angles(q):
    q = np.asarray(q, float)
    shank = -q[0]
    thigh = shank + q[1]
    hat = thigh - q[2]
    return np.array([shank, thigh, hat])


B_MAP = np.array([[-1.0, 0.0, 0.0], [-1.0, 1.0, 0.0], [-1.0, 1.0, -1.0]])  # phi = B q


# ------------------------------------------------------------ Newton-Euler (numeric)
def _perp(v):
    return np.stack([-v[1], v[0]])


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def kinematics(body, q, qd, qdd):
    """Positions, velocities and accelerations of joints and centres of mass (arrays of shape 2 x n)."""
    phi, w, al = B_MAP @ q, B_MAP @ qd, B_MAP @ qdd
    n = q.shape[1]
    out = {"ankle": (np.zeros((2, n)), np.zeros((2, n)), np.zeros((2, n)))}
    base = "ankle"
    for i, name in enumerate(MOVING):
        seg = body.segments[name]
        o, vo, ao = out[base]
        rot = np.stack([np.stack([np.cos(phi[i]), -np.sin(phi[i])]), np.stack([np.sin(phi[i]), np.cos(phi[i])])])
        for point, key in ((seg.com, f"com_{name}"), (seg.upper, f"top_{name}")):
            rp = np.einsum("ijn,j->in", rot, point)
            out[key] = (o + rp, vo + w[i] * _perp(rp), ao + al[i] * _perp(rp) - w[i] ** 2 * rp)
        base = f"top_{name}"
    out["knee"], out["hip"] = out["top_shank"], out["top_thigh"]
    out["phi"], out["omega"], out["alpha"] = phi, w, al
    return out


def inverse_dynamics(body, q, qd, qdd, gravity):
    """Recursive Newton-Euler from the HAT down. Returns joint torques and contact quantities."""
    q, qd, qdd = (np.atleast_2d(np.asarray(x, float)) for x in (q, qd, qdd))
    if q.shape[0] != 3:
        q, qd, qdd = q.T, qd.T, qdd.T
    k = kinematics(body, q, qd, qdd)
    gvec = np.array([0.0, -gravity])[:, None]
    lower = {"shank": "ankle", "thigh": "knee", "hat": "hip"}
    force_above, moment_above, point_above = np.zeros((2, q.shape[1])), np.zeros(q.shape[1]), None
    moments, forces = {}, {}
    for i, name in reversed(list(enumerate(MOVING))):
        seg = body.segments[name]
        c, _, a = k[f"com_{name}"]
        p_low = k[lower[name]][0]
        # Force on this segment at its lower joint, from the segment below.
        f = seg.mass * (a - gvec) + force_above
        # Moment on this segment at its lower joint, from the segment below (z, counter-clockwise).
        m = seg.inertia * k["alpha"][i] + moment_above - _cross(p_low - c, f)
        if point_above is not None:
            m = m + _cross(point_above - c, force_above)
        moments[lower[name]], forces[lower[name]] = m, f
        force_above, moment_above, point_above = f, m, p_low
    # Joint torques from moments (power: sum M_j (omega_upper - omega_lower) = sum tau_j qdot_j).
    tau = np.stack([-moments["ankle"], moments["knee"], -moments["hip"]])
    # Foot: fixed, in static equilibrium. Ground force and centre of pressure.
    foot = body.foot
    grf = forces["ankle"] - foot.mass * gvec
    h = -foot.ground_y
    with np.errstate(divide="ignore", invalid="ignore"):
        cop = (moments["ankle"] + foot.mass * gravity * foot.com[0] - h * grf[0]) / grf[1]
    return {"tau": tau, "grf": grf, "cop_x": cop, "joint_forces": forces, "joint_moments": moments,
            "kinematics": k}


# -------------------------------------------------------- Lagrange (symbolic, independent)
@lru_cache(maxsize=None)
def _lagrange_functions():
    """Equations of motion from kinetic and potential energy, with parameters symbolic.

    Built only from segment positions and energies, without free-body diagrams, so it
    is an independent check on inverse_dynamics (Amendment 1, A3).
    """
    t = sp.symbols("t")
    qs = [sp.Function(f"q{i}")(t) for i in range(3)]
    g = sp.symbols("g")
    par = {}
    for name in MOVING:
        par[name] = dict(zip(("m", "I", "cx", "cy", "ux", "uy"), sp.symbols(f"{name}_m {name}_I {name}_cx {name}_cy {name}_ux {name}_uy")))
    phis = [-qs[0], -qs[0] + qs[1], -qs[0] + qs[1] - qs[2]]
    rot = lambda a: sp.Matrix([[sp.cos(a), -sp.sin(a)], [sp.sin(a), sp.cos(a)]])  # noqa: E731
    origin = sp.Matrix([0, 0])
    T = V = 0
    for name, phi in zip(MOVING, phis):
        p = par[name]
        R = rot(phi)
        com = origin + R * sp.Matrix([p["cx"], p["cy"]])
        vel = com.diff(t)
        T += sp.Rational(1, 2) * p["m"] * (vel.dot(vel)) + sp.Rational(1, 2) * p["I"] * phi.diff(t) ** 2
        V += p["m"] * g * com[1]
        origin = origin + R * sp.Matrix([p["ux"], p["uy"]])
    L = T - V
    qv, qdv, qddv = sp.symbols("qa qk qh"), sp.symbols("qda qdk qdh"), sp.symbols("qdda qddk qddh")
    def plain(expr):  # replace q''(t), then q'(t), then q(t) by plain symbols, in that order
        expr = expr.subs({qs[i].diff(t, 2): qddv[i] for i in range(3)})
        expr = expr.subs({qs[i].diff(t): qdv[i] for i in range(3)})
        return expr.subs({qs[i]: qv[i] for i in range(3)})

    Q = [sp.expand(plain(L.diff(qs[i].diff(t)).diff(t) - L.diff(qs[i]))) for i in range(3)]
    E = plain(T + V)
    dEdt = sum(E.diff(qv[i]) * qdv[i] + E.diff(qdv[i]) * qddv[i] for i in range(3))
    M = sp.Matrix(3, 3, lambda i, j: sp.diff(Q[i], qddv[j]))
    h = [Q[i].subs({qddv[0]: 0, qddv[1]: 0, qddv[2]: 0}) for i in range(3)]
    params = [par[n][k] for n in MOVING for k in ("m", "I", "cx", "cy", "ux", "uy")] + [g]
    args = list(qv) + list(qdv) + list(qddv) + params
    return {"Q": sp.lambdify(args, Q, "numpy"), "M": sp.lambdify(list(qv) + params, M, "numpy"),
            "h": sp.lambdify(list(qv) + list(qdv) + params, h, "numpy"),
            "E": sp.lambdify(list(qv) + list(qdv) + params, E, "numpy"),
            "dEdt": sp.lambdify(args, dEdt, "numpy")}


def _params(body, gravity):
    out = []
    for name in MOVING:
        s = body.segments[name]
        out += [s.mass, s.inertia, s.com[0], s.com[1], s.upper[0], s.upper[1]]
    return out + [gravity]


def lagrange_torques(body, q, qd, qdd, gravity):
    f = _lagrange_functions()["Q"]
    return np.array([np.broadcast_to(x, np.shape(q[0])) for x in f(*q, *qd, *qdd, *_params(body, gravity))])


def energy(body, q, qd, gravity):
    return _lagrange_functions()["E"](*q, *qd, *_params(body, gravity))


def energy_rate(body, q, qd, qdd, gravity):
    return _lagrange_functions()["dEdt"](*q, *qd, *qdd, *_params(body, gravity))


def forward_step_accel(body, q, qd, tau, gravity):
    f = _lagrange_functions()
    p = _params(body, gravity)
    M = np.array(f["M"](*q, *p), float)
    h = np.array(f["h"](*q, *qd, *p), float)
    return np.linalg.solve(M, tau - h)


# ----------------------------------------------------------------- independent oracles
def static_torques(body, q, gravity):
    """Gravity moments computed directly: tau = sum m g (x_com - x_joint), with each joint's sign.

    Held still, the joint torque must balance the weight of everything above the joint.
    Increasing q_hip alone tilts the HAT forward about the hip, and increasing q_ankle tilts
    shank, thigh and HAT forward about the ankle, so a centre of mass in front of those
    joints needs a negative (extension / plantarflexion) torque. Increasing q_knee tilts
    thigh and HAT backward about the knee, so a centre of mass behind the knee needs a
    negative (extension) torque. Hence the signs -1, +1, -1.
    """
    q = np.asarray(q, float).reshape(3, 1)
    k = kinematics(body, q, np.zeros_like(q), np.zeros_like(q))
    x = lambda key: k[key][0][0, 0]  # noqa: E731
    m = {n: body.segments[n].mass for n in MOVING}
    above = {"hip": ["hat"], "knee": ["thigh", "hat"], "ankle": ["shank", "thigh", "hat"]}
    sign = {"ankle": -1.0, "knee": 1.0, "hip": -1.0}
    out = []
    for j in JOINTS:
        moment = sum(m[n] * gravity * (x(f"com_{n}") - x(j)) for n in above[j])
        out.append(sign[j] * moment)
    return np.array(out)


def rk4_round_trip(body, motion, gravity, step, starts=60):
    """One-step round trip: Newton-Euler torques drive the Lagrange equations forward.

    From the exact state at `starts` times spread over the motion, take one RK4 step of
    the Lagrange equations driven by the Newton-Euler torques, and return the largest
    joint-angle error against the exact motion at the end of the step. A correct pair
    of formulations gives an error of order step^5 (about 32 times smaller per halving).

    A single integration over the whole squat is not used: an upright chain driven
    open-loop is unstable, so rounding errors grow exponentially (time constant of
    order 0.2 s) and swamp the comparison. That growth is real dynamics, not a fault.
    """
    def torque(t):
        q, qd, qdd = motion(np.array([t]))
        return inverse_dynamics(body, q, qd, qdd, gravity)["tau"][:, 0]

    def rhs(t, y):
        return np.concatenate([y[3:], forward_step_accel(body, y[:3], y[3:], torque(t), gravity)])

    err = 0.0
    for t in np.linspace(0.0, motion.period - step, starts):
        q0, qd0, _ = motion(np.array([t]))
        y = np.concatenate([q0[:, 0], qd0[:, 0]])
        k1 = rhs(t, y)
        k2 = rhs(t + step / 2, y + step / 2 * k1)
        k3 = rhs(t + step / 2, y + step / 2 * k2)
        k4 = rhs(t + step, y + step * k3)
        y = y + step / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        q_true, _, _ = motion(np.array([t + step]))
        err = max(err, float(np.max(np.abs(y[:3] - q_true[:, 0]))))
    return err


# ---------------------------------------------------------------------- config / run
def load_config(path):
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    required = {"model_id", "decision", "bodies", "parameters", "assumptions", "omitted_physics", "tolerances"}
    if not isinstance(cfg, dict) or set(cfg) != required:
        raise ValueError("configuration fields must be exactly: " + ", ".join(sorted(required)))
    params = {}
    for name, item in cfg["parameters"].items():
        if not isinstance(item, dict) or set(item) != {"value", "unit", "kind", "rationale"}:
            raise ValueError(f"{name}: needs value, unit, kind and rationale")
        if item["kind"] not in ("demonstration_assumption", "defined_constant"):
            raise ValueError(f"{name}: kind must be demonstration_assumption or defined_constant")
        if not str(item["rationale"]).strip():
            raise ValueError(f"{name}: rationale required")
        value = item["value"]
        values = value if isinstance(value, list) else [value]
        if not values or any(type(x) not in (int, float) or not math.isfinite(x) for x in values):
            raise ValueError(f"{name}: finite numbers required")
        params[name] = np.array(values, float) if isinstance(value, list) else float(value)
    for name in ("gravity", "period", "samples", "friction_coefficient"):
        if name not in params or params[name] <= 0:
            raise ValueError(f"{name} must be present and positive")
    for name in ("start_angles", "depth_angles"):
        if name not in params or np.shape(params[name]) != (3,):
            raise ValueError(f"{name} must list three angles (ankle, knee, hip)")
    if int(params["samples"]) != params["samples"] or params["samples"] < 3:
        raise ValueError("samples must be an integer of at least 3")
    if any(b not in ("female", "male", "gait2392") for b in cfg["bodies"]):
        raise ValueError("bodies must be female, male or gait2392")
    return cfg, params


def run(body, params):
    """Run the prescribed squat for one body; return time series and contact checks."""
    motion = Motion(params["start_angles"], params["depth_angles"], params["period"])
    t = np.linspace(0.0, params["period"], int(params["samples"]))
    q, qd, qdd = motion(t)
    g = params["gravity"]
    res = inverse_dynamics(body, q, qd, qdd, g)
    grf, cop = res["grf"], res["cop_x"]
    foot = body.foot
    with np.errstate(divide="ignore", invalid="ignore"):
        friction = np.abs(grf[0]) / grf[1]
    k = res["kinematics"]
    contact = {
        "normal_force_min_N": float(np.min(grf[1])),
        "lift_off_samples": int(np.sum(grf[1] < 0)),
        "cop_min_m": float(np.min(cop)), "cop_max_m": float(np.max(cop)),
        "support_heel_m": float(foot.heel[0]), "support_ball_m": float(foot.ball[0]),
        "cop_outside_support_samples": int(np.sum((cop < foot.heel[0]) | (cop > foot.ball[0]))),
        "required_friction_max": float(np.nanmax(friction)),
        "friction_coefficient_assumed": params["friction_coefficient"],
        "friction_exceeded_samples": int(np.sum(friction > params["friction_coefficient"])),
    }
    contact["feasible"] = (contact["lift_off_samples"] == 0 and contact["cop_outside_support_samples"] == 0
                           and contact["friction_exceeded_samples"] == 0)
    return {"t": t, "q": q, "qd": qd, "qdd": qdd, "tau": res["tau"], "grf": grf, "cop_x": cop,
            "points": {key: k[key][0] for key in ("knee", "hip", "com_shank", "com_thigh", "com_hat")},
            "phi": k["phi"], "contact": contact, "motion": motion}


def whole_body_com(body, k):
    """Whole-body centre of mass x, y and acceleration from both legs plus the full HAT."""
    legs = [(body.segments[n].mass, k[f"com_{n}"]) for n in ("shank", "thigh")]
    hat = body.segments["hat"]
    zero = np.zeros_like(k["com_shank"][0])
    foot = (body.foot.mass, (body.foot.com[:, None] + zero, zero, zero))
    parts = [(2 * m, v) for m, v in legs] + [(2 * hat.mass, k["com_hat"]), (2 * foot[0], foot[1])]
    m = sum(p[0] for p in parts)
    pos = sum(p[0] * p[1][0] for p in parts) / m
    acc = sum(p[0] * p[1][2] for p in parts) / m
    return m, pos, acc
