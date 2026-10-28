"""Build the Stage D1 squat viewer: one self-contained HTML page from a run manifest (D-058 item 11).

    python -m tools.build_squat_page --manifest results/phase_d/<file>.json --output results/phase_d/<file>.html

Presentation only: every number on the page is copied from the manifest. The page plays
the squat as a stick figure beside the per-leg joint-torque curves, and states the
manifest's validity statement, commit and sources.
"""
import argparse
import json
from pathlib import Path

LABELS = {"female": "Female (de Leva)", "male": "Male (de Leva)", "gait2392": "Gait2392 reference"}


def compact(manifest):
    runs = []
    for r in manifest["runs"]:
        s = r["series"]
        runs.append({
            "body": r["body"], "label": LABELS.get(r["body"], r["body"]),
            "mass": r["body_mass_kg"], "stature": r["stature_m"],
            "t": s["t_s"], "q": s["q_rad"], "tau": s["tau_per_leg_N_m"], "grf": s["grf_per_leg_N"],
            "cop": s["cop_x_m"], "pts": s["points_m"], "foot": r["foot"],
            "contact": r["contact"], "checks": r["checks"], "status": r["status"],
        })
    return {"commit": manifest["commit_sha"], "provenance": manifest["commit_provenance_status"],
            "validity": manifest["validity"], "status": manifest["status"],
            "source_validation": manifest["source_validation"], "runs": runs}


