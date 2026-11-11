"""Build the Stage D2 muscle viewer: one self-contained HTML page from a D2 run manifest (D-059 item 10, Q55).

    python -m tools.build_d2_page --manifest results/phase_d/<d2 file>.json --output results/phase_d/<file>.html
    python -m tools.build_d2_page --manifest <d2 file>.json --moving-manifest <d3 file>.json --output <file>.html

With --moving-manifest (Stage D3, D-060 item 7) the page gains a knee switch: fixed (D1's knee, the D2
manifest) or moving (Gait2392's knee, the D3 manifest).

Presentation only: every number on the page is copied from the manifest. The page plays the
squat with the 14 muscle lines drawn along their active path points and coloured by
activation, beside per-muscle force traces and a reserve strip, and states the statuses,
the commit, the declared simplifications and the sources.
"""
import argparse
import json
from pathlib import Path

LABELS = {"female": "Female (de Leva)", "male": "Male (de Leva)", "gait2392": "Gait2392 reference"}
NAMES = {"glut_max1_r": "Gluteus max. (upper)", "glut_max2_r": "Gluteus max. (middle)",
         "glut_max3_r": "Gluteus max. (lower)", "bifemlh_r": "Biceps femoris (long)", "semimem_r": "Semimembranosus",
         "semiten_r": "Semitendinosus", "vas_med_r": "Vastus medialis", "vas_int_r": "Vastus intermedius",
         "vas_lat_r": "Vastus lateralis", "rect_fem_r": "Rectus femoris", "med_gas_r": "Gastrocnemius (medial)",
         "lat_gas_r": "Gastrocnemius (lateral)", "soleus_r": "Soleus", "tib_ant_r": "Tibialis anterior"}
GROUPS = [("Hip extensors", ["glut_max1_r", "glut_max2_r", "glut_max3_r"]),
          ("Hamstrings", ["bifemlh_r", "semimem_r", "semiten_r"]),
          ("Quadriceps", ["vas_med_r", "vas_int_r", "vas_lat_r", "rect_fem_r"]),
          ("Calf", ["med_gas_r", "lat_gas_r", "soleus_r"]), ("Shin", ["tib_ant_r"])]


def compact(manifest):
    runs = []
    for r in manifest["runs"]:
        s = r["series"]
        runs.append({
            "body": r["body"], "label": LABELS.get(r["body"], r["body"]), "mass": r["body_mass_kg"],
            "stature": r["stature_m"], "foot": r["foot"], "t": s["t_s"], "q": s["q_rad"], "tau": s["tau_per_leg_N_m"],
            "pts": s["d1_points_m"], "act": s["activation"], "force": s["tendon_force_N"],
            "paths": s["muscle_path_xy_m"], "tstar": s["t_star_N_m"], "needed": s["smallest_needed_reserve_per_joint_N_m"],
            "reserve": s["reserve_per_joint_N_m"], "status": r["status"], "summary": r["reserve_summary"],
            "verification": r["verification"], "domain_flags": len(r["force_law_domain_flags"]),
            "jumps": r["path_length_jumps"],
            "fmax": {a["name"]: a["max_isometric_force_N"] for a in r["actuators"]},
            "comparison": r.get("comparison_with_fixed_knee"),
        })
    size = (manifest.get("d1_simplification_size_gait2392") or {}).get("by_actuator")
    moving = manifest.get("knee_model") == "gait2392_moving"
    if moving:
        # Stage D3: the run's own declared list (D3's simplifications, then D2's restated for the moving knee).
        assumptions = [{"label": f"{a['source']}-{a['number']}" + (" (restated)" if a.get("restated_for_stage_d3") else ""),
                        "text": a["text"]} for a in manifest["declared_assumptions"]]
    else:
        assumptions = [{"label": f"D2-{k}", "text": t.split(". ", 1)[1] if t.split(". ", 1)[0].isdigit() else t}
                       for k, t in enumerate(manifest["configuration"]["assumptions"], 1)]
    return {"knee": "moving" if moving else "fixed",
            "decision": manifest["decision"].split(" ")[0],
            "commit": manifest["commit_sha"], "provenance": manifest["commit_provenance_status"],
            "validity": manifest["validity"], "status": manifest["status"], "d1": manifest["d1_official_manifest"],
            "oracle": manifest["oracle_reference"], "names": NAMES, "groups": GROUPS,
            "simplification_size_knee_mm": max(v["knee"] for v in size.values()) if size else None,
            "ankle_foot_size": (manifest.get("ankle_foot_simplification_size_gait2392") or {}).get("largest_by_coordinate"),
            "epsilon": (manifest.get("d2_configuration") or manifest["configuration"])["parameters"]["epsilon_reserve"]["value"],
            "assumptions": assumptions, "runs": runs}


