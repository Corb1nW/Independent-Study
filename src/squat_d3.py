"""Stage D3: the D1 squat with Gait2392's moving knee (D-060).

The knee keeps one coordinate (q_knee, flexion positive). As in Gait2392, the tibia origin
sits at T(theta) in the femur frame, with theta = -q_knee the Gait2392 knee angle and T read
from the model's two translation splines (dataset observation LB-QD:G2392:JOINT:KNEE_R_MOVING,
evaluated with the ported OpenSim SimmSpline). The female and male bodies scale T by D1's
stature factor. Segment masses, centres of mass and inertias are D1's, fixed in their own body
frames: the thigh's centre of mass, stored by D1 relative to its fixed knee datum, is converted
to the femur frame once (ChatGPT note D3-N02). The motion is D1's.

Two independent inverse-dynamics formulations:
- Newton-Euler: D1's recursion with the moving joint point; the knee's generalized force is the
  joint moment plus the work of the joint force F (on the thigh, from the shank) over the
  displacement of the thigh-fixed point at the joint relative to the shank per unit q_knee. The
  tibia origin slides by R_thigh dT within the femur, so that point moves by -R_thigh dT:
  tau_knee = M_knee - F . (R_thigh dT/dq_knee);
- Kane's method: generalized inertia and gravity forces projected on analytic partial
  velocities (Jacobians with the spline derivatives); also gives the mass matrix and bias for
  the forward checks.

With `frozen=True` the knee is fixed at D1's datum (a linear interpolation, not T(0)), and the
module must reproduce D1's torques (regression; note D3-N02). Frames, signs and coordinates
follow src/squat_d1.py.
"""
from dataclasses import dataclass
import math

import numpy as np

from . import squat_d1 as sq
from .muscles_d2 import SimmSpline
from .quantitative import QuantitativeSchema

ROOT = sq.ROOT
KNEE_OBS = "LB-QD:G2392:JOINT:KNEE_R_MOVING"
KNEE_FIXED_OBS = "LB-QD:G2392:JOINT:KNEE_R"


# ------------------------------------------------------------------------ knee model
class MovingKnee:
    """T(theta) of the tibia origin in the femur frame (2-D, metres), scaled; derivatives with respect to q_knee."""

    def __init__(self, value, scale=1.0, frozen_at=None):
        self.scale = float(scale)
        self.frozen_at = None if frozen_at is None else np.asarray(frozen_at, float)[:2] * self.scale
        self.sx = SimmSpline(value["x"]["x"], value["x"]["y"])
        self.sy = SimmSpline(value["y"]["x"], value["y"]["y"])

    def T(self, q_knee):
        """Position, d/dq_knee and d2/dq_knee2 (theta = -q_knee, so d/dq = -d/dtheta)."""
        if self.frozen_at is not None:
            return self.frozen_at.copy(), np.zeros(2), np.zeros(2)
        th = -float(q_knee)
        s = self.scale
        p = s * np.array([self.sx.value(th), self.sy.value(th)])
        d = -s * np.array([self.sx.derivative(th), self.sy.derivative(th)])
        dd = s * np.array([self.sx.second_derivative(th), self.sy.second_derivative(th)])
        return p, d, dd


def load_knee(scale=1.0, schema=None, frozen=False):
    schema = schema or QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    obs = schema.load_dataset(sq.DATA / sq.G2392)["observations"]
    fixed = obs[KNEE_FIXED_OBS]["value"] if frozen else None
    return MovingKnee(obs[KNEE_OBS]["value"], scale, frozen_at=fixed), [KNEE_OBS] + ([KNEE_FIXED_OBS] if frozen else [])


