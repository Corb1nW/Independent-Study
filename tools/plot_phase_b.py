"""Plot hip angle against time for the Phase B runs in a manifest (D-055 item C6).

    python -m tools.plot_phase_b --manifest results/phase_b/<file>.json --output results/phase_b/<file>.svg

Presentation only: no new science. Each curve is drawn from the manifest's own
initial state and constant angular acceleration, q(t) = q0 + v0*t + a*t^2/2,
which is the Phase B model's exact solution (D-053), up to the recorded exit
time. The figure carries the manifest's validity statement and commit.

The output is a self-contained SVG with no dependencies beyond the standard
library, so it renders on GitHub and in a browser. Colors follow a validated
categorical palette (blue, then orange); each line is also labeled directly,
so identity never depends on color alone.
"""
import argparse
import json
import math
from html import escape
from pathlib import Path

SERIES = ["#2a78d6", "#eb6834"]  # categorical slots 1 and 2 (validated light palette)
INK, INK_2, INK_3, GRID, SURFACE = "#0b0b0b", "#52514e", "#7a7974", "#e4e3df", "#fcfcfb"
W, H = 760, 500
LEFT, RIGHT, TOP, BOTTOM = 72, 40, 76, 128


def validity_text(run):
    validity = run.get("validity")
    if validity:
        return (f"{validity['kind']}. Physiological validity: {validity['physiological_validity']}; "
                f"clinical validity: {validity['clinical_validity']}.")
    return run.get("status", "validity not stated")  # manifests made before Phase C


def trajectory(run, samples=160):
    p = {k: v["value"] for k, v in run["configuration"]["parameters"].items()}
    sim = run["simulation"]
    q0, v0, a = p["initial_q_rad"], p["initial_qdot_rad_s"], sim["angular_acceleration_rad_s2"]
    end = sim["time_s"]
    points = []
    for i in range(samples + 1):
        t = end * i / samples
        points.append((t, math.degrees(q0 + v0 * t + a * t * t / 2)))
    return points, p


def label_for(run):
    multiplier = run["effective_values"]["scenario_multiplier"]
    name = "Baseline" if multiplier == 1 else f"Right Fmax ×{multiplier:g}"
    return name, run["effective_values"]["right_Fmax_N"]


