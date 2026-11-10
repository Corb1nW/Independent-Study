"""Stage D2: muscle forces for the D1 squat (D-059 with Amendments 1 and 2).

Pipeline, at each sample of a D1 run and for one body:

1. Geometry (item 6). The 14 Gait2392 actuators' path points are placed on D1's
   planar chain: foot fixed, shank, thigh and HAT rotating about z at fixed joint
   centres. Musculotendon length L is the sum of distances between consecutive
   ACTIVE points; moment arm R_j = -dL/dq_j (positive R increases q_j when the
   muscle pulls); dL/dt = -sum_j R_j qdot_j, from the active-point set at that sample.
   Conditional points use OpenSim's inclusive rule (range widened by 1e-5 rad), so L
   jumps at a switch (Amendment 2); nothing here differences L across samples.
2. Force law (item 5, Amendment 1). De Groote et al. 2016 curves with constants read
   from the vendored OpenSim header; rigid tendon, constant thickness, single cos(alpha)
   projection, fiber velocity v_M = cos(alpha) dL/dt (lengthening positive),
   normalized by v_max * l_opt. Baseline: no passive force, damping 0. Outside the
   curve domain an actuator is excluded at that sample and flagged, never extrapolated.
3. Recruitment (items 1 and 3, Amendment 2). Stage 1: the smallest largest per-joint
   reserve t* (linear program). Stage 2: minimum sum of squared activations with every
   |reserve| <= t* + delta. muscle_feasibility is feasible when t* <= epsilon_reserve.

Frames and signs follow src/squat_d1.py: q = (ankle dorsiflexion, knee flexion, hip
flexion), positive torques increase q. Gait2392's knee angle is -q_knee.
"""
from dataclasses import dataclass, field
import math
from pathlib import Path
import re

import numpy as np
from scipy.optimize import linprog

from .input_gate import require_traceable
from .quantitative import QuantitativeSchema
from .squat_d1 import B_MAP, gait2392_geometry

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "ontology" / "quantitative_data"
MUSCLES = "muscles_gait2392.yaml"
HEADER = ROOT / "sources" / "vendor" / "opensim-core" / "DeGrooteFregly2016Muscle.h"
ACTIVITY_TOL = 1e-5  # rad; OpenSim ConditionalPathPoint::isActive at opensim-core 01683ac
FRAMES = {"LB:FRAME:GAIT2392_PELVIS": "pelvis", "LB:FRAME:GAIT2392_FEMUR_R": "femur",
          "LB:FRAME:GAIT2392_TIBIA_R": "tibia", "LB:FRAME:GAIT2392_CALCN_R": "calcn"}


# ------------------------------------------------------------------ curve constants
def header_constants(path=HEADER):
    """The `constexpr static double` constants of the vendored De Groote header, by name."""
    text = Path(path).read_text(encoding="utf-8")
    return {k: float(v) for k, v in re.findall(r"constexpr static double\s+(\w+)\s*=\s*([-+\d.eE]+)\s*;", text)}


C = header_constants()
MIN_NORM_FIBER_LENGTH = C["m_minNormFiberLength"]   # 0.2
MAX_NORM_FIBER_LENGTH = C["m_maxNormFiberLength"]   # 1.8
VELOCITY_DOMAIN = (-1.0, 1.0)                        # header: calcForceVelocityMultiplier domain


def f_active(l_norm):
    """Active force-length multiplier (header calcActiveForceLengthMultiplier) with active-force width scale 1,
    the baseline value set explicitly in D-059 Amendment 1."""
    total = 0.0
    for i in (1, 2, 3):
        b1, b2, b3, b4 = (C[f"b{j}{i}"] for j in (1, 2, 3, 4))
        x = (l_norm - b2) / (b3 + b4 * l_norm)
        total = total + b1 * np.exp(-0.5 * x * x)
    return total


def f_velocity(v_norm):
    """Force-velocity multiplier (header calcForceVelocityMultiplier); domain [-1, 1]."""
    t = C["d2"] * v_norm + C["d3"]
    return C["d1"] * np.log(t + np.sqrt(t * t + 1.0)) + C["d4"]