# ------------------------------------------------------------------------- body
@dataclass
class D3Body:
    """D1's per-leg body with the moving knee. Vectors are 2-D, in each segment's own frame."""
    base: sq.Body
    knee: MovingKnee
    u_s: np.ndarray      # tibia origin (knee) relative to the ankle, tibia axes
    c_s: np.ndarray      # shank centre of mass relative to the ankle
    c_f: np.ndarray      # thigh centre of mass relative to the hip (femur origin), femur axes (converted once)
    c_h: np.ndarray      # HAT centre of mass relative to the hip
    mass: tuple
    inertia: tuple

    @property
    def name(self):
        return self.base.name


def build_body(name, schema=None, frozen=False):
    schema = schema or QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml")
    base = sq.build_body(name, schema)
    scale = 1.0 if name == "gait2392" else base.stature / sq.gait2392_geometry(schema)[0]["stature"]
    knee, used = load_knee(scale, schema, frozen)
    base.consumed.setdefault(sq.G2392, []).extend(used)
    sh, th, hat = (base.segments[k] for k in sq.MOVING)
    # D1's thigh frame has its origin at the fixed knee datum, with the hip at `upper`;
    # in the femur frame (origin at the hip) the centre of mass is com - upper (note D3-N02).
    return D3Body(base, knee, np.asarray(sh.upper, float), np.asarray(sh.com, float),
                  np.asarray(th.com, float) - np.asarray(th.upper, float), np.asarray(hat.com, float),
                  (sh.mass, th.mass, hat.mass), (sh.inertia, th.inertia, hat.inertia))


def _rot(phi):
    c, s = math.cos(phi), math.sin(phi)
    return np.array([[c, -s], [s, c]])


def _z(v):
    return np.array([-v[1], v[0]])


# --------------------------------------------------------------------- kinematics
def kinematics(b, q, qd, qdd):
    """Positions, velocities and accelerations (2 x n) of joints and centres of mass, ankle at the origin."""
    q, qd, qdd = (np.atleast_2d(np.asarray(x, float)) for x in (q, qd, qdd))
    phi, w, al = sq.B_MAP @ q, sq.B_MAP @ qd, sq.B_MAP @ qdd
    n = q.shape[1]
    keys = ("knee", "hip", "com_shank", "com_thigh", "com_hat")
    out = {k: (np.zeros((2, n)), np.zeros((2, n)), np.zeros((2, n))) for k in keys}
    for i in range(n):
        Rs, Rt, Rh = _rot(phi[0, i]), _rot(phi[1, i]), _rot(phi[2, i])
        ws, wt, wh = w[:, i]
        as_, at, ah = al[:, i]
        T, Tq, Tqq = b.knee.T(q[1, i])
        qk, qkk = qd[1, i], qdd[1, i]

        def rigid(R, v, om, a):
            p = R @ v
            return p, om * _z(p), a * _z(p) - om * om * p
        k = rigid(Rs, b.u_s, ws, as_)
        RT = Rt @ T
        RTq = Rt @ Tq
        # relative vector hip - knee = -R_t T(q_knee)
        rel = (-RT, -(wt * _z(RT) + RTq * qk),
               -(at * _z(RT) - wt * wt * RT + 2 * wt * qk * _z(RTq) + Rt @ Tqq * qk * qk + RTq * qkk))
        h = tuple(k[j] + rel[j] for j in range(3))
        cs = rigid(Rs, b.c_s, ws, as_)
        ct = tuple(h[j] + rigid(Rt, b.c_f, wt, at)[j] for j in range(3))
        ch = tuple(h[j] + rigid(Rh, b.c_h, wh, ah)[j] for j in range(3))
        for key, val in zip(keys, (k, h, cs, ct, ch)):
            for j in range(3):
                out[key][j][:, i] = val[j]
    out["ankle"] = (np.zeros((2, n)),) * 3
    out["phi"], out["omega"], out["alpha"] = phi, w, al
    return out