TEMPLATE = r"""<title>LB-AO Squat Viewer</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700&family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: a lab instrument panel. Figure on the left, three torque traces on the right, findings below. */
:root {
  --bg: #f3f5f6; --surface: #fdfefe; --ink: #13202a; --ink-2: #4a5964; --muted: #7c8a94;
  --line: #dde3e7; --axis: #b9c4cb; --accent: #0f5c8c; --ok: #1b7f4b; --flag: #b4471b;
  --ankle: #2a78d6; --knee: #eb6834; --hip: #1baf7a; --body: #13202a; --ground: #8a9aa5;
  --font-display: "Archivo", "Arial Narrow", system-ui, sans-serif;
  --font-body: "Atkinson Hyperlegible", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-data: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #11161a; --surface: #171d22; --ink: #e6edf1; --ink-2: #aab7c0; --muted: #7f8d97;
  --line: #263037; --axis: #3a4750; --accent: #6db3e3; --ok: #4cc28a; --flag: #f08a5d;
  --ankle: #3987e5; --knee: #d95926; --hip: #199e70; --body: #e6edf1; --ground: #6f808b; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #11161a; --surface: #171d22; --ink: #e6edf1; --ink-2: #aab7c0; --muted: #7f8d97;
  --line: #263037; --axis: #3a4750; --accent: #6db3e3; --ok: #4cc28a; --flag: #f08a5d;
  --ankle: #3987e5; --knee: #d95926; --hip: #199e70; --body: #e6edf1; --ground: #6f808b; color-scheme: dark }
* { box-sizing: border-box }
body { background: var(--bg); color: var(--ink); font-family: var(--font-body); font-size: 15px; line-height: 1.5 }
.wrap { max-width: 1120px; margin: 0 auto; padding-block: 28px 48px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 20px }
header { display: grid; gap: 8px }
.eyebrow { font-family: var(--font-data); font-size: 12px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted) }
h1 { font-family: var(--font-display); font-weight: 700; font-size: clamp(26px, 4vw, 38px); line-height: 1.1; margin: 0; text-wrap: balance; letter-spacing: -.01em }
.lede { margin: 0; max-width: 68ch; color: var(--ink-2) }
.badge { justify-self: start; display: inline-flex; gap: 8px; align-items: center; font-size: 13px; padding: 4px 10px;
  border: 1px solid var(--line); border-radius: 999px; background: var(--surface); color: var(--ink-2) }
.badge b { color: var(--ok); font-weight: 700 }
.badge b.flag { color: var(--flag) }
.badge b.prov { color: var(--ink-2) }
.controls { display: flex; flex-wrap: wrap; gap: 12px 20px; align-items: center }
.seg { display: inline-flex; border: 1px solid var(--axis); border-radius: 8px; overflow: hidden }
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
@media (max-width: 760px) { .main { grid-template-columns: 1fr } }
.panel { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 14px; min-width: 0 }
.panel h2 { font-family: var(--font-display); font-weight: 500; font-size: 15px; margin: 0 0 8px; letter-spacing: .01em }
.stage svg, .chart svg { display: block; width: 100%; height: auto }
.charts { display: grid; gap: 10px }
.chart { position: relative }
.chart-head { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; font-size: 13px }
.chart-head .name { font-weight: 700; display: inline-flex; align-items: center; gap: 6px }
.swatch { width: 14px; height: 3px; border-radius: 2px; display: inline-block }
.chart-head .val { font-family: var(--font-data); font-variant-numeric: tabular-nums; color: var(--ink) }
.chart-head .hint { color: var(--muted); font-size: 12px }
.readout { width: 100%; border-collapse: collapse; font-size: 13px }
.readout th, .readout td { text-align: right; padding: 5px 8px; border-bottom: 1px solid var(--line); font-variant-numeric: tabular-nums }
.readout th:first-child, .readout td:first-child { text-align: left }
.readout td { font-family: var(--font-data) }
.readout thead th { color: var(--muted); font-weight: 400; font-size: 12px }
.lower { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; align-items: start }
.facts { display: grid; grid-template-columns: auto 1fr; gap: 4px 14px; font-size: 13px; margin: 0 }
.facts dt { color: var(--muted) }
.facts dd { margin: 0; font-family: var(--font-data); font-variant-numeric: tabular-nums; min-width: 0; overflow-wrap: anywhere }
.pill { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 12px; font-family: var(--font-body); font-weight: 700 }
.pill.ok { color: var(--ok); border: 1px solid var(--ok) }
.pill.flag { color: var(--flag); border: 1px solid var(--flag) }
.notes { margin: 0; padding-left: 18px; font-size: 13px; color: var(--ink-2); display: grid; gap: 4px }
footer { font-size: 12px; color: var(--muted); display: grid; gap: 4px }
footer code { font-family: var(--font-data); overflow-wrap: anywhere }
footer a { color: var(--accent) }
.tip { position: absolute; pointer-events: none; font-family: var(--font-data); font-size: 12px; padding: 3px 6px; border-radius: 4px;
  background: var(--ink); color: var(--surface); transform: translate(-50%, -110%); white-space: nowrap }
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto } }
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">Independent Study · LB-AO · Phase D, Stage D1</div>
    <h1>A bodyweight squat, joint by joint</h1>
    <p class="lede">A side-view model of one leg carrying half the upper body. The squat motion is prescribed; the model works out the torque each joint must produce, per leg, and where the ground pushes back under the foot.</p>
    <div class="badge" id="badge"></div>
  </header>

  <div class="controls" role="group" aria-label="Playback">
    <div class="seg" id="bodies" role="group" aria-label="Body"></div>
    <button class="play" id="play" type="button">Pause</button>
    <div class="scrub"><input id="scrub" type="range" min="0" max="300" value="0" aria-label="Time"><span class="time" id="time"></span></div>
  </div>

  <div class="main">
    <section class="panel stage" aria-label="Stick figure">
      <h2>Side view (facing right)</h2>
      <svg id="figure" viewBox="0 0 400 440" role="img" aria-label="Stick figure of the squat"></svg>
      <table class="readout" aria-label="Values at the current time">
        <thead><tr><th>Joint</th><th>Angle</th><th>Torque per leg</th><th>per kg</th></tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </section>
    <section class="panel" aria-label="Joint torques">
      <h2>Joint torque per leg (N·m). Positive: flexion (dorsiflexion at the ankle). Negative: extension (plantarflexion).</h2>
      <div class="charts" id="charts"></div>
    </section>
  </div>

  <div class="lower">
    <section class="panel"><h2>Mechanics checks for this body</h2><dl class="facts" id="checks"></dl></section>
    <section class="panel"><h2>Foot contact</h2><dl class="facts" id="contact"></dl></section>
    <section class="panel"><h2>What this model is, and is not</h2>
      <ul class="notes">
        <li>The checks show the equations are solved correctly for an idealized model. They do not validate it against measured squats.</li>
        <li>The squat motion is a demonstration, chosen so the foot stays balanced; it is not taken from motion capture.</li>
        <li>Segment masses and proportions: de Leva (1996) for the female and male bodies, scaled to their height from the OpenSim Gait2392 geometry; Gait2392 as published for the reference body. The de Leva values are provisional: two independent copies agree, but they have not been checked against the paper.</li>
        <li>The largest uncertainties: Gait2392's true height (1.8 m documented, about 1.66 m measured by one user) changes knee torque by about 9%, and where the knee centre sits changes it by about 8%. Details in the sensitivity analysis.</li>
        <li>No muscles yet. A net joint torque is the sum of everything acting at the joint (Stage D2 adds muscles).</li>
        <li>The upper body is drawn as a line through its centre of mass, for illustration only.</li>
      </ul>
    </section>
  </div>

  <footer id="foot"></footer>
</div>

<script>
const DATA = __DATA__;
const JOINTS = [["ankle","Ankle"],["knee","Knee"],["hip","Hip"]];
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
let run = DATA.runs[0], i = 0, playing = !matchMedia("(prefers-reduced-motion: reduce)").matches, last = null;
const N = () => run.t.length;
const svgNS = "http://www.w3.org/2000/svg";
const el = (tag, attrs, parent) => { const e = document.createElementNS(svgNS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const fmt = (v, d=1) => (v < 0 ? "−" : "") + Math.abs(v).toFixed(d);

// ---- body selector
const seg = document.getElementById("bodies");
DATA.runs.forEach((r, k) => {
  const b = document.createElement("button"); b.type = "button"; b.id = "body-" + r.body;
  b.textContent = r.label; b.setAttribute("aria-pressed", k === 0);
  b.onclick = () => { run = r; [...seg.children].forEach(x => x.setAttribute("aria-pressed", x === b)); buildCharts(); facts(); draw(); };
  seg.appendChild(b);
});

// ---- figure: world metres -> svg pixels, fixed scale across bodies so sizes compare honestly
const fig = document.getElementById("figure");
const S = 210, X0 = 150, Y0 = 370;  // px per metre, ankle position
const px = (x, y) => [X0 + S * x, Y0 - S * y];
function draw() {
  const r = run, p = r.pts, f = r.foot;
  fig.replaceChildren();
  const gy = f.ground_y_m;
  const [gx1, gy1] = px(-0.7, gy), [gx2] = px(1.2, gy);
  el("line", {x1: gx1, y1: gy1, x2: gx2, y2: gy1, stroke: css("--ground"), "stroke-width": 1.5}, fig);
  for (let x = -0.6; x < 1.2; x += 0.1) { const [a, b] = px(x, gy); el("line", {x1: a, y1: b, x2: a - 6, y2: b + 7, stroke: css("--line"), "stroke-width": 1}, fig); }
  // support region
  const [hx] = px(f.heel_m[0], gy), [bx] = px(f.ball_m[0], gy);
  el("rect", {x: hx, y: gy1 - 3, width: bx - hx, height: 3, fill: css("--axis")}, fig);
  const ank = px(0, 0), heel = px(f.heel_m[0], f.heel_m[1]), ball = px(f.ball_m[0], f.ball_m[1]);
  el("polygon", {points: [ank, heel, ball].map(q => q.join(",")).join(" "), fill: "none", stroke: css("--body"), "stroke-width": 3, "stroke-linejoin": "round"}, fig);
  const k = px(p.knee.x[i], p.knee.y[i]), h = px(p.hip.x[i], p.hip.y[i]), top = px(p.hat_drawing_top.x[i], p.hat_drawing_top.y[i]);
  el("polyline", {points: [ank, k, h].map(q => q.join(",")).join(" "), fill: "none", stroke: css("--body"), "stroke-width": 5, "stroke-linecap": "round", "stroke-linejoin": "round"}, fig);
  el("line", {x1: h[0], y1: h[1], x2: top[0], y2: top[1], stroke: css("--body"), "stroke-width": 7, "stroke-linecap": "round", opacity: .85}, fig);
  el("circle", {cx: top[0], cy: top[1] - 14, r: 13, fill: "none", stroke: css("--body"), "stroke-width": 3}, fig);
  // centres of mass
  for (const key of ["com_shank", "com_thigh", "com_hat"]) {
    const c = px(p[key].x[i], p[key].y[i]);
    el("circle", {cx: c[0], cy: c[1], r: 4.5, fill: css("--surface"), stroke: css("--body"), "stroke-width": 1.5}, fig);
  }
  // joints, coloured as their torque charts, with a ring sized by torque per kg
  const at = {ankle: ank, knee: k, hip: h};
  JOINTS.forEach(([j]) => {
    const v = r.tau[j][i] / r.mass;
    el("circle", {cx: at[j][0], cy: at[j][1], r: 6 + 14 * Math.min(1, Math.abs(v) / 1.5), fill: css("--" + j), opacity: .18}, fig);
    el("circle", {cx: at[j][0], cy: at[j][1], r: 6, fill: css("--" + j), stroke: css("--surface"), "stroke-width": 2}, fig);
  });
  // ground force arrow at the centre of pressure (per leg), 1 px per 4 N
  const cx = px(r.cop[i], gy)[0], fy = r.grf.y[i];
  el("line", {x1: cx, y1: gy1 + 30, x2: cx, y2: gy1 + 4, stroke: css("--accent"), "stroke-width": 2.5}, fig);
  el("polygon", {points: `${cx-5},${gy1+9} ${cx+5},${gy1+9} ${cx},${gy1+2}`, fill: css("--accent")}, fig);
  const lbl = el("text", {x: cx, y: gy1 + 44, "text-anchor": "middle", "font-size": 11, fill: css("--ink-2"), "font-family": css("--font-data")}, fig);
  lbl.textContent = `ground ${fmt(fy, 0)} N`;
  const scale = el("text", {x: 12, y: 18, "font-size": 11, fill: css("--muted"), "font-family": css("--font-data")}, fig);
  scale.textContent = `${r.label}: ${r.mass} kg, ${r.stature} m`;
  // readout + charts cursor
  document.getElementById("rows").innerHTML = JOINTS.map(([j, name]) =>
    `<tr><td><span class="swatch" style="background:var(--${j})"></span> ${name}</td><td>${fmt(r.q[j][i] * 180 / Math.PI, 0)}°</td><td>${fmt(r.tau[j][i])} N·m</td><td>${fmt(r.tau[j][i] / r.mass, 2)}</td></tr>`).join("");
  document.getElementById("time").textContent = `${r.t[i].toFixed(2)} s / ${r.t[N() - 1].toFixed(1)} s`;
  document.getElementById("scrub").value = i;
  charts.forEach(c => c.cursor(i));
}

// ---- torque charts, one per joint, shared time axis, each on its own symmetric scale
let charts = [];
function buildCharts() {
  const host = document.getElementById("charts"); host.replaceChildren(); charts = [];
  const W = Math.max(300, Math.round(host.clientWidth || 640)), H = 128, L = 46, R = 10, T = 8, B = 22;
  JOINTS.forEach(([j, name]) => {
    const ys = run.tau[j], t = run.t, tmax = t[t.length - 1];
    const peak = Math.max(...ys.map(Math.abs));
    const step = [2, 5, 10, 20, 25, 50, 100].find(s => peak / s <= 2.5) || 100;
    const lim = Math.max(step, Math.ceil(peak / step) * step);
    const xs = v => L + (W - L - R) * v / tmax, yv = v => T + (H - T - B) * (lim - v) / (2 * lim);
    const box = document.createElement("div"); box.className = "chart";
    box.innerHTML = `<div class="chart-head"><span class="name"><span class="swatch" style="background:var(--${j})"></span>${name}</span><span class="hint">peak ${fmt(ys.reduce((a, b) => Math.abs(b) > Math.abs(a) ? b : a), 1)} N·m</span><span class="val" id="v-${j}"></span></div>`;
    const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": `${name} torque per leg over time`});
    for (const v of [-lim, -lim / 2, 0, lim / 2, lim]) {
      el("line", {x1: L, x2: W - R, y1: yv(v), y2: yv(v), stroke: v === 0 ? css("--axis") : css("--line"), "stroke-width": 1}, svg);
      const tx = el("text", {x: L - 6, y: yv(v) + 4, "text-anchor": "end", "font-size": 11, fill: css("--muted"), "font-family": css("--font-data")}, svg);
      tx.textContent = fmt(v, Number.isInteger(v) ? 0 : 1);
    }
    for (let s = 0; s <= tmax + 1e-9; s += 0.5) {
      const tx = el("text", {x: xs(s), y: H - 6, "text-anchor": "middle", "font-size": 11, fill: css("--muted"), "font-family": css("--font-data")}, svg);
      tx.textContent = s.toFixed(1) + (s === 0 ? " s" : "");
    }
    const d = ys.map((v, k) => `${k ? "L" : "M"}${xs(t[k]).toFixed(1)},${yv(v).toFixed(1)}`).join("");
    el("path", {d, fill: "none", stroke: css("--" + j), "stroke-width": 2, "stroke-linejoin": "round"}, svg);
    const cur = el("line", {y1: T, y2: H - B, stroke: css("--ink-2"), "stroke-width": 1, "stroke-dasharray": "3 3"}, svg);
    const dot = el("circle", {r: 4, fill: css("--" + j), stroke: css("--surface"), "stroke-width": 2}, svg);
    const hit = el("rect", {x: L, y: 0, width: W - L - R, height: H, fill: "transparent", style: "cursor: crosshair"}, svg);
    const pick = ev => { const b = svg.getBoundingClientRect(); const x = (ev.clientX - b.left) / b.width * W;
      i = Math.max(0, Math.min(N() - 1, Math.round((x - L) / (W - L - R) * (N() - 1)))); playing = false; syncPlay(); draw(); };
    hit.addEventListener("pointerdown", ev => { pick(ev); hit.setPointerCapture(ev.pointerId); });
    hit.addEventListener("pointermove", ev => { if (ev.buttons) pick(ev); });
    box.appendChild(svg); host.appendChild(box);
    charts.push({cursor: k => { cur.setAttribute("x1", xs(t[k])); cur.setAttribute("x2", xs(t[k]));
      dot.setAttribute("cx", xs(t[k])); dot.setAttribute("cy", yv(ys[k]));
      document.getElementById("v-" + j).textContent = `${fmt(ys[k])} N·m at ${t[k].toFixed(2)} s`; }});
  });
}

// ---- facts panels
function facts() {
  const c = run.checks, res = c.residuals;
  const names = {newton_euler_vs_lagrange_N_m: ["Two formulations agree", "N·m"], static_oracle_N_m: ["Held poses vs gravity", "N·m"],
    energy_W: ["Energy balance", "W"], newton_identity_per_leg_N: ["Ground force, per leg", "N"],
    newton_identity_whole_body_N: ["Ground force, whole body", "N"], round_trip_one_step_rad_at_1ms: ["Forward step, 1 ms", "rad"],
    mass_bookkeeping_relative: ["Mass bookkeeping", "relative"]};
  document.getElementById("checks").innerHTML = Object.entries(names).map(([k, [n, u]]) =>
    `<dt>${n}</dt><dd>${c.passed[k] ? '<span class="pill ok">pass</span>' : '<span class="pill flag">fail</span>'} ${Math.abs(res[k]).toExponential(1)} ${u}</dd>`).join("");
  const ct = run.contact;
  document.getElementById("contact").innerHTML = `
    <dt>Status</dt><dd>${ct.feasible ? '<span class="pill ok">feasible throughout</span>' : '<span class="pill flag">flagged</span>'}</dd>
    <dt>Lowest ground force</dt><dd>${ct.normal_force_min_N.toFixed(0)} N per leg</dd>
    <dt>Centre of pressure</dt><dd>${(ct.cop_min_m * 100).toFixed(1)} to ${(ct.cop_max_m * 100).toFixed(1)} cm from the ankle</dd>
    <dt>Foot support</dt><dd>${(ct.support_heel_m * 100).toFixed(1)} (heel) to ${(ct.support_ball_m * 100).toFixed(1)} cm (ball)</dd>
    <dt>Grip needed</dt><dd>${ct.required_friction_max.toFixed(3)} (flag above ${ct.friction_coefficient_assumed})</dd>`;
}

// ---- playback
const playBtn = document.getElementById("play");
function syncPlay() { playBtn.textContent = playing ? "Pause" : "Play"; }
playBtn.onclick = () => { playing = !playing; if (playing && i >= N() - 1) i = 0; syncPlay(); };
document.getElementById("scrub").addEventListener("input", e => { i = +e.target.value; playing = false; syncPlay(); draw(); });
function tick(ts) {
  if (playing) { if (last === null) last = ts; const dt = (ts - last) / 1000; last = ts;
    const step = run.t[1] - run.t[0]; const adv = Math.floor(dt / step);
    if (adv > 0) { i = (i + adv) % N(); last = ts - (dt - adv * step) * 1000; draw(); } } else last = null;
  requestAnimationFrame(tick);
}
document.getElementById("scrub").max = N() - 1;
const fv = DATA.validity;
const st = DATA.status;
document.getElementById("badge").innerHTML = (st.mechanics_verification === "passed"
    ? `<b>Mechanics verified</b> for an idealized model` : `<b class="flag">Mechanics checks FAILED</b> do not use these results`)
  + ` · ` + (st.contact_feasibility === "feasible" ? `<b>Contact feasible</b>` : `<b class="flag">Contact flagged</b>`)
  + ` · <b class="prov">Sources provisional</b> · not validated against measured squats`;
document.getElementById("foot").innerHTML = `
  <div>${fv.kind.charAt(0).toUpperCase() + fv.kind.slice(1)}. Physiological validity: ${fv.physiological_validity}. Clinical validity: ${fv.clinical_validity}.</div>
  <div>Status: mechanics ${st.mechanics_verification}; contact ${st.contact_feasibility}; sources ${st.source_validation} (${DATA.source_validation.de_leva_values}).</div>
  <div>Run manifest at commit <code>${DATA.commit.slice(0, 12)}</code> · provenance <code>${DATA.provenance}</code> · decision D-058.</div>
  <div>Sources: de Leva P (1996) J Biomech 29(9):1223–1230, via the open data of Duarte M, <a href="https://github.com/BMClab/BMC" target="_blank" rel="noopener">BMClab/BMC</a> (CC BY 4.0); OpenSim Gait2392, <a href="https://github.com/opensim-org/opensim-models" target="_blank" rel="noopener">opensim-org/opensim-models</a> (CC BY 3.0).</div>`;
syncPlay(); buildCharts(); facts(); draw(); requestAnimationFrame(tick);
let rw = 0; addEventListener("resize", () => { const w = document.getElementById("charts").clientWidth; if (Math.abs(w - rw) > 4) { rw = w; buildCharts(); draw(); } });
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { buildCharts(); draw(); });
new MutationObserver(() => { buildCharts(); draw(); }).observe(document.documentElement, {attributes: true, attributeFilter: ["data-theme"]});
</script>
"""


def render(manifest):
    data = json.dumps(compact(manifest), separators=(",", ":"), allow_nan=False)
    return TEMPLATE.replace("__DATA__", data.replace("</", "<\\/"))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(manifest), encoding="utf-8")
    print("Page written to", args.output)


if __name__ == "__main__":
    main()