def f_passive(l_norm, strain=0.6):
    """Passive force-length multiplier (header calcPassiveForceMultiplier); used only in a sensitivity case."""
    k = C["kPE"]
    offset = math.exp(k * (MIN_NORM_FIBER_LENGTH - 1.0) / strain)
    return (np.exp(k * (l_norm - 1.0) / strain) - offset) / (math.exp(k) - offset)


# ------------------------------------------------------------------- SimmSpline port
class SimmSpline:
    """OpenSim's SimmSpline (opensim-core 01683ac, OpenSim/Common/SimmSpline.cpp), ported line by line.

    Cubic spline whose end conditions take the third derivative from divided
    differences (not a natural spline); linear extrapolation outside the knots.
    """
    TINY, ROUNDOFF = 1e-7, 2e-13

    def __init__(self, x, y):
        x, y = list(map(float, x)), list(map(float, y))
        n = len(x)
        self.x, self.y = x, y
        b, c, d = [0.0] * n, [0.0] * n, [0.0] * n
        tiny = self.TINY
        if n == 2:
            t = max(tiny, x[1] - x[0])
            b[0] = b[1] = (y[1] - y[0]) / t
            self.b, self.c, self.d = b, c, d
            return
        nm1, nm2 = n - 1, n - 2
        d[0] = max(tiny, x[1] - x[0])
        c[1] = (y[1] - y[0]) / d[0]
        for i in range(1, nm1):
            d[i] = max(tiny, x[i + 1] - x[i])
            b[i] = 2.0 * (d[i - 1] + d[i])
            c[i + 1] = (y[i + 1] - y[i]) / d[i]
            c[i] = c[i + 1] - c[i]
        b[0], b[nm1] = -d[0], -d[nm2]
        c[0] = c[nm1] = 0.0
        if n > 3:
            d31 = max(tiny, x[3] - x[1]); d20 = max(tiny, x[2] - x[0])
            d1 = max(tiny, x[nm1] - x[n - 3]); d2 = max(tiny, x[nm2] - x[n - 4])
            d30 = max(tiny, x[3] - x[0]); d3 = max(tiny, x[nm1] - x[n - 4])
            c[0] = c[2] / d31 - c[1] / d20
            c[nm1] = c[nm2] / d1 - c[n - 3] / d2
            c[0] = c[0] * d[0] * d[0] / d30
            c[nm1] = -c[nm1] * d[nm2] * d[nm2] / d3
        for i in range(1, n):
            t = d[i - 1] / b[i - 1]
            b[i] -= t * d[i - 1]
            c[i] -= t * c[i - 1]
        c[nm1] /= b[nm1]
        for j in range(nm1):
            i = nm2 - j
            c[i] = (c[i] - d[i] * c[i + 1]) / b[i]
        b[nm1] = (y[nm1] - y[nm2]) / d[nm2] + d[nm2] * (c[nm2] + 2.0 * c[nm1])
        for i in range(nm1):
            b[i] = (y[i + 1] - y[i]) / d[i] - d[i] * (c[i + 1] + 2.0 * c[i])
            d[i] = (c[i + 1] - c[i]) / d[i]
            c[i] *= 3.0
        c[nm1] *= 3.0
        d[nm1] = d[nm2]
        self.b, self.c, self.d = b, c, d

    def _segment(self, a):
        x, n = self.x, len(self.x)
        if n < 3:
            return 0
        i, j = 0, n
        while True:
            k = (i + j) // 2
            if a < x[k]:
                j = k
            elif a > x[k + 1]:
                i = k
            else:
                return k

    def value(self, a):
        x, y, n = self.x, self.y, len(self.x)
        if a < x[0]:
            return y[0] + (a - x[0]) * self.b[0]
        if a > x[n - 1]:
            return y[n - 1] + (a - x[n - 1]) * self.b[n - 1]
        if abs(a - x[0]) <= self.ROUNDOFF:
            return y[0]
        if abs(a - x[n - 1]) <= self.ROUNDOFF:
            return y[n - 1]
        k = self._segment(a)
        dx = a - x[k]
        return y[k] + dx * (self.b[k] + dx * (self.c[k] + dx * self.d[k]))

    def derivative(self, a):
        x, n = self.x, len(self.x)
        if a < x[0]:
            return self.b[0]
        if a > x[n - 1]:
            return self.b[n - 1]
        if abs(a - x[0]) <= self.ROUNDOFF:
            return self.b[0]
        if abs(a - x[n - 1]) <= self.ROUNDOFF:
            return self.b[n - 1]
        k = self._segment(a)
        dx = a - x[k]
        return self.b[k] + dx * (2.0 * self.c[k] + 3.0 * dx * self.d[k])