def render(runs, manifest_name):
    if not runs:
        raise ValueError("manifest contains no runs")
    shas = {r["commit_sha"] for r in runs}
    if len(shas) != 1:
        raise ValueError("runs come from different commits")
    curves = [trajectory(r) for r in runs]
    p = curves[0][1]
    t_max = max(r["simulation"]["time_s"] for r in runs)
    x_max = math.ceil(t_max * 10) / 10 + 0.1
    y_min = math.floor(math.degrees(p["q_min_rad"]) / 10) * 10 - 5
    y_max = 5.0
    pw, ph = W - LEFT - RIGHT, H - TOP - BOTTOM

    def x(t):
        return LEFT + pw * t / x_max

    def y(deg):
        return TOP + ph * (y_max - deg) / (y_max - y_min)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'font-family="system-ui, -apple-system, Segoe UI, sans-serif" role="img" '
           f'aria-labelledby="t d">',
           f'<title id="t">Phase B hip model: hip angle over time</title>',
           f'<desc id="d">Right hip angle from rest until it reaches the demonstration domain limit, '
           f'for {len(runs)} runs from one commit.</desc>',
           f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
           f'<text x="{LEFT}" y="30" font-size="17" font-weight="600" fill="{INK}">'
           f'Hip angle over time: stronger gluteus maximus reaches the limit sooner</text>',
           f'<text x="{LEFT}" y="52" font-size="12.5" fill="{INK_2}">Right hip, sagittal plane; '
           f'flexion positive. Demonstration model (D-053), not a prediction.</text>']
    # grid and y axis (degrees)
    tick = 10
    deg = 0
    while deg >= y_min:
        out.append(f'<line x1="{LEFT}" x2="{LEFT + pw}" y1="{y(deg):.1f}" y2="{y(deg):.1f}" '
                   f'stroke="{GRID}" stroke-width="1"/>')
        out.append(f'<text x="{LEFT - 8}" y="{y(deg) + 4:.1f}" font-size="12" fill="{INK_3}" '
                   f'text-anchor="end">{str(deg).replace("-", "−")}°</text>')
        deg -= tick
    # x axis (seconds)
    steps = int(round(x_max / 0.1))
    for i in range(0, steps + 1, 2):
        t = i * 0.1
        out.append(f'<text x="{x(t):.1f}" y="{TOP + ph + 20}" font-size="12" fill="{INK_3}" '
                   f'text-anchor="middle">{t:.1f}</text>')
    out.append(f'<line x1="{LEFT}" x2="{LEFT + pw}" y1="{TOP + ph}" y2="{TOP + ph}" stroke="{INK_3}" '
               f'stroke-width="1"/>')
    out.append(f'<text x="{LEFT + pw / 2:.1f}" y="{TOP + ph + 40}" font-size="12.5" fill="{INK_2}" '
               f'text-anchor="middle">Time (s)</text>')
    out.append(f'<text x="18" y="{TOP + ph / 2:.1f}" font-size="12.5" fill="{INK_2}" text-anchor="middle" '
               f'transform="rotate(-90 18 {TOP + ph / 2:.1f})">Hip angle</text>')
    # domain limit
    lim = math.degrees(p["q_min_rad"])
    out.append(f'<line x1="{LEFT}" x2="{LEFT + pw}" y1="{y(lim):.1f}" y2="{y(lim):.1f}" stroke="{INK_2}" '
               f'stroke-width="1.5" stroke-dasharray="5 4"/>')
    out.append(f'<text x="{LEFT + 6}" y="{y(lim) + 16:.1f}" font-size="11.5" fill="{INK_2}">'
               f'Demonstration domain limit ({lim:.0f}°): run stops here</text>'.replace("(-", "(−"))
    # curves, exit markers, legend (top right, where the plot is empty)
    lx, ly0 = LEFT + pw - 230, y(-5)
    ends = []
    for k, (run, (points, _)) in enumerate(zip(runs, curves)):
        color = SERIES[k % len(SERIES)]
        name, force = label_for(run)
        d = " ".join(f"{'M' if i == 0 else 'L'}{x(t):.2f},{y(v):.2f}" for i, (t, v) in enumerate(points))
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" '
                   f'stroke-linejoin="round" stroke-linecap="round"/>')
        te, qe = points[-1]
        ends.append((te, qe))
        tip = f"{name}: F = {force:.1f} N; reaches {qe:.0f}° at t = {te:.4f} s"
        out.append(f'<circle cx="{x(te):.2f}" cy="{y(qe):.2f}" r="5" fill="{color}" stroke="{SURFACE}" '
                   f'stroke-width="2"><title>{escape(tip)}</title></circle>')
        ly = ly0 + 40 * k
        out.append(f'<line x1="{lx}" x2="{lx + 18}" y1="{ly - 4}" y2="{ly - 4}" stroke="{color}" '
                   f'stroke-width="2.5" stroke-linecap="round"/>')
        out.append(f'<text x="{lx + 26}" y="{ly:.1f}" font-size="12.5" font-weight="600" '
                   f'fill="{INK}">{escape(name)}</text>')
        out.append(f'<text x="{lx + 26}" y="{ly + 16:.1f}" font-size="11.5" fill="{INK_2}">'
                   f'Fmax {force:.1f} N · reaches limit at {te:.3f} s</text>')
    if len(ends) == 2:
        (t1, q1), (t2, _) = ends
        gap_ms = abs(t1 - t2) * 1000
        mid = x((t1 + t2) / 2)
        out.append(f'<text x="{mid:.1f}" y="{y(q1) + 18:.1f}" font-size="11.5" fill="{INK_2}" '
                   f'text-anchor="middle">{gap_ms:.0f} ms sooner</text>')
    # footer: validity and provenance
    sha = next(iter(shas))
    footer = [validity_text(runs[0]),
              "Activation, moment arm and inertia are demonstration assumptions (config/phase_b_hip.yaml).",
              "Fmax: Arnold et al. 2010, whole gluteus maximus (LB-QD:GMAX:FMAX:ARNOLD2010).",
              f"Source: {manifest_name} · commit {sha[:12]} · provenance "
              f"{runs[0]['commit_provenance_status']}"]
    for i, line in enumerate(footer):
        out.append(f'<text x="{LEFT}" y="{H - 60 + 16 * i}" font-size="11" fill="{INK_3}">'
                   f'{escape(line)}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runs = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(runs, args.manifest.name), encoding="utf-8")
    print("Figure written to", args.output)


if __name__ == "__main__":
    main()
