"""Generator for References/LB_AO_Project_Phases_Overview.pdf (phase overview for the instructor).

Regenerate: python tools/make_phases_overview_pdf.py References/LB_AO_Project_Phases_Overview.pdf <Stage D1 run JSON>
The run JSON used for the 2026-10-28 PDF is results/phase_d/2026-10-28_d1_squat_runs_38d5bdf.json
(branch phase-d/claude-d1-squat at 0aa4651). Figures 1-2 are drawn from that file.
Needs reportlab, matplotlib and the DejaVu fonts (Linux path below); not project dependencies.
Prose and tables are a hand-written summary of DECISIONS.md and PROJECT_STATE.md as of 2026-10-28.
"""
import sys, json, tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether, Image)

OUT, RUN = sys.argv[1], sys.argv[2]
FIG = tempfile.mkdtemp()


def make_figures(run_path, out_dir):
    d = json.load(open(run_path))
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    ink, ac, mu, c2 = "#1f2933", "#1d5b79", "#52606d", "#c26a2a"
    r = [x for x in d["runs"] if x["body"] == "female"][0]
    s, pts_all, f = r["series"], r["series"]["points_m"], r["foot"]
    fig, ax = plt.subplots(figsize=(6.4, 2.5))
    for n, i in enumerate([0, 40, 80, 150]):
        o = n * 0.72
        pts = [(0, 0), (pts_all["knee"]["x"][i], pts_all["knee"]["y"][i]), (pts_all["hip"]["x"][i], pts_all["hip"]["y"][i])]
        top = (pts_all["hat_drawing_top"]["x"][i], pts_all["hat_drawing_top"]["y"][i])
        ax.plot([p[0] + o for p in pts], [p[1] for p in pts], color=ac, lw=2.6, solid_capstyle="round")
        ax.plot([pts[2][0] + o, top[0] + o], [pts[2][1], top[1]], color=mu, lw=4, solid_capstyle="round")
        ax.plot([f["heel_m"][0] + o, f["ball_m"][0] + o], [f["ground_y_m"]] * 2, color=ink, lw=3)
        ax.scatter([p[0] + o for p in pts], [p[1] for p in pts], s=16, color="white", edgecolor=ink, zorder=3, lw=1)
        ax.text(o + 0.03, -0.17, f"t = {s['t_s'][i]:.1f} s", ha="center", color=mu, fontsize=8.5)
    ax.axhline(f["ground_y_m"], color="#c5d0d8", lw=1, zorder=0)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-0.3, 2.45); ax.set_ylim(-0.21, 1.72)
    fig.tight_layout(pad=0.2); fig.savefig(f"{out_dir}/stick.png", dpi=220); plt.close(fig)
    fig, axs = plt.subplots(1, 3, figsize=(6.8, 2.3), sharey=True)
    for j, a in zip(("ankle", "knee", "hip"), axs):
        for body, c, ls in (("female", ac, "-"), ("male", c2, "--")):
            rr = [x for x in d["runs"] if x["body"] == body][0]
            a.plot(rr["series"]["t_s"], [v / rr["body_mass_kg"] for v in rr["series"]["tau_per_leg_N_m"][j]],
                   color=c, ls=ls, lw=1.6, label=body.capitalize())
        a.set_title(j.capitalize(), fontsize=9.5, color=ink); a.axhline(0, color="#c5d0d8", lw=0.8)
        a.set_xlabel("time (s)")
        for sp in ("top", "right"): a.spines[sp].set_visible(False)
    axs[0].set_ylabel("torque per leg\n(N\u00b7m per kg body mass)"); axs[0].legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(f"{out_dir}/torque.png", dpi=220); plt.close(fig)


make_figures(RUN, FIG)
D = "/usr/share/fonts/truetype/dejavu/"
for n, f in [("Sans", "DejaVuSans"), ("Sans-B", "DejaVuSans-Bold"), ("Sans-I", "DejaVuSans-Oblique"),
             ("Sans-BI", "DejaVuSans-BoldOblique"), ("Serif", "DejaVuSerif"), ("Serif-B", "DejaVuSerif-Bold")]:
    pdfmetrics.registerFont(TTFont(n, D + f + ".ttf"))
registerFontFamily("Sans", normal="Sans", bold="Sans-B", italic="Sans-I", boldItalic="Sans-BI")