def _coordinate_function(spec):
    if spec["kind"] == "simm_spline":
        s = SimmSpline(spec["x"], spec["y"])
        return s.value, s.derivative
    if spec["kind"] == "constant":
        v = float(spec["value"])
        return (lambda a: v), (lambda a: 0.0)
    raise ValueError(f"unsupported coordinate function {spec['kind']}")


# ----------------------------------------------------------------------- actuators
@dataclass
class PathPoint:
    frame: str                      # pelvis, femur, tibia or calcn
    kind: str                       # fixed, conditional or moving
    location: np.ndarray = None     # fixed and conditional points, scaled, m
    active_range: tuple = None      # conditional: Gait2392 knee-angle range, rad
    funcs: tuple = None             # moving: ((value, derivative) for x, y, z), unscaled
    scale: float = 1.0
    name: str = ""

    def active(self, knee_angle):
        if self.kind != "conditional":
            return True
        lo, hi = self.active_range
        return lo - ACTIVITY_TOL <= knee_angle <= hi + ACTIVITY_TOL

    def local(self, knee_angle):
        """Location in its body frame and its derivative with respect to the Gait2392 knee angle."""
        if self.kind != "moving":
            return self.location, np.zeros(3)
        p = np.array([f[0](knee_angle) for f in self.funcs]) * self.scale
        dp = np.array([f[1](knee_angle) for f in self.funcs]) * self.scale
        return p, dp


@dataclass
class Actuator:
    name: str                       # Gait2392 name, e.g. 'vas_lat_r'
    entity: str                     # anatomical muscle it represents
    f0: float                       # N, maximum isometric (fiber) force, D-056
    l_opt: float                    # m
    l_ts: float                     # m
    alpha0: float                   # rad
    v_max: float                    # optimal fiber lengths per second
    points: list = field(default_factory=list)


def load_actuators(scale=1.0, schema=None):
    """The 14 actuators from the muscle dataset, lengths scaled by `scale` (D-059 item 7)."""
    schema = schema or QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    d = schema.load_dataset(DATA / MUSCLES)
    obs = d["observations"]
    used = []
    names = []
    for oid in obs:
        m = re.fullmatch(r"LB-QD:G2392:MUS:(\w+):MAXIMUM_ISOMETRIC_FORCE", oid)
        if m:
            names.append(m.group(1))
    acts = []
    for key in names:
        def v(prop):
            oid = f"LB-QD:G2392:MUS:{key}:{prop}"
            used.append(oid)
            return obs[oid]["value"]
        f0 = v("MAXIMUM_ISOMETRIC_FORCE")
        a = Actuator(key.lower(), obs[f"LB-QD:G2392:MUS:{key}:MAXIMUM_ISOMETRIC_FORCE"]["target"]["entity_ids"][0],
                     float(f0), scale * float(v("OPTIMAL_FIBER_LENGTH")), scale * float(v("TENDON_SLACK_LENGTH")),
                     float(v("PENNATION_ANGLE_AT_OPTIMAL")), float(v("MAXIMUM_CONTRACTION_VELOCITY")))
        k = 1
        while f"LB-QD:G2392:MUS:{key}:PATH:{k:02d}" in obs:
            oid = f"LB-QD:G2392:MUS:{key}:PATH:{k:02d}"
            used.append(oid)
            o = obs[oid]
            frame = FRAMES[o["coordinate_context"]["frame_id"]]
            val = o["value"]
            if o["value_form"] == "vector":
                pt = PathPoint(frame, "fixed", scale * np.array(val, float))
            elif val["kind"] == "conditional":
                pt = PathPoint(frame, "conditional", scale * np.array(val["location"], float),
                               active_range=tuple(val["active_range"]))
            else:
                pt = PathPoint(frame, "moving", funcs=tuple(_coordinate_function(val[ax]) for ax in "xyz"),
                               scale=scale)
            pt.name = f"{a.name}-P{k}"
            a.points.append(pt)
            k += 1
        acts.append(a)
    return acts, {MUSCLES: used}