# ------------------------------------------------------------- Newton-Euler
def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def inverse_dynamics(b, q, qd, qdd, gravity):
    """Newton-Euler from the HAT down, with the knee's translation term. Same outputs as D1's."""
    q, qd, qdd = (np.atleast_2d(np.asarray(x, float)) for x in (q, qd, qdd))
    k = kinematics(b, q, qd, qdd)
    n = q.shape[1]
    gvec = np.array([0.0, -gravity])[:, None]
    lower = {"shank": "ankle", "thigh": "knee", "hat": "hip"}
    force_above, moment_above, point_above = np.zeros((2, n)), np.zeros(n), None
    moments, forces = {}, {}
    for i, name in reversed(list(enumerate(sq.MOVING))):
        c, _, a = k[f"com_{name}"]
        p_low = k[lower[name]][0]
        f = b.mass[i] * (a - gvec) + force_above
        m = b.inertia[i] * k["alpha"][i] + moment_above - _cross(p_low - c, f)
        if point_above is not None:
            m = m + _cross(point_above - c, force_above)
        moments[lower[name]], forces[lower[name]] = m, f
        force_above, moment_above, point_above = f, m, p_low
    # Knee: the thigh-fixed point at the joint moves by -R_t dT/dq relative to the shank per unit q_knee.
    # (A first version used +R_t dT/dq; the Kane formulation caught the sign, at about 12 N m.)
    trans = np.zeros(n)
    for i in range(n):
        _, Tq, _ = b.knee.T(q[1, i])
        trans[i] = -forces["knee"][:, i] @ (_rot(k["phi"][1, i]) @ Tq)
    tau = np.stack([-moments["ankle"], moments["knee"] + trans, -moments["hip"]])
    foot = b.base.foot
    grf = forces["ankle"] - foot.mass * gvec
    h = -foot.ground_y
    with np.errstate(divide="ignore", invalid="ignore"):
        cop = (moments["ankle"] + foot.mass * gravity * foot.com[0] - h * grf[0]) / grf[1]
    return {"tau": tau, "grf": grf, "cop_x": cop, "joint_forces": forces, "joint_moments": moments,
            "knee_translation_term": trans, "kinematics": k}


# ------------------------------------------------------------------ Kane's method
def _jacobians(b, q):
    """Positions (2) and partial-velocity Jacobians (2 x 3) of the three centres of mass, with the quadratic
    acceleration terms as functions of qdot (returned as callables), computed analytically."""
    phi = sq.B_MAP @ q
    Rs, Rt, Rh = _rot(phi[0]), _rot(phi[1]), _rot(phi[2])
    B = sq.B_MAP
    T, Tq, Tqq = b.knee.T(q[1])
    e1 = np.array([0.0, 1.0, 0.0])

    def rigid(R, v, row):
        p = R @ v
        return p, np.outer(_z(p), B[row]), (lambda qd, p=p, row=row: -(B[row] @ qd) ** 2 * p)
    pk, Jk, qk_ = rigid(Rs, b.u_s, 0)
    RT, RTq, RTqq = Rt @ T, Rt @ Tq, Rt @ Tqq
    Jrel = -(np.outer(_z(RT), B[1]) + np.outer(RTq, e1))

    def qrel(qd):
        wt, qkd = B[1] @ qd, qd[1]
        return -(-wt * wt * RT + 2 * wt * qkd * _z(RTq) + RTqq * qkd * qkd)
    ph, Jh = pk - RT, Jk + Jrel
    cs = rigid(Rs, b.c_s, 0)
    ft = rigid(Rt, b.c_f, 1)
    fh = rigid(Rh, b.c_h, 2)
    bodies = [cs,
              (ph + ft[0], Jh + ft[1], lambda qd: qk_(qd) + qrel(qd) + ft[2](qd)),
              (ph + fh[0], Jh + fh[1], lambda qd: qk_(qd) + qrel(qd) + fh[2](qd))]
    return bodies


