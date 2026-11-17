"""Musculotendon paths on an assembled model (D-062 item 6): generic geometry.

Path points sit in any frame of any segment. A conditional point is active when its coordinate's model value lies
in its range (OpenSim's inclusive rule, widened by 1e-5 rad); a moving point's location is a function of its
coordinate's model value. Length L is the sum of distances between consecutive active points; moment arms
R = -dL/dq for every retained coordinate, from the active set at that configuration (as src/muscles_d2.py; nothing
differences L across samples). Positions are in the ground segment's coordinates.
"""
import numpy as np

from .model_assembly import point_active, point_in_world, segment_frames


def point_positions(model, act, q, frames=None):
    """[(position 3-vector, d/dq 3 x n)] of the actuator's active points at q."""
    q = np.asarray(q, float)
    frames = frames or segment_frames(model, q)
    out = []
    for pt in act.points:
        if not point_active(pt, q):
            continue
        seg = model.segments[pt.segment]
        if pt.kind == "moving":
            p, dp, _ = pt.function.at(q[pt.coordinate])
        else:
            p, dp = pt.location, None
        w, J = point_in_world(model, frames, pt.segment, seg.frame_offsets[pt.frame] + p)
        if dp is not None:
            J = J.copy()
            J[:, pt.coordinate] += frames[pt.segment][3] @ dp
        out.append((w, J))
    return out


def path(model, act, q, frames=None):
    """Length (m), moment arms R = -dL/dq (m, one per coordinate) and the active point positions."""
    pts = point_positions(model, act, q, frames)
    length, dL = 0.0, np.zeros(len(model.coordinates))
    for (a, Ja), (b, Jb) in zip(pts, pts[1:]):
        seg = b - a
        n = float(np.linalg.norm(seg))
        length += n
        dL += (seg / n) @ (Jb - Ja)
    return length, -dL, [p for p, _ in pts]


def active_set(act, q):
    return tuple(point_active(p, np.asarray(q, float)) for p in act.points)


def recruit_series(model, q, qd, tau, delta, second_solver=True, needed_reserve=True):
    """Force law and two-stage recruitment at every sample, reusing src/muscles_d2.py unchanged (D-062 item 6).

    Returns activations, tendon forces, unit forces, normalized fiber length and velocity (actuators x n), signed
    reserves and the smallest needed reserve per coordinate (coordinates x n), t*, force-law domain flags, drawing
    points (x, y of the active points), and the worst KKT residual and second-solver differences."""
    from . import muscles_d2 as m2
    acts = model.actuators
    nq, n, k = len(model.coordinates), q.shape[1], len(acts)
    out = {"activation": np.zeros((k, n)), "force": np.zeros((k, n)), "unit": np.zeros((k, n)),
           "l_norm": np.full((k, n), np.nan), "v_norm": np.full((k, n), np.nan), "reserve": np.zeros((nq, n)),
           "needed": np.zeros((nq, n)), "t_star": np.zeros(n), "flags": [], "drawing": [],
           "lengths": np.zeros((k, n)), "moment_arms": np.zeros((k, nq, n))}
    worst = {"kkt": 0.0, "t_star_difference": 0.0, "activation_difference": 0.0}
    for i in range(n):
        frames = segment_frames(model, q[:, i])
        Cm = np.zeros((nq, k))
        frame = []
        for j, a in enumerate(acts):
            L, R, pts = path(model, a, q[:, i], frames)
            out["lengths"][j, i], out["moment_arms"][j, :, i] = L, R
            st = m2.fiber_state(a, L, -R @ qd[:, i])
            out["unit"][j, i] = m2.unit_tendon_force(a, st)
            Cm[:, j] = out["unit"][j, i] * R
            out["l_norm"][j, i], out["v_norm"][j, i] = st["l_norm"], st["v_norm"]
            out["flags"] += [{"sample": i, "actuator": a.name, "flag": f} for f in st["flags"]]
            frame.append([[round(float(p[0]), 5), round(float(p[1]), 5)] for p in pts])
        out["drawing"].append(frame)
        rec = m2.recruit(Cm, tau[:, i], delta=delta, second_solver=second_solver)
        out["activation"][:, i], out["reserve"][:, i], out["t_star"][i] = rec.activation, rec.reserve, rec.t_star
        out["force"][:, i] = rec.activation * out["unit"][:, i]
        if needed_reserve and rec.t_star > delta:
            out["needed"][:, i] = m2.smallest_reserve_per_joint(Cm, tau[:, i], rec.band)
        worst["kkt"] = max(worst["kkt"], *(v for st_ in rec.kkt.values() for v in st_.values()))
        if second_solver:
            worst["t_star_difference"] = max(worst["t_star_difference"], rec.solvers["t_star_difference"])
            worst["activation_difference"] = max(worst["activation_difference"], rec.solvers["activation_difference"])
    out["worst"] = worst
    return out


def moment_arm_series(model, q):
    """(actuator IDs, moment arms: actuators x coordinates x samples) over a motion."""
    q = np.asarray(q, float)
    R = np.zeros((len(model.actuators), len(model.coordinates), q.shape[1]))
    for i in range(q.shape[1]):
        frames = segment_frames(model, q[:, i])
        for j, a in enumerate(model.actuators):
            R[j, :, i] = path(model, a, q[:, i], frames)[1]
    return [a.id for a in model.actuators], R