def muscle_traceability(consumed, schema=None):
    """D-055 C4 gate on every muscle observation consumed."""
    schema = schema or QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    return {name: require_traceable(schema, schema.load_dataset(DATA / name), sorted(set(ids)))
            for name, ids in consumed.items()}


# ------------------------------------------------------------------------ geometry
@dataclass
class Joints:
    """Gait2392 joint locations used by D1, scaled: hip in pelvis, knee in femur, ankle in tibia, subtalar in talus."""
    hip: np.ndarray
    knee: np.ndarray
    ankle: np.ndarray
    subtalar: np.ndarray


def d1_joints(scale=1.0, schema=None):
    """Joint locations exactly as D1 uses them (knee frozen at knee angle 0), as 3-vectors, scaled."""
    schema = schema or QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    d = schema.load_dataset(DATA / "segments_gait2392.yaml")["observations"]
    v = lambda j: scale * np.array(d[f"LB-QD:G2392:JOINT:{j}"]["value"], float)  # noqa: E731
    return Joints(v("HIP_R"), v("KNEE_R"), v("ANKLE_R"), v("SUBTALAR_R"))


def _rz(phi):
    c, s = math.cos(phi), math.sin(phi)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def _z(w):
    """d/dphi of R(phi) u, written in terms of w = R(phi) u."""
    return np.array([-w[1], w[0], 0.0])


def point_world(pt, q, joints):
    """Position of a path point in the fixed foot frame (ankle centre at the origin) and d(position)/dq (3 x 3)."""
    qa, qk, qh = q
    phi = B_MAP @ np.asarray(q, float)
    Rs, Rt, Rh = _rz(phi[0]), _rz(phi[1]), _rz(phi[2])
    knee_angle = -qk
    p, dp = pt.local(knee_angle)
    J = np.zeros((3, 3))
    if pt.frame == "calcn":
        return joints.subtalar + p, J
    if pt.frame == "tibia":
        w = Rs @ (p - joints.ankle)
        J += np.outer(_z(w), B_MAP[0])
        J[:, 1] += Rs @ (-dp)          # d(local)/dq_knee = -d(local)/d(knee_angle)
        return w, J
    K = Rs @ (-joints.ankle)
    JK = np.outer(_z(K), B_MAP[0])
    if pt.frame == "femur":
        w = Rt @ (p - joints.knee)
        return K + w, JK + np.outer(_z(w), B_MAP[1])
    H_rel = Rt @ (-joints.knee)
    w = Rh @ (p - joints.hip)
    return K + H_rel + w, JK + np.outer(_z(H_rel), B_MAP[1]) + np.outer(_z(w), B_MAP[2])


def path(act, q, joints):
    """Length (m), moment arms R = -dL/dq (m, 3) and the active point positions, on the active branch at q."""
    knee_angle = -q[1]
    pts = [point_world(p, q, joints) for p in act.points if p.active(knee_angle)]
    length, dL = 0.0, np.zeros(3)
    for (a, Ja), (b, Jb) in zip(pts, pts[1:]):
        seg = b - a
        n = float(np.linalg.norm(seg))
        e = seg / n
        length += n
        dL += e @ (Jb - Ja)
    return length, -dL, [p[0] for p in pts]


def branch_active_set(act, q):
    return tuple(p.active(-q[1]) for p in act.points)


# ---------------------------------------------------------------------- force law
FLAG_X, FLAG_LENGTH, FLAG_VELOCITY = "x_nonpositive", "fiber_length_out_of_domain", "fiber_velocity_out_of_domain"