def kane(b, q, qd, qdd, gravity):
    """Generalized forces by Kane's method; also the mass matrix M and bias h (tau = M qdd + h)."""
    q, qd, qdd = (np.atleast_2d(np.asarray(x, float)) for x in (q, qd, qdd))
    n = q.shape[1]
    tau, Ms, hs = np.zeros((3, n)), np.zeros((n, 3, 3)), np.zeros((3, n))
    g = np.array([0.0, -gravity])
    for i in range(n):
        M, h = np.zeros((3, 3)), np.zeros(3)
        for j, (p, J, quad) in enumerate(_jacobians(b, q[:, i])):
            m, I, Jw = b.mass[j], b.inertia[j], sq.B_MAP[j]
            M += m * J.T @ J + I * np.outer(Jw, Jw)
            h += m * J.T @ (quad(qd[:, i]) - g)
        Ms[i], hs[:, i] = M, h
        tau[:, i] = M @ qdd[:, i] + h
    return {"tau": tau, "M": Ms, "h": hs}


def potential(b, q, gravity):
    """Potential energy of the moving segments (J), from centre-of-mass heights."""
    return sum(b.mass[j] * gravity * p[1] for j, (p, _, _) in enumerate(_jacobians(b, np.asarray(q, float))))


def kinetic(b, q, qd):
    M = kane(b, q[:, None], qd[:, None], np.zeros((3, 1)), 0.0)["M"][0]
    return 0.5 * qd @ M @ qd


def _d5(f, h):
    """Fourth-order central difference: (-f(2h) + 8 f(h) - 8 f(-h) + f(-2h)) / (12 h)."""
    return (-f(2 * h) + 8 * f(h) - 8 * f(-h) + f(-2 * h)) / (12 * h)


def static_torques(b, q, gravity, h=1e-3):
    """Held still, the torque balances gravity: tau = dV/dq, by fourth-order differences of the potential."""
    q = np.asarray(q, float)
    return np.array([_d5(lambda s, e=e: potential(b, q + s * e, gravity), h) for e in np.eye(3)])


def forward_accel(b, q, qd, tau, gravity):
    k = kane(b, q[:, None], qd[:, None], np.zeros((3, 1)), gravity)
    return np.linalg.solve(k["M"][0], tau - k["h"][:, 0])


# ---------------------------------------------------------------- forward checks
def _driven_rhs(b, motion, gravity):
    def rhs(t, y):
        qq, qqd, qqdd = motion(np.array([t]))
        tau = inverse_dynamics(b, qq, qqd, qqdd, gravity)["tau"][:, 0]
        return np.concatenate([y[3:], forward_accel(b, y[:3], y[3:], tau, gravity)])
    return rhs


def _exact(motion, t):
    q, qd, _ = motion(np.array([t]))
    return np.concatenate([q[:, 0], qd[:, 0]])


def local_step_error(b, motion, gravity, step, starts=30):
    """One RK4 step of Kane's equations driven by Newton-Euler torques, from exact states (as D1)."""
    rhs = _driven_rhs(b, motion, gravity)
    err = 0.0
    for t in np.linspace(0.0, motion.period - step, starts):
        y = sq._rk4(rhs, t, _exact(motion, t), step)
        err = max(err, float(np.max(np.abs(y[:3] - _exact(motion, t + step)[:3]))))
    return err


def short_horizon_error(b, motion, gravity, step, horizon=0.1, starts=6):
    rhs = _driven_rhs(b, motion, gravity)
    n = int(round(horizon / step))
    err = 0.0
    for t0 in np.linspace(0.0, motion.period - horizon, starts):
        y, t = _exact(motion, t0), t0
        for _ in range(n):
            y = sq._rk4(rhs, t, y, step)
            t += step
            err = max(err, float(np.max(np.abs(y[:3] - _exact(motion, t)[:3]))))
    return err