INK = colors.HexColor("#1f2933"); MUTED = colors.HexColor("#52606d"); ACCENT = colors.HexColor("#1d5b79")
LIGHT = colors.HexColor("#e8f0f4"); RULE = colors.HexColor("#c5d0d8"); WARM = colors.HexColor("#c26a2a")
DONE = colors.HexColor("#1d5b79"); NOW = colors.HexColor("#c26a2a"); NEXT = colors.HexColor("#9aa5b1")

body = ParagraphStyle("b", fontName="Sans", fontSize=9.6, leading=13.8, textColor=INK, spaceAfter=6)
small = ParagraphStyle("s", parent=body, fontSize=8.4, leading=11.5, spaceAfter=0)
cell = ParagraphStyle("c", parent=body, fontSize=8.5, leading=11.4, spaceAfter=0)
cellb = ParagraphStyle("cb", parent=cell, fontName="Sans-B")
h1 = ParagraphStyle("h1", parent=body, fontName="Serif-B", fontSize=15, leading=19, textColor=ACCENT,
                    spaceBefore=12, spaceAfter=6, keepWithNext=1)
h2 = ParagraphStyle("h2", parent=body, fontName="Sans-B", fontSize=10.5, leading=14, spaceBefore=7,
                    spaceAfter=3, keepWithNext=1)
bul = ParagraphStyle("bul", parent=body, leftIndent=14, bulletIndent=3, spaceAfter=3)
title = ParagraphStyle("t", parent=body, fontName="Serif-B", fontSize=23, leading=28, spaceAfter=6)
subtitle = ParagraphStyle("st", parent=body, fontName="Serif", fontSize=12.5, leading=17, textColor=MUTED, spaceAfter=12)
meta = ParagraphStyle("m", parent=body, fontSize=8.8, leading=12.5, textColor=MUTED, spaceAfter=0)
box = ParagraphStyle("box", parent=body, fontSize=9.8, leading=14.2, spaceAfter=4)
cap = ParagraphStyle("cap", parent=small, textColor=MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=10)


def P(t, s=body): return Paragraph(t, s)
def bullets(items): return [Paragraph(i, bul, bulletText="•") for i in items]


def callout(paras, bg=LIGHT, edge=ACCENT):
    t = Table([[paras]], colWidths=[6.5 * inch])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, edge),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def table(rows, widths, header=True):
    data = [[P(c, cellb if (header and i == 0) else cell) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * inch for w in widths], repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, RULE),
          ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 1, ACCENT)]
    t.setStyle(TableStyle(st))
    return t


def timeline():
    W, H = 6.5 * inch, 1.4 * inch
    d = Drawing(W, H)
    phases = [("A", "Integrity", DONE, "Done"), ("B", "Hip-only model", DONE, "Done"),
              ("C", "Foundations", DONE, "Done"), ("D", "Planar squat", NOW, "In progress"),
              ("E", "Conditions", NEXT, "Planned"), ("F", "Personalization", NEXT, "Planned")]
    n = len(phases); gap = 6; bw = (W - gap * (n - 1)) / n; y = 34
    for i, (k, name, col, st) in enumerate(phases):
        x = i * (bw + gap)
        d.add(Polygon([x, y, x + bw - 8, y, x + bw + 2, y + 21, x + bw - 8, y + 42, x, y + 42, x + 10, y + 21]
                      if i else [x, y, x + bw - 8, y, x + bw + 2, y + 21, x + bw - 8, y + 42, x, y + 42],
                      fillColor=col, strokeColor=None))
        d.add(String(x + bw / 2, y + 17, f"Phase {k}", fontName="Sans-B", fontSize=10.5,
                     fillColor=colors.white, textAnchor="middle"))
        d.add(String(x + bw / 2, y - 13, name, fontName="Sans", fontSize=8.4, fillColor=INK, textAnchor="middle"))
        d.add(String(x + bw / 2, y - 25, st, fontName="Sans-I", fontSize=7.8, fillColor=MUTED, textAnchor="middle"))
    d.add(String(0, H - 10, "Oct 7: plan adopted", fontName="Sans", fontSize=7.8, fillColor=MUTED))
    d.add(String(W, H - 10, "Oct 28: Stage D1 built, under review", fontName="Sans", fontSize=7.8,
                 fillColor=MUTED, textAnchor="end"))
    return d