def fiber_state(act, length, length_rate):
    """Rigid tendon, constant thickness. Returns a dict of intermediates and domain flags."""
    vals = (length, length_rate)
    if not all(math.isfinite(v) for v in vals):
        raise FloatingPointError(f"{act.name}: non-finite musculotendon state {vals}")
    h = act.l_opt * math.sin(act.alpha0)
    x = length - act.l_ts
    flags = []
    if x <= 0.0:
        return {"x": x, "l_m": float("nan"), "cos_alpha": float("nan"), "alpha": float("nan"),
                "l_norm": float("nan"), "v_m": float("nan"), "v_norm": float("nan"), "flags": [FLAG_X]}
    l_m = math.hypot(x, h)
    cos_a = x / l_m
    l_norm = l_m / act.l_opt
    v_m = cos_a * length_rate
    v_norm = v_m / (act.v_max * act.l_opt)
    if not (MIN_NORM_FIBER_LENGTH <= l_norm <= MAX_NORM_FIBER_LENGTH):
        flags.append(FLAG_LENGTH)
    if not (VELOCITY_DOMAIN[0] <= v_norm <= VELOCITY_DOMAIN[1]):
        flags.append(FLAG_VELOCITY)
    return {"x": x, "l_m": l_m, "cos_alpha": cos_a, "alpha": math.acos(cos_a), "l_norm": l_norm,
            "v_m": v_m, "v_norm": v_norm, "flags": flags}


def unit_tendon_force(act, state):
    """Baseline tendon force at full activation (N): F0 f_act f_v cos(alpha); 0 if out of domain (excluded)."""
    if state["flags"]:
        return 0.0
    return act.f0 * float(f_active(state["l_norm"])) * float(f_velocity(state["v_norm"])) * state["cos_alpha"]


def passive_tendon_force(act, state, strain=0.6):
    """Passive tendon force (N) for the sensitivity case; 0 if out of domain (excluded)."""
    if state["flags"]:
        return 0.0
    return act.f0 * max(0.0, float(f_passive(state["l_norm"], strain))) * state["cos_alpha"]


# ---------------------------------------------------------------------- optimizer
@dataclass
class Recruitment:
    activation: np.ndarray
    reserve: np.ndarray          # signed, per joint, N m (stage 2)
    t_star: float                # stage-1 optimum, N m
    band: float                  # t_star + delta
    kkt: dict
    solvers: dict


def stage1(Cm, tau, method="highs-ds"):
    """min t over 0<=a<=1, t>=0, |tau - C a| <= t. Returns (t*, a, residuals)."""
    m, n = Cm.shape
    A = np.vstack((np.column_stack((-Cm, -np.ones(m))), np.column_stack((Cm, -np.ones(m)))))
    b = np.concatenate((-tau, tau))
    cost = np.r_[np.zeros(n), 1.0]
    res = linprog(cost, A_ub=A, b_ub=b, bounds=[(0.0, 1.0)] * n + [(0.0, None)], method=method)
    if not res.success:
        raise RuntimeError(f"stage 1 LP failed: {res.message}")
    # KKT for HiGHS sign conventions: cost = A^T y_ub + z_lower + z_upper, y_ub <= 0, z_lower >= 0, z_upper <= 0.
    y, zl, zu = res.ineqlin.marginals, res.lower.marginals, res.upper.marginals
    stat = cost - A.T @ y - zl - zu
    slack = b - A @ res.x
    kkt = {"stationarity": float(np.max(np.abs(stat))),
           "dual_feasibility": float(max(0.0, np.max(y), -np.min(zl), np.max(zu))),
           "complementarity": float(np.max(np.abs(y * slack))),
           "primal": float(max(0.0, -np.min(slack)))}
    return float(res.x[-1]), res.x[:-1], kkt


def _stage2_constraints(Cm, tau, band):
    """Rows g with g @ a >= h: C a >= tau - band, -C a >= -(tau + band), a >= 0, -a >= -1."""
    n = Cm.shape[1]
    G = np.vstack((Cm, -Cm, np.eye(n), -np.eye(n)))
    h = np.concatenate((tau - band, -(tau + band), np.zeros(n), -np.ones(n)))
    return G, h


def stage2(Cm, tau, band):
    """min sum a^2 subject to |tau - C a| <= band and 0 <= a <= 1, by the Goldfarb-Idnani active-set
    method (quadprog). Returns the activations and KKT residuals computed from its multipliers."""
    import quadprog
    n = Cm.shape[1]
    G, h = _stage2_constraints(Cm, tau, band)
    try:
        a, _, _, _, lam, _ = quadprog.solve_qp(2.0 * np.eye(n), np.zeros(n), G.T, h, 0)
    except ValueError as exc:   # quadprog reports infeasibility this way
        raise RuntimeError(f"stage 2 QP failed: {exc}") from exc
    slack = G @ a - h
    stat = 2.0 * a - G.T @ lam
    kkt = {"stationarity": float(np.max(np.abs(stat))), "dual_feasibility": float(max(0.0, -np.min(lam))),
           "complementarity": float(np.max(np.abs(lam * slack))), "primal": float(max(0.0, -np.min(slack)))}
    return a, kkt