TEMPLATE = r"""<title>LB-AO Muscle Viewer</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700&family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Same instrument-panel language as the Stage D1 viewer; muscles add one sequential effort scale. */
:root {
  --bg: #f3f5f6; --surface: #fdfefe; --ink: #13202a; --ink-2: #4a5964; --muted: #7c8a94;
  --line: #dde3e7; --axis: #b9c4cb; --accent: #0f5c8c; --ok: #1b7f4b; --flag: #b4471b;
  --ankle: #2a78d6; --knee: #eb6834; --hip: #1baf7a; --body: #13202a; --ground: #8a9aa5;
  --act-0: #d4dce1; --act-1: #c2410c; --bone: #a9b6be;
  --font-display: "Archivo", "Arial Narrow", system-ui, sans-serif;
  --font-body: "Atkinson Hyperlegible", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-data: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #11161a; --surface: #171d22; --ink: #e6edf1; --ink-2: #aab7c0; --muted: #7f8d97;
  --line: #263037; --axis: #3a4750; --accent: #6db3e3; --ok: #4cc28a; --flag: #f08a5d;
  --ankle: #3987e5; --knee: #d95926; --hip: #199e70; --body: #e6edf1; --ground: #6f808b;
  --act-0: #34414a; --act-1: #ff8a4c; --bone: #56646d; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #11161a; --surface: #171d22; --ink: #e6edf1; --ink-2: #aab7c0; --muted: #7f8d97;
  --line: #263037; --axis: #3a4750; --accent: #6db3e3; --ok: #4cc28a; --flag: #f08a5d;
  --ankle: #3987e5; --knee: #d95926; --hip: #199e70; --body: #e6edf1; --ground: #6f808b;
  --act-0: #34414a; --act-1: #ff8a4c; --bone: #56646d; color-scheme: dark }
* { box-sizing: border-box }
body { background: var(--bg); color: var(--ink); font-family: var(--font-body); font-size: 15px; line-height: 1.5; margin: 0 }
.wrap { max-width: 1160px; margin: 0 auto; padding-block: 28px 48px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 20px }
header { display: grid; gap: 8px }
.eyebrow { font-family: var(--font-data); font-size: 12px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted) }
h1 { font-family: var(--font-display); font-weight: 700; font-size: clamp(26px, 4vw, 38px); line-height: 1.1; margin: 0; text-wrap: balance; letter-spacing: -.01em }
.lede { margin: 0; max-width: 70ch; color: var(--ink-2) }
.badges { display: flex; flex-wrap: wrap; gap: 6px }
.badge { display: inline-flex; gap: 6px; align-items: center; font-size: 13px; padding: 3px 10px;
  border: 1px solid var(--line); border-radius: 999px; background: var(--surface); color: var(--ink-2) }
.badge b { font-weight: 700; color: var(--ok) } .badge b.flag { color: var(--flag) } .badge b.plain { color: var(--ink-2) }
.controls { display: flex; flex-wrap: wrap; gap: 12px 20px; align-items: center }
.seg { display: inline-flex; border: 1px solid var(--axis); border-radius: 8px; overflow: hidden; max-width: 100% }
.seg button { font: inherit; font-size: 14px; padding: 7px 12px; border: 0; background: var(--surface); color: var(--ink-2); cursor: pointer }
.seg button + button { border-left: 1px solid var(--axis) }
.seg button[aria-pressed="true"] { background: var(--ink); color: var(--surface) }
.play { font: inherit; font-weight: 700; font-size: 14px; padding: 7px 14px; border-radius: 8px; border: 1px solid var(--accent);
  background: var(--accent); color: var(--surface); cursor: pointer; min-width: 84px }
.scrub { display: flex; align-items: center; gap: 10px; flex: 1 1 260px; min-width: 0 }
.scrub input { flex: 1; min-width: 0; accent-color: var(--accent) }
.time { font-family: var(--font-data); font-variant-numeric: tabular-nums; font-size: 13px; color: var(--ink-2); white-space: nowrap }
button:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }
.main { display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 7fr); gap: 20px; align-items: start }
@media (max-width: 820px) { .main { grid-template-columns: 1fr } }
.panel { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 14px; min-width: 0 }
.panel h2 { font-family: var(--font-display); font-weight: 500; font-size: 15px; margin: 0 0 8px; letter-spacing: .01em }
.panel p.sub { margin: -4px 0 10px; font-size: 13px; color: var(--muted) }
svg { display: block; width: 100%; height: auto }
.legend { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--muted); margin-top: 6px }
.legend .ramp { flex: 0 1 160px; height: 8px; border-radius: 4px; background: linear-gradient(90deg, var(--act-0), var(--act-1)) }
.readout { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px }
.readout th, .readout td { text-align: right; padding: 4px 6px; border-bottom: 1px solid var(--line); font-variant-numeric: tabular-nums }
.readout th:first-child, .readout td:first-child { text-align: left }
.readout td { font-family: var(--font-data) } .readout td:first-child { font-family: var(--font-body) }
.readout thead th { color: var(--muted); font-weight: 400; font-size: 12px }
.readout tr.group td { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .05em; font-family: var(--font-data); padding-top: 8px; border-bottom: 0 }
.bar { display: inline-block; height: 8px; border-radius: 2px; vertical-align: middle; margin-right: 6px }
.right { display: grid; gap: 14px }
.heat-wrap { position: relative }
.heat-labels { font-size: 12px }
.reserve-note { font-size: 13px; color: var(--ink-2); margin: 6px 0 0 }
.chips { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 12px; color: var(--ink-2); margin: 0 0 6px }
.chips span { display: inline-flex; align-items: center; gap: 6px }
.chips i { width: 14px; height: 3px; border-radius: 2px; display: inline-block }
.lower { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; align-items: start }
.facts { display: grid; grid-template-columns: auto 1fr; gap: 4px 14px; font-size: 13px; margin: 0 }
.facts dt { color: var(--muted) }
.facts dd { margin: 0; font-family: var(--font-data); font-variant-numeric: tabular-nums; min-width: 0; overflow-wrap: anywhere }
.pill { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 12px; font-family: var(--font-body); font-weight: 700 }
.pill.ok { color: var(--ok); border: 1px solid var(--ok) } .pill.flag { color: var(--flag); border: 1px solid var(--flag) }
.notes { margin: 0; padding-left: 18px; font-size: 13px; color: var(--ink-2); display: grid; gap: 4px }
#assump { list-style: none; padding-left: 0; margin-top: 6px }
#assump .tag { font-family: var(--font-data); font-size: 11px; color: var(--muted); margin-right: 6px; white-space: nowrap }
details { font-size: 13px; color: var(--ink-2) } summary { cursor: pointer; color: var(--accent) }
footer { font-size: 12px; color: var(--muted); display: grid; gap: 4px }
footer code { font-family: var(--font-data); overflow-wrap: anywhere } footer a { color: var(--accent) }
</style>

<div class="wrap">
  <header>
    <div class="eyebrow" id="eyebrow">Independent Study · LB-AO · Phase D, Stage D2</div>
    <h1>Which muscles do the work in a squat</h1>
    <p class="lede">The same side-view squat as Stage D1, now with 14 leg muscles from the OpenSim Gait2392 model. At each instant the model finds the least total muscle effort that still produces the joint torques the squat needs. Where the muscles cannot, a labelled “reserve” torque makes up the gap, and the page says so.</p>
    <div class="badges" id="badges"></div>
  </header>

  <div class="controls" role="group" aria-label="Playback">
    <div class="seg" id="bodies" role="group" aria-label="Body"></div>
    <div class="seg" id="knees" role="group" aria-label="Knee model" hidden></div>
    <button class="play" id="play" type="button">Pause</button>
    <div class="scrub"><input id="scrub" type="range" min="0" max="300" value="0" aria-label="Time"><span class="time" id="time"></span></div>
  </div>

  <div class="main">
    <section class="panel" aria-label="Figure with muscles">
      <h2>Side view (facing right), muscles coloured by effort</h2>
      <svg id="figure" viewBox="0 0 400 460" role="img" aria-label="Stick figure with muscle lines"></svg>
      <div class="legend"><span>Activation 0</span><span class="ramp"></span><span>1 (fully active)</span></div>
      <table class="readout" aria-label="Muscle values at the current time">
        <thead><tr><th>Muscle</th><th>Activation</th><th>Force</th></tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </section>
    <div class="right">
      <section class="panel" aria-label="Activation over time">
        <h2>Activation of each muscle over the squat</h2>
        <p class="sub">Darker means harder working. Down for 1.5 s, up for 1.5 s. Click or drag to move in time.</p>
        <div class="heat-wrap"><svg id="heat" role="img" aria-label="Activation heat map, one row per muscle"></svg></div>
      </section>
      <section class="panel" aria-label="Muscle forces">
        <h2>Muscle force (N), the five largest for this body</h2>
        <div class="chips" id="forces-legend"></div>
        <svg id="forces" role="img" aria-label="Force over time for the five strongest-working muscles"></svg>
      </section>
      <section class="panel" aria-label="Reserve torque">
        <h2>Reserve torque: what the muscles could not supply</h2>
        <div class="chips" id="reserve-legend"></div>
        <svg id="reserve" role="img" aria-label="Smallest reserve torque needed at each joint over time"></svg>
        <p class="reserve-note" id="reserve-note"></p>
      </section>
    </div>
  </div>

  <div class="lower">
    <section class="panel"><h2>Checks for this body</h2><dl class="facts" id="checks"></dl></section>
    <section class="panel"><h2>Can the muscles do it?</h2><dl class="facts" id="feas"></dl></section>
    <section class="panel"><h2>What this model is, and is not</h2>
      <ul class="notes" id="isnot"></ul>
      <details><summary id="assump-summary">Declared simplifications</summary><ul class="notes" id="assump"></ul></details>
    </section>
  </div>
  <footer id="foot"></footer>
</div>

<script>
const DATA = __DATA__;
const JOINTS = [["ankle","Ankle"],["knee","Knee"],["hip","Hip"]];
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const svgNS = "http://www.w3.org/2000/svg";
const el = (tag, attrs, parent) => { const e = document.createElementNS(svgNS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const fmt = (v, d=1) => (v < 0 && Math.abs(v) >= 0.5 * 10 ** -d ? "−" : "") + Math.abs(v).toFixed(d);
const ORDER = DATA.groups.flatMap(g => g[1]);
let V = DATA.moving || DATA;
let run = V.runs[0], i = 0, playing = !matchMedia("(prefers-reduced-motion: reduce)").matches, last = null;
const N = () => run.t.length;

// sequential effort colour: mix --act-0 -> --act-1
function hex(c) { c = c.replace("#", ""); return [0, 2, 4].map(k => parseInt(c.slice(k, k + 2), 16)); }
function actColor(a) { const p = hex(css("--act-0")), q = hex(css("--act-1")); const t = Math.max(0, Math.min(1, a));
  return `rgb(${p.map((v, k) => Math.round(v + (q[k] - v) * t)).join(",")})`; }

const seg = document.getElementById("bodies");
V.runs.forEach((r, k) => {
  const b = document.createElement("button"); b.type = "button"; b.textContent = r.label; b.setAttribute("aria-pressed", k === 0);
  b.onclick = () => { run = V.runs[k]; [...seg.children].forEach(x => x.setAttribute("aria-pressed", x === b)); rebuild(); };
  seg.appendChild(b);
});
if (DATA.moving) {
  const ks = document.getElementById("knees"); ks.hidden = false;
  [["moving", "Moving knee (Gait2392)"], ["fixed", "Fixed knee (D1)"]].forEach(([key, label]) => {
    const b = document.createElement("button"); b.type = "button"; b.textContent = label; b.setAttribute("aria-pressed", key === V.knee);
    b.onclick = () => { const k = V.runs.indexOf(run); V = key === "moving" ? DATA.moving : DATA; run = V.runs[k];
      [...ks.children].forEach(x => x.setAttribute("aria-pressed", x === b)); header(); rebuild(); };
    ks.appendChild(b);
  });
}

// ---- figure
const fig = document.getElementById("figure");
const S = 210, X0 = 150, Y0 = 385;
const px = (x, y) => [X0 + S * x, Y0 - S * y];
function drawFigure() {
  const r = run, p = r.pts, f = r.foot; fig.replaceChildren();
  const gy = f.ground_y_m, [gx1, gy1] = px(-0.7, gy), [gx2] = px(1.2, gy);
  el("line", {x1: gx1, y1: gy1, x2: gx2, y2: gy1, stroke: css("--ground"), "stroke-width": 1.5}, fig);
  const ank = px(0, 0), heel = px(f.heel_m[0], f.heel_m[1]), ball = px(f.ball_m[0], f.ball_m[1]);
  el("polygon", {points: [ank, heel, ball].map(q => q.join(",")).join(" "), fill: "none", stroke: css("--bone"), "stroke-width": 3, "stroke-linejoin": "round"}, fig);
  const k = px(p.knee.x[i], p.knee.y[i]), h = px(p.hip.x[i], p.hip.y[i]), top = px(p.hat_drawing_top.x[i], p.hat_drawing_top.y[i]);
  el("polyline", {points: [ank, k, h].map(q => q.join(",")).join(" "), fill: "none", stroke: css("--bone"), "stroke-width": 6, "stroke-linecap": "round", "stroke-linejoin": "round"}, fig);
  el("line", {x1: h[0], y1: h[1], x2: top[0], y2: top[1], stroke: css("--bone"), "stroke-width": 8, "stroke-linecap": "round"}, fig);
  el("circle", {cx: top[0], cy: top[1] - 14, r: 13, fill: "none", stroke: css("--bone"), "stroke-width": 3}, fig);
  // muscles: least active first so working muscles draw on top
  const order = ORDER.map((m, k) => [m, k]).sort((a, b) => r.act[a[0]][i] - r.act[b[0]][i]);
  for (const [m] of order) {
    const pts = r.paths[i][ORDER.indexOf(m)].map(([x, y]) => px(x, y).join(",")).join(" ");
    const a = r.act[m][i];
    el("polyline", {points: pts, fill: "none", stroke: actColor(a), "stroke-width": 2 + 3 * a, "stroke-linecap": "round", "stroke-linejoin": "round", opacity: 0.95}, fig);
  }
  JOINTS.forEach(([j], n) => { const at = [ank, k, h][n]; el("circle", {cx: at[0], cy: at[1], r: 5, fill: css("--" + j), stroke: css("--surface"), "stroke-width": 2}, fig); });
  const lbl = el("text", {x: 12, y: 18, "font-size": 11, fill: css("--muted"), "font-family": css("--font-data")}, fig);
  lbl.textContent = `${r.label}: ${r.mass} kg, ${r.stature} m`;
  if (r.tstar[i] > V.epsilon) {
    const w = el("text", {x: 12, y: 36, "font-size": 12, "font-weight": 700, fill: css("--flag"), "font-family": css("--font-body")}, fig);
    w.textContent = `Muscles short by ${r.tstar[i].toFixed(1)} N·m here`;
  }
}

function drawRows() {
  const r = run;
  document.getElementById("rows").innerHTML = DATA.groups.map(([g, ms]) =>
    `<tr class="group"><td colspan="3">${g}</td></tr>` + ms.map(m => {
      const a = r.act[m][i], F = r.force[m][i];
      return `<tr><td>${DATA.names[m]}</td><td><span class="bar" style="width:${Math.round(40 * a)}px;background:${actColor(a)}"></span>${a.toFixed(2)}</td><td>${Math.round(F)} N</td></tr>`;
    }).join("")).join("");
  document.getElementById("time").textContent = `${r.t[i].toFixed(2)} s / ${r.t[N() - 1].toFixed(1)} s`;
  document.getElementById("scrub").value = i;
}

// ---- heat map
let cursors = [];
function timeAxis(svg, W, H, L, R, B, tmax) {
  for (let s = 0; s <= tmax + 1e-9; s += 0.5) {
    const x = L + (W - L - R) * s / tmax;
    const t = el("text", {x, y: H - 6, "text-anchor": "middle", "font-size": 11, fill: css("--muted"), "font-family": css("--font-data")}, svg);
    t.textContent = s.toFixed(1) + (s === 0 ? " s" : "");
  }
}
function addCursor(svg, L, R, W, T, B, H, tmax) {
  const cur = el("line", {y1: T, y2: H - B, stroke: css("--ink"), "stroke-width": 1.2, "stroke-dasharray": "3 3"}, svg);
  const hit = el("rect", {x: L, y: 0, width: W - L - R, height: H, fill: "transparent", style: "cursor: crosshair"}, svg);
  const pick = ev => { const b = svg.getBoundingClientRect(); const x = (ev.clientX - b.left) / b.width * W;
    i = Math.max(0, Math.min(N() - 1, Math.round((x - L) / (W - L - R) * (N() - 1)))); playing = false; syncPlay(); frame(); };
  hit.addEventListener("pointerdown", ev => { pick(ev); hit.setPointerCapture(ev.pointerId); });
  hit.addEventListener("pointermove", ev => { if (ev.buttons) pick(ev); });
  cursors.push(k => { const x = L + (W - L - R) * run.t[k] / tmax; cur.setAttribute("x1", x); cur.setAttribute("x2", x); });
}
function buildHeat() {
  const svg = document.getElementById("heat"); svg.replaceChildren();
  const W = Math.max(320, Math.round(svg.parentElement.clientWidth || 640));
  const narrow = W < 520, L = narrow ? 132 : 150, R = 16, T = 4, B = 22, rh = 14, gap = 6;
  const groupsH = DATA.groups.length * gap;
  const H = T + ORDER.length * rh + groupsH + B;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const t = run.t, tmax = t[t.length - 1], cw = (W - L - R) / t.length;
  let y = T;
  DATA.groups.forEach(([g, ms]) => {
    y += gap;
    ms.forEach(m => {
      const lab = el("text", {x: L - 6, y: y + rh - 3, "text-anchor": "end", "font-size": narrow ? 10 : 12, fill: css("--ink-2")}, svg);
      lab.textContent = DATA.names[m];
      const a = run.act[m];
      for (let k = 0; k < t.length; k++)
        el("rect", {x: (L + k * cw).toFixed(2), y, width: (cw + 0.6).toFixed(2), height: rh - 2, fill: actColor(a[k])}, svg);
      y += rh;
    });
  });
  timeAxis(svg, W, H, L, R, B, tmax);
  addCursor(svg, L, R, W, T, B, H, tmax);
}

function lineChart(svgId, series, unit, opts={}) {
  const svg = document.getElementById(svgId); svg.replaceChildren();
  const W = Math.max(320, Math.round(svg.parentElement.clientWidth || 640)), H = opts.H || 170, L = 46, R = 16, T = 10, B = 22;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const t = run.t, tmax = t[t.length - 1];
  const peak = Math.max(opts.minTop || 0, ...series.flatMap(s => s.y));
  const step = [1, 2, 5, 10, 20, 50, 100, 200, 250, 500, 1000].find(s => peak / s <= 4) || 1000;
  const top = Math.max(step, Math.ceil(peak / step) * step);
  const xs = v => L + (W - L - R) * v / tmax, ys = v => T + (H - T - B) * (1 - v / top);
  for (let v = 0; v <= top + 1e-9; v += step) {
    el("line", {x1: L, x2: W - R, y1: ys(v), y2: ys(v), stroke: v === 0 ? css("--axis") : css("--line"), "stroke-width": 1}, svg);
    const tx = el("text", {x: L - 6, y: ys(v) + 4, "text-anchor": "end", "font-size": 11, fill: css("--muted"), "font-family": css("--font-data")}, svg);
    tx.textContent = v;
  }
  if (opts.threshold !== undefined) {
    el("line", {x1: L, x2: W - R, y1: ys(opts.threshold), y2: ys(opts.threshold), stroke: css("--flag"), "stroke-width": 1, "stroke-dasharray": "5 4"}, svg);
    const tx = el("text", {x: W - R, y: ys(opts.threshold) - 4, "text-anchor": "end", "font-size": 11, fill: css("--flag"), "font-family": css("--font-data")}, svg);
    tx.textContent = opts.thresholdLabel;
  }
  timeAxis(svg, W, H, L, R, B, tmax);
  const dots = [];
  series.forEach(s => {
    const d = s.y.map((v, k) => `${k ? "L" : "M"}${xs(t[k]).toFixed(1)},${ys(v).toFixed(1)}`).join("");
    el("path", {d, fill: "none", stroke: s.color, "stroke-width": s.width || 2, "stroke-linejoin": "round", "stroke-dasharray": s.dash || ""}, svg);
    dots.push({s, dot: el("circle", {r: 3.5, fill: s.color, stroke: css("--surface"), "stroke-width": 1.5}, svg)});
  });
  if (opts.legend) document.getElementById(opts.legend).innerHTML =
    series.map(s => `<span><i style="background:${s.color}${s.dash ? ";opacity:.7" : ""}"></i>${s.label}</span>`).join("") + (opts.legendNote || "");
  addCursor(svg, L, R, W, T, B, H, tmax);
  cursors.push(k => dots.forEach(({s, dot}) => { dot.setAttribute("cx", xs(t[k])); dot.setAttribute("cy", ys(s.y[k])); }));
}
function buildForces() {
  const top5 = ORDER.map(m => [m, Math.max(...run.force[m])]).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const shades = ["--act-1", "--knee", "--hip", "--ankle", "--accent"];
  lineChart("forces", top5.map(([m], k) => ({y: run.force[m], label: DATA.names[m], color: css(shades[k])})), "N", {legend: "forces-legend"});
}
function buildReserve() {
  const s = JOINTS.map(([j, name], k) => ({y: run.needed[j], label: name, color: css("--" + j), width: 4 - k * 1.2}));
  const same = JOINTS.every(([j]) => run.needed[j].every((v, k) => Math.abs(v - run.needed.knee[k]) < 1e-3));
  lineChart("reserve", s, "N·m", {H: 130, minTop: 2 * V.epsilon, threshold: V.epsilon, thresholdLabel: `allowance ${V.epsilon} N·m`,
    legend: "reserve-legend", legendNote: same && run.summary.t_star_max_N_m > 0 ? `<span>(the three lines coincide)</span>` : ""});
  const sm = run.summary;
  document.getElementById("reserve-note").innerHTML = run.status.muscle_feasibility === "feasible"
    ? `The muscles supply the whole torque at every instant for this body (largest reserve ${sm.t_star_max_N_m.toFixed(3)} N·m)` +
      (V.knee === "moving" && run.comparison ? `. With D1's fixed knee it was ${run.comparison.t_star_max_N_m.fixed.toFixed(1)} N·m.` : ".")
    : `Around the bottom (${sm.flagged_time_range_s.map(x => x.toFixed(2)).join("–")} s) the muscles fall short by up to <b>${sm.t_star_max_N_m.toFixed(1)} N·m</b>; limiting: ${sm.limiting_joints_at_t_star_max.join(", ")} (coupled through two-joint muscles). Lines show the least reserve each joint needs. <b>This shortfall comes from D1's simplified knee:</b> with Gait2392's own moving knee the same muscles suffice (${DATA.moving ? "switch to the moving knee above" : "sensitivity analysis"}).`;
}

function facts() {
  const v = run.verification, st = run.status;
  const pill = (ok, a, b) => ok ? `<span class="pill ok">${a}</span>` : `<span class="pill flag">${b}</span>`;
  document.getElementById("checks").innerHTML = `
    <dt>Optimizer</dt><dd>${pill(st.optimizer_verification === "passed", "pass", "fail")} KKT residual ${v.largest_kkt_residual.toExponential(1)}</dd>
    <dt>Second solver</dt><dd>activations within ${v.second_solver_activation_difference.toExponential(1)}</dd>
    ${st.kinematics_verification ? `<dt>Moving-knee mechanics</dt><dd>${pill(st.mechanics_verification === "passed", "pass", "fail")} two formulations agree</dd>
    <dt>Kinematics vs OpenSim</dt><dd>${pill(st.kinematics_verification === "passed", "pass", "fail")} within ${v.kinematics_oracle_error_m.toExponential(1)} m</dd>`
    : `<dt>Uses D1's torques</dt><dd>${pill(st.d1_consistency === "passed", "pass", "fail")} difference ${v.d1_torque_difference_N_m.toExponential(1)} N·m</dd>`}
    <dt>Force-curve range</dt><dd>${pill(st.force_law_domain === "in_domain", "in range", "flagged")} ${run.domain_flags} flagged samples</dd>
    <dt>Geometry vs OpenSim</dt><dd>checked in the test suite (OpenSim ${V.oracle.opensim_version})</dd>
    <dt>${st.kinematics_verification ? "Foot contact" : "D1 mechanics"}</dt><dd>${st.kinematics_verification ? pill(st.contact_feasibility === "feasible", "feasible", "flagged") + (run.comparison ? ` heel margin ${(run.comparison.heel_margin_min_m.moving * 1000).toFixed(0)} mm (fixed knee ${(run.comparison.heel_margin_min_m.fixed * 1000).toFixed(0)} mm)` : "") : pill(st.mechanics_verification === "passed", "pass", "fail") + ` contact ${st.contact_feasibility}`}</dd>`;
  const sm = run.summary;
  document.getElementById("feas").innerHTML = `
    <dt>Status</dt><dd>${pill(st.muscle_feasibility === "feasible", "feasible throughout", "short of torque")}</dd>
    ${sm.t_star_max_N_m > 0 ? `<dt>Largest shortfall</dt><dd>${sm.t_star_max_N_m.toFixed(2)} N·m at ${sm.t_star_max_time_s.toFixed(2)} s</dd>
    <dt>Pose then</dt><dd>ankle ${sm.q_at_t_star_max_deg[0].toFixed(0)}°, knee ${sm.q_at_t_star_max_deg[1].toFixed(0)}°, hip ${sm.q_at_t_star_max_deg[2].toFixed(0)}°</dd>` : `<dt>Largest shortfall</dt><dd>none</dd>`}
    ${run.comparison ? `<dt>With D1's fixed knee</dt><dd>${run.comparison.t_star_max_N_m.fixed.toFixed(2)} N·m shortfall; peak knee torque ${run.comparison.peak_knee_torque_N_m.fixed.toFixed(1)} → ${run.comparison.peak_knee_torque_N_m.moving.toFixed(1)} N·m</dd>` : ""}
    <dt>Flagged time</dt><dd>${sm.flagged_time_range_s ? sm.flagged_time_range_s.map(x => x.toFixed(2)).join("–") + " s (" + sm.flagged_samples + " samples)" : "none"}</dd>
    <dt>Allowance</dt><dd>${sm.epsilon_reserve_N_m} N·m per joint (a demonstration choice)</dd>`;
}

function frame() { drawFigure(); drawRows(); cursors.forEach(c => c(i)); }
function rebuild() { cursors = []; buildHeat(); buildForces(); buildReserve(); facts(); frame(); }
const playBtn = document.getElementById("play");
function syncPlay() { playBtn.textContent = playing ? "Pause" : "Play"; }
playBtn.onclick = () => { playing = !playing; if (playing && i >= N() - 1) i = 0; syncPlay(); };
document.getElementById("scrub").addEventListener("input", e => { i = +e.target.value; playing = false; syncPlay(); frame(); });
function tick(ts) {
  if (playing) { if (last === null) last = ts; const dt = (ts - last) / 1000; last = ts;
    const step = run.t[1] - run.t[0], adv = Math.floor(dt / step);
    if (adv > 0) { i = (i + adv) % N(); last = ts - (dt - adv * step) * 1000; frame(); } } else last = null;
  requestAnimationFrame(tick);
}
document.getElementById("scrub").max = N() - 1;
function header() {
const st = V.status, fv = V.validity;
document.getElementById("eyebrow").textContent = `Independent Study · LB-AO · Phase D, Stage ${V.knee === "moving" ? "D3 (moving knee)" : "D2"}`;
document.getElementById("badges").innerHTML = [
  st.optimizer_verification === "passed" ? `<b>Computation verified</b> against OpenSim and a second solver` : `<b class="flag">Verification FAILED</b>`,
  (DATA.moving ? (V.knee === "moving" ? "Moving knee: " : "Fixed knee: ") : "") +
  V.runs.map(r => `${r.label.split(" ")[0]}: ` + (r.status.muscle_feasibility === "feasible" ? `<b>muscles suffice</b>` : `<b class="flag">short at the bottom</b>`)).join(" · "),
  `<b class="plain">Sources provisional</b>`, `not validated against measured muscle activity`].map(x => `<span class="badge">${x}</span>`).join("");
const maxJump = Math.max(...V.runs.flatMap(r => r.jumps.map(j => Math.abs(j.length_with_point_minus_without_mm))));
const af = V.ankle_foot_size;
const kneeNote = V.knee === "moving"
  ? `In this view both the joint torques and the muscle paths use Gait2392's own knee, whose centre slides about 6 mm forward and 21 mm down as it bends (a model fit, not measured motion). The squat motion itself is D1's, unchanged. With D1's fixed knee the male and Gait2392 bodies came up short near the bottom; with this knee they do not. Path switches change muscle lengths by at most ${maxJump.toFixed(2)} mm` +
    (af ? `, and the remaining ankle and foot simplifications change moment arms by up to ${af.ankle.mm.toFixed(1)} mm (${DATA.names[af.ankle.actuator]}, at the ankle).` : ".")
  : `D1's simplified knee (a fixed hinge) changes knee moment arms by up to ${(DATA.simplification_size_knee_mm || 0).toFixed(0)} mm compared with Gait2392's moving knee, and some muscle paths jump by up to ${maxJump.toFixed(1)} mm where a path point switches on or off. Both are reported, not hidden.`;
document.getElementById("isnot").innerHTML = [
  "The checks show the stated model is computed correctly (geometry and forces match OpenSim to machine precision; the recruitment rule is solved exactly). They do not show real muscles work this way: no comparison with measured muscle activity.",
  "“Least total effort” is a modelling rule, not a law of physiology. It predicts no co-contraction unless the torques and the available muscles force it. Near standing they do, a little: rectus femoris is the only hip flexor among the 14 muscles (iliopsoas is left out) and it also extends the knee, so the gastrocnemius offsets that and the tibialis anterior offsets the gastrocnemius at the ankle.",
  "Tendons are treated as rigid and passive muscle stretch is left out; both matter most for the calf muscles.",
  "Muscle strengths and paths come from the Gait2392 model, built for walking. The female and male bodies share its generic strengths, scaled in size only, not in strength.",
  kneeNote,
].map(x => `<li>${x}</li>`).join("");
const esc = x => String(x).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"})[c]);
document.getElementById("assump").innerHTML = V.assumptions.map(a => `<li><span class="tag">${esc(a.label)}</span>${esc(a.text)}</li>`).join("");
document.getElementById("assump-summary").textContent = `All ${V.assumptions.length} declared simplifications (${V.knee === "moving" ? "Stage D3, moving knee" : "Stage D2, fixed knee"})`;
const statusLine = Object.entries(st).map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`).join("; ");
document.getElementById("foot").innerHTML = `
  <div>${fv.kind.charAt(0).toUpperCase() + fv.kind.slice(1)}. Physiological validity: ${fv.physiological_validity}. Clinical validity: ${fv.clinical_validity}.</div>
  <div>Status (${V.knee} knee): ${statusLine}.</div>
  <div>${V.knee === "moving" ? "D3" : "D2"} run manifest at commit <code>${V.commit.slice(0, 12)}</code> · provenance <code>${V.provenance}</code> · decision ${V.decision} · official D1 run <code>${V.d1.commit_sha.slice(0, 12)}</code>${DATA.moving && V.knee === "moving" ? ` · compared with the fixed-knee D2 run <code>${DATA.commit.slice(0, 12)}</code>` : ""}.</div>
  <div>Sources: OpenSim Gait2392 muscle parameters, paths and knee, <a href="https://github.com/opensim-org/opensim-models" target="_blank" rel="noopener">opensim-org/opensim-models</a> (CC BY 3.0); muscle curves of De Groote et al. (2016) as implemented in <a href="https://github.com/opensim-org/opensim-core" target="_blank" rel="noopener">opensim-core</a> (Apache-2.0); segment data of de Leva (1996) via BMClab/BMC (CC BY 4.0); anatomy from StatPearls.</div>`;
}
header();
syncPlay(); rebuild(); requestAnimationFrame(tick);
let rw = 0; addEventListener("resize", () => { const w = document.getElementById("heat").parentElement.clientWidth; if (Math.abs(w - rw) > 4) { rw = w; rebuild(); } });
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", rebuild);
new MutationObserver(rebuild).observe(document.documentElement, {attributes: true, attributeFilter: ["data-theme"]});
</script>
"""


def render(manifest, moving=None):
    data = compact(manifest)
    if moving is not None:
        data["moving"] = compact(moving)
    data = json.dumps(data, separators=(",", ":"), allow_nan=False)
    return TEMPLATE.replace("__DATA__", data.replace("</", "<\\/"))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--moving-manifest", type=Path, help="Stage D3 manifest: adds the knee switch (D-060 item 7)")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    moving = json.loads(args.moving_manifest.read_text(encoding="utf-8")) if args.moving_manifest else None
    args.output.write_text(render(manifest, moving), encoding="utf-8")
    print("Page written to", args.output)


if __name__ == "__main__":
    main()