def footer(c, doc):
    c.saveState(); c.setFont("Sans", 7.6); c.setFillColor(MUTED)
    c.drawString(inch, 0.6 * inch, "LB-AO musculoskeletal digital twin · Project phases to date · October 28, 2026")
    c.drawRightString(7.5 * inch, 0.6 * inch, f"Page {doc.page}")
    c.restoreState()


doc = BaseDocTemplate(OUT, pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=0.85 * inch,
                      bottomMargin=0.9 * inch, title="LB-AO: Project Phases to Date",
                      author="Claude (Anthropic), prepared for Corbin Wright",
                      subject="Overview of the LB-AO independent study phases for the course instructor")
doc.addPageTemplates([PageTemplate("p", [Frame(inch, 0.9 * inch, 6.5 * inch, 9.25 * inch, id="f",
                                                leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                                   onPage=footer)])
s = []

# ---------- Title ----------
s += [P("A Musculoskeletal Digital Twin: Project Phases to Date", title),
      P("How the LB-AO independent study got from an anatomy database to a simulated squat, and what comes next", subtitle),
      P("<b>Student:</b> Corbin Wright · Independent Study, Fall 2026", meta),
      P("<b>Snapshot:</b> October 28, 2026 · repository <font name='Sans-I'>Corb1nW/Independent-Study</font>, "
        "<font name='Sans'>main</font> at ce0acce; Stage D1 on branch phase-d/claude-d1-squat at 0aa4651", meta),
      P("<b>Prepared by:</b> Claude (Anthropic), one of the two AI models working on the project, at Corbin’s request. "
        "Every figure here is taken from the project’s records and run files.", meta),
      Spacer(1, 12)]

s.append(callout([
    P("<b>The goal.</b> Build the groundwork for a digital model of the human lower body that can be adjusted to "
      "reflect real conditions (weakness, injury, individual body size) and used in physical therapy education and "
      "clinics. The project applies dynamic systems and control theory to human movement.", box),
    P("<b>Where it stands.</b> Phases A through C are complete and accepted. Phase D, the first model that looks like a "
      "person doing something (a squat), has its first stage built and is in review. The model can already take "
      "published body measurements, move a simulated leg through a squat, and report the joint loads, with "
      "independent mathematical checks that the answers are correct for the model as stated.", box),
    P("<b>Guiding rule.</b> The model must always be able to say which number it used and why. Every value carries its "
      "source and how certain it is; values with no traceable source are refused.", box)]))

s += [P("The six-phase plan", h1),
      P("The plan was adopted on October 7 after the first round of review, and each phase must meet a stated exit "
        "criterion before the next begins."),
      timeline(), Spacer(1, 4)]

# ---------- How the work is done ----------
s += [P("How the work is done", h1),
      P("Two AI models, Claude and ChatGPT, take turns as <b>builder</b> and <b>reviewer</b>, and Corbin makes every "
        "decision. The builder writes the code and records; the reviewer checks them independently and returns one of "
        "three verdicts: AGREE, AMEND or DISAGREE. Only Corbin can accept or reject. The two models hand work to each "
        "other through a shared GitHub repository, so every change, review and approval is saved with a date and can "
        "be traced."),
      P("Two records hold the project together. A <b>decision log</b> (58 decisions so far) records each choice with its "
        "justification, who proposed it and Corbin’s approval in his own words. A <b>source list</b> names every "
        "publication the project relies on and whether it was actually read. A separate document in the repository, "
        "<i>GitHub Multi-Model Workflow</i>, explains this process in more detail.")]

# ---------- Earlier phases ----------
s += [P("Phases A to C, briefly", h1),
      P("The starting point", h2),
      P("ChatGPT built the first version: an <b>ontology</b> of the pelvis and hip (a structured database of bones, "
        "joints, muscles and nerves and how they connect) and a data file for one reference muscle, the gluteus "
        "maximus, with values from published studies. Claude reviewed it, ran the code and found real defects. The two "
        "models then disagreed on parts of the critique, Corbin weighed both sides, and the six-phase plan came out "
        "of that exchange."),
      P("Phase A: Integrity  <font color='#52606d' name='Sans'>(Claude built, ChatGPT reviewed)</font>", h2),
      P("Fix what was broken before building on it. The checker was accepting records it should have rejected, some "
        "references pointed at nothing, and units were not checked. Phase A added a three-layer validator "
        "(structure, then meaning and units, then evidence), a project-wide integrity check, and a test that fails on "
        "each defect found. Two anatomy entries were corrected after checking them against primary sources."),
      P("Phase B: Hip-only model  <font color='#52606d' name='Sans'>(ChatGPT built, Claude reviewed)</font>", h2),
      P("The first simulation, kept as small as possible on purpose: one hip joint driven by one muscle (gluteus "
        "maximus) with a fixed lever arm, its strength read from the data file. It proved that data reaches the "
        "physics: change a number in the data and the simulated hip moves differently, in a way that can be "
        "explained. With 20% more muscle force, the hip reaches the end of its range about 73 ms sooner (0.767 s "
        "instead of 0.841 s), matching the hand-derived formula to machine precision. Every run records the exact "
        "numbers and code version it used."),
      P("Phase C: Foundations  <font color='#52606d' name='Sans'>(Claude built, ChatGPT reviewed)</font>", h2),
      P("Corbin chose a slimmer Phase C covering only what Phase B showed was needed, so the project could reach a "
        "demonstrable model sooner:"),
      *bullets(["a shared run record that works the same on Windows and Linux;",
                "a check of what the published gluteus maximus force value means (whether it acts along the muscle "
                "fibers or the tendon), still open as decision D-056;",
                "a rule that contraction speeds must state their units;",
                "a gate that refuses to run a model on any number that cannot be traced to a source;",
                "a test that the ontology can grow without breaking existing data, and the first results plot."]),
      P("The project’s source list and the shared builder/reviewer instructions for both models were added at the "
        "same time.")]

# ---------- Phase D ----------
s += [P("Phase D: Planar squat, in detail", h1),
      P("Phase D is split into two stages so the mechanics can be proven correct before muscles are added. "
        "Claude is building and ChatGPT is reviewing."),
      P("Stage D1: the mechanics (built, in review)", h2),
      P("<b>The model.</b> A side view of one leg (foot, shank and thigh) carrying half of the upper body. The ankle, "
        "knee and hip are hinges, and the foot is fixed flat on the floor. Because both legs do the same thing in a "
        "squat, one leg with half the upper body stands in for the whole body."),
      P("<b>The motion is prescribed, not simulated.</b> The joints are told how to move: from standing down to about "
        "100° of knee bend and back up over 3 seconds. The model then works backwards, a calculation called "
        "<b>inverse dynamics</b>, to find the torque each joint must produce and how hard and where the ground pushes "
        "on the foot. This is the same calculation a gait lab performs on motion-capture data, here with a "
        "constructed motion instead of a recorded one.")]

s += [KeepTogether([Image(f"{FIG}/stick.png", width=6.0 * inch, height=6.0 * inch * 2.5 / 6.4),
                    P("Figure 1. The female body at four moments of the squat (side view, facing right). Blue: "
                      "shank and thigh. Grey: a line from the hip toward the upper body’s centre of mass, not the "
                      "spine. Drawn from the Stage D1 run file.", cap)])]

s += [P("<b>Body measurements</b> come from two published, open sources. The OpenSim Gait2392 model, widely used "
        "in research, provides joint positions and the upper body’s shape. de Leva (1996) provides how body mass is "
        "divided among the segments, separately for women and men. Together they give three switchable bodies:"),
      table([["Body", "Mass", "Height", "Peak knee torque per leg"],
             ["Female (de Leva 1996)", "61.9 kg", "1.735 m", "1.20 N·m per kg"],
             ["Male (de Leva 1996)", "73.0 kg", "1.741 m", "1.20 N·m per kg"],
             ["Gait2392 reference", "75.16 kg", "1.80 m", "1.21 N·m per kg"]], [2.0, 1.1, 1.1, 2.3]),
      Spacer(1, 8)]

s += [KeepTogether([Image(f"{FIG}/torque.png", width=6.4 * inch, height=6.4 * inch * 2.3 / 6.8),
                    P("Figure 2. Net joint torque per leg, divided by body mass, through one 3-second squat. "
                      "Sign convention: positive torque acts to increase flexion (dorsiflexion at the ankle), so the "
                      "large negative knee torque is the knee extensors holding the body up. Female and male curves "
                      "nearly coincide once scaled by body mass.", cap)])]

s += [P("<b>Why the checks matter.</b> Numbers that look plausible are not proof, so most of Stage D1 is "
        "verification. Each check tests the answer a different way:"),
      table([["Check", "What it confirms", "Result"],
             ["Two methods agree", "Torques computed segment by segment (Newton–Euler) and again from energy "
              "equations (Lagrange), written independently", "Agree to about 10<super>-13</super> N·m"],
             ["Holding still", "In frozen poses the torques equal the gravity load, computed a third, simpler way",
              "Match"],
             ["Energy balance", "Power put in by the joints equals the change in the body’s energy at every moment",
              "Match"],
             ["Force balance", "Ground force equals body weight plus mass times acceleration", "Match"],
             ["Feeding back", "Putting the computed torques into a forward simulation reproduces the motion", "Match"],
             ["Known answers", "One- and two-segment pendulums reproduce their textbook formulas", "Match"],
             ["Balance and grip", "Flags any moment the foot would lift, slip, or the pressure point leaves the foot",
              "None occur"]], [1.35, 3.85, 1.3]),
      Spacer(1, 8),
      P("<b>What it shows.</b> A peak knee torque of about 1.2 N·m per kilogram of body mass per leg, a reasonable "
        "magnitude for a bodyweight squat."),
      P("<b>What it does not show.</b> The model has not been compared against real people, the motion was not "
        "recorded from anyone, and there are no muscles yet. The checks show the equations of this simplified model "
        "are solved correctly, not that the model matches a human body. The run files and the viewer page state "
        "these limits."),
      P("<b>Current status.</b> ChatGPT reviewed Stage D1 on October 28 and returned AMEND, asking mainly for "
        "clearer labeling of what is verified versus assumed (for example, how the upper body’s shape is derived) "
        "and for status fields that separate the mechanics checks from the balance check. Stage D1 will be "
        "revised, re-reviewed, and then accepted or not by Corbin."),
      P("Stage D2: muscles (next)", h2),
      P("Muscles are added, and the question becomes which muscles produce the joint torques found in Stage D1. "
        "Because many muscles cross each joint, this is a distribution problem with more than one possible answer, "
        "so it needs an explicit, documented choice of method. It first requires Corbin’s decision on D-056, the "
        "meaning of the published gluteus maximus force value, which determines how the muscle force law is written.")]

# ---------- What comes next ----------
s += [P("After Phase D", h1),
      table([["Phase", "Purpose", "Finished when"],
             ["E. Conditions", "Represent clinical conditions (for example, muscle weakness) as documented parameter "
              "changes with supporting evidence, limited to conditions the model can actually express; test how "
              "sensitive the results are", "A condition can be switched on and its effect reported with its "
              "uncertainty"],
             ["F. Personalization", "Connect clinic measurements to model parameters and check which parameters the "
              "measurements can actually determine", "A patient’s measurements produce a parameter set with "
              "stated confidence"]], [1.3, 3.3, 1.9]),
      Spacer(1, 8),
      P("This independent study lays the groundwork. The longer-term aim is a highly customizable model covering all "
        "the major systems that affect movement, useful to clinicians and to students preparing for clinical "
        "practice.")]

s += [P("Where to find things", h1),
      table([["Item", "Location in the repository"],
             ["Decision log (all 58 decisions, approvals and amendments)", "docs/DECISIONS.md"],
             ["Current status and next tasks", "PROJECT_STATE.md"],
             ["Every source used, and whether it was read", "sources/SOURCES.md"],
             ["Reviews by each model", "docs/reviews/"],
             ["Stage D1 run results and animated squat viewer", "results/phase_d/ (branch phase-d/claude-d1-squat until merged)"],
             ["Explainer for the two-model workflow", "References/GitHub_Multi_Model_Workflow.pdf"]],
            [3.2, 3.3]),
      Spacer(1, 10),
      P("<b>Key sources.</b> Arnold EM et al. (2010), <i>Annals of Biomedical Engineering</i> 38:269–279 (muscle "
        "parameters). de Leva P (1996), <i>Journal of Biomechanics</i> 29:1223–1230 (segment mass and inertia). "
        "The OpenSim Gait2392 model file, opensim-org/opensim-models (joint geometry). The full list is in "
        "sources/SOURCES.md.", small)]

doc.build(s)
print("ok", OUT)