def stage2_second(Cm, tau, band):
    """Independent second solver for stage 2: Clarabel, an interior-point conic solver.

    (HiGHS's QP solver was tried first and cycles on degenerate cases such as many
    identical actuators at their upper bound, so it is not used.)"""
    import clarabel
    import scipy.sparse as sp
    m, n = Cm.shape
    A = sp.csc_matrix(np.vstack((Cm, -Cm, -np.eye(n), np.eye(n))))
    b = np.concatenate((tau + band, -(tau - band), np.zeros(n), np.ones(n)))
    st = clarabel.DefaultSettings()
    st.verbose = False
    st.tol_gap_abs = st.tol_gap_rel = st.tol_feas = 1e-12
    st.tol_ktratio = 1e-10
    sol = clarabel.DefaultSolver(sp.csc_matrix(2.0 * np.eye(n)), np.zeros(n), A, b,
                                 [clarabel.NonnegativeConeT(A.shape[0])], st).solve()
    status = str(sol.status)
    if status not in ("Solved", "AlmostSolved"):   # AlmostSolved: reduced accuracy; the agreement check decides
        raise RuntimeError(f"stage 2 second solver: {status}")
    return np.array(sol.x), status


def smallest_reserve_per_joint(Cm, tau, band):
    """Diagnostic, not part of recruitment: for each joint, the smallest |reserve| any bounded activation can give
    there while every joint stays within the stage-2 band. A joint whose value equals t* is limiting."""
    m, n = Cm.shape
    out = []
    for j in range(m):
        # variables a (n), u (1): minimize u subject to |tau_j - C_j a| <= u and |tau_k - C_k a| <= band for all k
        A, b = [], []
        for k in range(m):
            A += [np.r_[-Cm[k], 0.0], np.r_[Cm[k], 0.0]]
            b += [band - tau[k], band + tau[k]]
        A += [np.r_[-Cm[j], -1.0], np.r_[Cm[j], -1.0]]
        b += [-tau[j], tau[j]]
        res = linprog(np.r_[np.zeros(n), 1.0], A_ub=np.array(A), b_ub=np.array(b),
                      bounds=[(0.0, 1.0)] * n + [(0.0, None)], method="highs-ds")
        if not res.success:
            raise RuntimeError(f"smallest reserve LP failed: {res.message}")
        out.append(float(res.x[-1]))
    return np.array(out)


def recruit(Cm, tau, delta=1e-6, second_solver=True):
    """Two-stage recruitment at one sample (D-059 Amendment 2). Cm: joints x actuators (N m at full activation)."""
    Cm, tau = np.asarray(Cm, float), np.asarray(tau, float)
    t_star, _, kkt1 = stage1(Cm, tau)
    band = t_star + delta
    a, kkt2 = stage2(Cm, tau, band)
    a = np.clip(a, 0.0, 1.0)          # removes round-off of order 1e-16 outside the bounds after the KKT check
    solvers = {"stage1": "scipy linprog highs-ds", "stage2": "quadprog (Goldfarb-Idnani)"}
    if second_solver:
        t_alt, _, _ = stage1(Cm, tau, method="highs-ipm")
        try:
            a_alt, status = stage2_second(Cm, tau, band)
            diff = float(np.max(np.abs(a_alt - a)))
        except RuntimeError as exc:          # a failed cross-check is a failed verification, never skipped
            status, diff = str(exc), float("inf")
        solvers.update({"stage1_second": "scipy linprog highs-ipm", "stage2_second": "Clarabel (interior point)",
                        "stage2_second_status": status, "t_star_difference": abs(t_alt - t_star),
                        "activation_difference": diff})
    return Recruitment(a, tau - Cm @ a, t_star, band, {"stage1": kkt1, "stage2": kkt2}, solvers)