# ------------------------------------------------------------------------- run
def run(b, params):
    """D1's run with the moving knee: time series and contact checks (same structure as squat_d1.run)."""
    motion = sq.Motion(params["start_angles"], params["depth_angles"], params["period"])
    t = np.linspace(0.0, params["period"], int(params["samples"]))
    q, qd, qdd = motion(t)
    g = params["gravity"]
    foot = b.base.foot
    res = inverse_dynamics(b, q, qd, qdd, g)
    grf, cop = res["grf"], res["cop_x"]
    in_contact = grf[1] > 0
    cop = np.where(in_contact & np.isfinite(cop), cop, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        friction = np.where(in_contact, np.abs(grf[0]) / grf[1], np.inf)
    outside = ~np.isfinite(cop) | (cop < foot.heel[0]) | (cop > foot.ball[0])
    finite = cop[np.isfinite(cop)]
    contact = {
        "normal_force_min_N": float(np.min(grf[1])), "lift_off_samples": int(np.sum(~in_contact)),
        "cop_min_m": float(np.min(finite)) if finite.size else None,
        "cop_max_m": float(np.max(finite)) if finite.size else None,
        "support_heel_m": float(foot.heel[0]), "support_ball_m": float(foot.ball[0]),
        "heel_margin_min_m": float(np.min(finite) - foot.heel[0]) if finite.size else None,
        "cop_outside_support_samples": int(np.sum(outside)),
        "required_friction_max": float(np.max(friction)) if np.all(np.isfinite(friction)) else None,
        "friction_coefficient_assumed": params["friction_coefficient"],
        "friction_exceeded_samples": int(np.sum(friction > params["friction_coefficient"])),
    }
    contact["feasible"] = (contact["lift_off_samples"] == 0 and contact["cop_outside_support_samples"] == 0
                           and contact["friction_exceeded_samples"] == 0)
    k = res["kinematics"]
    return {"t": t, "q": q, "qd": qd, "qdd": qdd, "tau": res["tau"], "grf": grf, "cop_x": cop,
            "points": {key: k[key][0] for key in ("knee", "hip", "com_shank", "com_thigh", "com_hat")},
            "phi": k["phi"], "contact": contact, "motion": motion, "knee_translation_term": res["knee_translation_term"]}


def check_residuals(b, params, result, energy_dt=1e-3):
    """Residual of each mechanics check on this run (D-060 item 3; D1's set, adapted)."""
    g = params["gravity"]
    q, qd, qdd, tau = result["q"], result["qd"], result["qdd"], result["tau"]
    kn = kane(b, q, qd, qdd, g)
    motion = result["motion"]
    # energy: d/dt (T + V) by a fourth-order difference in time against joint power
    t = result["t"]

    def E(shift):
        qq, qqd, _ = motion(t + shift)
        return np.array([kinetic(b, qq[:, i], qqd[:, i]) + potential(b, qq[:, i], g) for i in range(qq.shape[1])])
    dEdt = _d5(E, energy_dt)
    # Newton: vertical ground force per leg equals the weight of the leg plus HAT share plus m a_y
    k = kinematics(b, q, qd, qdd)
    per_leg = b.base.foot.mass * g + sum(b.mass[j] * (g + k[f"com_{n}"][2][1]) for j, n in enumerate(sq.MOVING))
    grf = inverse_dynamics(b, q, qd, qdd, g)["grf"]
    static = max(float(np.max(np.abs(inverse_dynamics(b, qq[:, None], np.zeros((3, 1)), np.zeros((3, 1)), g)["tau"][:, 0]
                                      - static_torques(b, qq, g)))) for qq in q[:, ::30].T)
    return {
        "newton_euler_vs_kane_N_m": float(np.max(np.abs(tau - kn["tau"]))),
        "static_virtual_work_N_m": static,
        "energy_W": float(np.max(np.abs(np.sum(tau * qd, axis=0) - dEdt))),
        "newton_identity_per_leg_N": float(np.max(np.abs(grf[1] - per_leg))),
        "local_one_step_rad_at_1ms": local_step_error(b, motion, g, 0.001),
        "short_horizon_0p1s_rad_at_1ms": short_horizon_error(b, motion, g, 0.001),
        "mass_bookkeeping_relative": float(2 * b.base.per_leg_mass() / b.base.body_mass - 1),
    }
