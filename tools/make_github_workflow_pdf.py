"""Generator for References/GitHub_Multi_Model_Workflow.pdf (D-051 explainer for peers).

Regenerate: python tools/make_github_workflow_pdf.py References/GitHub_Multi_Model_Workflow.pdf <records SHA>
Needs reportlab and the DejaVu fonts (Linux path below); not a project dependency.
"""
import sys
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether, PageBreak)

OUT = sys.argv[1]
SNAP = sys.argv[2]
D = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Sans", D + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-B", D + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Sans-I", D + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("Sans-BI", D + "DejaVuSans-BoldOblique.ttf"))
pdfmetrics.registerFont(TTFont("Serif", D + "DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("Serif-B", D + "DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono", D + "DejaVuSansMono.ttf"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("Sans", normal="Sans", bold="Sans-B", italic="Sans-I", boldItalic="Sans-BI")

INK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#52606d")
ACCENT = colors.HexColor("#1d5b79")
LIGHT = colors.HexColor("#e8f0f4")
RULE = colors.HexColor("#c5d0d8")

base = ParagraphStyle("base", fontName="Sans", fontSize=9.4, leading=13.4, textColor=INK, spaceAfter=6)
body = base
small = ParagraphStyle("small", parent=base, fontSize=8.4, leading=11.5, spaceAfter=0)
cell = ParagraphStyle("cell", parent=base, fontSize=8.4, leading=11.2, spaceAfter=0)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Sans-B")
h1 = ParagraphStyle("h1", parent=base, fontName="Serif-B", fontSize=15, leading=19, textColor=ACCENT,
                    spaceBefore=14, spaceAfter=6, keepWithNext=1)
h2 = ParagraphStyle("h2", parent=base, fontName="Sans-B", fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=3, keepWithNext=1)
bullet = ParagraphStyle("bullet", parent=base, leftIndent=14, bulletIndent=3, spaceAfter=3)
title = ParagraphStyle("title", parent=base, fontName="Serif-B", fontSize=24, leading=29, textColor=INK, spaceAfter=8)
subtitle = ParagraphStyle("subtitle", parent=base, fontName="Serif", fontSize=12.5, leading=17, textColor=MUTED,
                          spaceAfter=14)
meta = ParagraphStyle("meta", parent=base, fontSize=8.8, leading=12.5, textColor=MUTED, spaceAfter=0)
boxstyle = ParagraphStyle("box", parent=base, fontSize=9.8, leading=14.2)
cap = ParagraphStyle("cap", parent=small, textColor=MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=8)


def P(t, s=body):
    return Paragraph(t, s)


def bullets(items):
    return [Paragraph(i, bullet, bulletText="•") for i in items]


def code(t):
    return f'<font name="Mono" size="8.4">{t}</font>'


def table(rows, widths, header=True, zebra=True):
    data = [[Paragraph(c, cellb if (header and r == 0) else cell) if isinstance(c, str) else c for c in row]
            for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT),
          ("LINEBELOW", (0, 1), (-1, -1), 0.3, RULE),
          ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), LIGHT))
    t.setStyle(TableStyle(st))
    return t


def callout(flowables, color=LIGHT):
    t = Table([[flowables]], colWidths=[6.5 * inch])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color),
                           ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


def workflow_diagram():
    W, H = 468, 250
    d = Drawing(W, H)

    def box(x, y, w, h, title_, lines, fill=LIGHT, stroke=ACCENT):
        d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=stroke, strokeWidth=0.9, rx=4, ry=4))
        d.add(String(x + w / 2, y + h - 13, title_, fontName="Sans-B", fontSize=8.4, fillColor=INK,
                     textAnchor="middle"))
        for i, ln in enumerate(lines):
            d.add(String(x + w / 2, y + h - 25 - 10 * i, ln, fontName="Sans", fontSize=7.2, fillColor=MUTED,
                         textAnchor="middle"))

    def arrow(x1, y1, x2, y2, label=None, dx=0, dy=4):
        d.add(Line(x1, y1, x2, y2, strokeColor=INK, strokeWidth=0.9))
        import math
        a = math.atan2(y2 - y1, x2 - x1)
        s = 5
        p1 = (x2 - s * math.cos(a - 0.4), y2 - s * math.sin(a - 0.4))
        p2 = (x2 - s * math.cos(a + 0.4), y2 - s * math.sin(a + 0.4))
        d.add(Polygon([x2, y2, p1[0], p1[1], p2[0], p2[1]], fillColor=INK, strokeColor=INK, strokeWidth=0.5))
        if label:
            d.add(String((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, label, fontName="Sans-I", fontSize=6.8,
                         fillColor=MUTED, textAnchor="middle"))

    # top row
    box(0, 170, 110, 62, "Builder model", ["works on a branch", "commits + pushes"])
    box(150, 170, 140, 62, "Pull request", ["handoff: start/head SHA,", "changes, commands run,", "results, open questions"])
    box(330, 170, 138, 62, "Automated checks (CI)", ["tests + integrity check", "on every push", "(supporting evidence)"],
        fill=colors.white)
    # middle
    box(150, 78, 140, 62, "Reviewer model", ["reviews the exact SHA,", "reruns checks, files one", "review record (own PR)"])
    box(0, 78, 110, 62, "Fix round", ["builder answers with", "new commits; new SHA", "= new review target"],
        fill=colors.white)
    box(330, 78, 138, 62, "Owner (Corbin)", ["approves a specific", "revision and merges", "(merge commit only)"],
        fill=colors.HexColor("#fdf3e1"), stroke=colors.HexColor("#b7791f"))
    # bottom
    box(150, 0, 318, 50, "main  (protected: pull request required, no force-push)",
        ["accepted history  +  DECISIONS.md (why)  +  PROJECT_STATE.md (what next)"],
        fill=colors.HexColor("#eef6ee"), stroke=colors.HexColor("#3f7d4a"))

    arrow(110, 201, 150, 201, "opens")
    arrow(290, 201, 330, 201, "triggers")
    arrow(220, 170, 220, 140, "pinned to SHA", dx=30, dy=-2)
    arrow(150, 109, 110, 109, "findings", dy=4)
    arrow(55, 140, 55, 170, "push", dx=-14, dy=-2)
    arrow(290, 109, 330, 109, "verdict")
    arrow(399, 78, 399, 50, "merge", dx=16, dy=-2)
    return d


def on_page(c, doc):
    c.saveState()
    c.setFont("Sans", 7.5)
    c.setFillColor(MUTED)
    c.drawString(0.9 * inch, 0.55 * inch, "Coordinating two AI models through GitHub  ·  LB-AO / Independent Study")
    c.drawRightString(7.6 * inch, 0.55 * inch, f"{doc.page}")
    c.setStrokeColor(RULE)
    c.setLineWidth(0.4)
    c.line(0.9 * inch, 0.7 * inch, 7.6 * inch, 0.7 * inch)
    c.restoreState()


doc = BaseDocTemplate(OUT, pagesize=letter, leftMargin=0.9 * inch, rightMargin=0.9 * inch,
                      topMargin=0.75 * inch, bottomMargin=0.95 * inch,
                      title="Coordinating Two AI Models Through GitHub",
                      author="Claude (Anthropic), for Corbin Wright",
                      subject="LB-AO project: GitHub-based build-and-review workflow between two AI models (D-051)",
                      creator="ReportLab")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=on_page)])

s = []
s.append(P("Coordinating Two AI Models Through GitHub", title))
s.append(P("How the LB-AO musculoskeletal digital twin project moved its AI build-and-review workflow onto a "
           "shared repository, what happened when we tried it, and why we are keeping it", subtitle))
s.append(P("<b>Project:</b> Lower-Body Anatomical Ontology (LB-AO), groundwork for a musculoskeletal digital twin. "
           "Independent study, Misericordia University, Fall 2026.", meta))
s.append(P("<b>Owner:</b> Corbin Wright  ·  <b>AI collaborators:</b> ChatGPT and Claude", meta))
s.append(P(f"<b>Repository:</b> github.com/Corb1nW/Independent-Study  ·  <b>Records as of commit</b> "
           f"{code(SNAP[:7])} (21 October 2026)", meta))
s.append(P("<b>Prepared by</b> Claude (Anthropic) at Corbin's request, from the repository's own records. "
           "Every claim below can be checked against the files and pull requests listed at the end. Claude is one of "
           "the two models described: this document reports the records rather than evaluating them independently.", meta))
s.append(Spacer(1, 14))

s.append(callout([
    P("<b>In one paragraph</b>", h2),
    P("Two AI models take turns building and reviewing the project's code and data, and Corbin, the human owner, "
      "makes every decision. Until 20 October 2026 their work moved between them as zip files and chat messages. "
      "Decision <b>D-051</b> made a GitHub repository the meeting point instead. Every handoff is now a <i>commit</i> "
      "with a unique ID, every review names the exact commit it examined, and every approval is a recorded action "
      "by Corbin on a specific revision. A two-day pilot, eight pull requests, ran a complete cycle: build, review, "
      "fix, re-review, and an independent re-run of the tests by the second model. It met every pass criterion, "
      "and Corbin accepted D-051 on 21 October 2026. The next phase starts with the models' roles swapped.",
      boxstyle)]))

s.append(P("1. The setup: two models, one owner", h1))
s.append(P("The project uses a deliberate division of labour (decision D-041). One model <b>builds</b>: it writes code, "
           "data and documentation. The other <b>reviews</b>: it checks the work, tries to break it, and reports "
           "findings. Corbin <b>decides</b>: model agreement is only a recommendation, and nothing becomes accepted "
           "without his approval or an explicit delegation. Two files hold the project's memory: "
           f"{code('docs/DECISIONS.md')}, which records every decision, who proposed it, how it is defended and who "
           f"approved it, and {code('PROJECT_STATE.md')}, which records what exists, what has been verified and "
           "what happens next."))
s.append(P("For Phase A (fixing integrity defects in the ontology and its validator), Claude built and ChatGPT "
           "reviewed. For Phase B (a first hip-only simulation), the roles are swapped."))

s.append(P("2. The problem with passing files around", h1))
s.append(P("Before D-051, a handoff meant downloading the repository as a zip, uploading it to the other model's chat, "
           "and often recreating files from chat output. On 20 October Corbin proposed giving both models direct access "
           "to the project files instead, to “save time and energy of downloading and sharing and then recreating "
           "files.” The time cost was the visible problem. Three less visible ones mattered as much:"))
s += bullets([
    "<b>No fixed snapshot.</b> A reviewer could not prove which version it had examined, and a file could change "
    "between a test run and the report about it.",
    "<b>Transcription risk.</b> A file regenerated from a chat message can differ silently from the one that was "
    "reviewed.",
    "<b>Scattered approvals.</b> Corbin's decisions lived in separate chat transcripts, which made them hard to cite.",
])

s.append(P("3. Choosing the mechanism", h1))
s.append(P("Taken literally, Corbin's idea was for both models to work in one shared folder on his computer. Claude "
           "proposed a shared <b>git remote</b> instead. Git records every version permanently and gives each one a "
           "unique identifier, so that is what a review should point to. The options compared:"))
s.append(table([
    ["Option", "Fixed snapshot a review can cite", "Version history", "Safe with two editors", "Verdict"],
    ["Shared local folder", "No: files change underneath a review", "No", "No: silent overwrites", "Allowed as a way of <i>working</i>, never as the handoff"],
    ["Shared cloud folder", "No", "Limited", "No", "Rejected"],
    ["Zip uploads (status quo)", "Only if the zip includes git history", "Only with git history", "n/a", "Kept as the fallback"],
    ["<b>Shared git remote (GitHub)</b>", "<b>Yes: the commit ID (SHA)</b>", "<b>Yes, complete</b>", "<b>Yes: separate branches</b>", "<b>Chosen</b>"],
], [1.25 * inch, 1.55 * inch, 1.05 * inch, 1.15 * inch, 1.5 * inch]))
s.append(Spacer(1, 6))
s.append(P("A <b>commit SHA</b> such as " + code("4abb4f1995956d926959ac5ef0f0f68656619ee6") + " is a fingerprint of "
           "the entire project at one moment: every file, byte for byte. If two people name the same SHA, they are "
           "looking at exactly the same thing."))

s.append(P("4. How the decision itself was made", h1))
s.append(P("D-051 went through the same build-and-review process it describes, and the review changed it substantially."))
s.append(table([
    ["When (2026)", "Step", "Record"],
    ["20 Oct, 13:11", "Corbin proposes direct file access for both models", "Session transcript, quoted in D-051"],
    ["20 Oct", "Claude drafts D-051 revision 1: a shared git remote, pull requests, owner-only merges", "docs/reviews/…Claude_Proposal_D-051.md"],
    ["20 Oct", "ChatGPT reviews it: <i>conditional approval with amendments</i>", "docs/reviews/…ChatGPT_Review_of_D-051.md"],
    ["20 Oct", "Claude's revision 2 adopts all amendments, narrowing one", "docs/reviews/…Claude_Revised_Proposal_D-051.md"],
    ["20 Oct, 14:40", "Corbin approves running a <b>pilot</b> (Q9). The decision itself waits for the pilot result", "DECISIONS.md §4"],
    ["21 Oct, 09:10", "Pilot passed. Corbin <b>accepts D-051</b> (Q15)", "DECISIONS.md §4, Part V"],
], [1.0 * inch, 3.3 * inch, 2.2 * inch]))
s.append(Spacer(1, 6))
s.append(P("ChatGPT's amendments are the reason the workflow is lean rather than bureaucratic:"))
s += bullets([
    "<b>Proportionate process.</b> Code, data and the substance of decisions get an independent review. Pure wording "
    "and formatting fixes take a lighter path, but still need the owner's merge.",
    "<b>One authoritative review record.</b> A review exists in one place, not copied into three.",
    "<b>Approval names a specific revision.</b> Approving one commit never silently covers commits added later.",
    "<b>Software verification is not scientific validation.</b> Passing tests show the code behaves as specified. "
    "They say nothing about whether the anatomy or biomechanics is right.",
    "<b>Test tool access; don't assume it.</b> Each model's actual GitHub abilities had to be demonstrated before the "
    "process relied on them. This mattered a great deal (Section 6).",
])

s.append(P("5. The workflow", h1))
s.append(KeepTogether([workflow_diagram(),
                       P("Figure 1. One build-and-review cycle under D-051. Either model can hold either role.", cap)]))
s.append(P("The essential rules, condensed from D-051's thirteen items:", body))
s += bullets([
    "<b>One canonical repository.</b> Local folders are working copies.",
    "<b>Only Corbin integrates into " + code("main") + ".</b> A GitHub ruleset blocks direct pushes, deletion and "
    "history rewriting on " + code("main") + ", and allows only “merge commit” merges, so imported history is never "
    "flattened.",
    "<b>Work happens on branches</b> named after phase, model and topic (e.g. " + code("phase-b/chatgpt-d037") + "). "
    "Each pull request description carries the handoff: start and head SHA, what changed, the commands run and "
    "their results, and open questions.",
    "<b>Reviews are pinned to a full SHA</b> and state plainly what the reviewer executed and what it only read. "
    "A model reviewing its own work does not count as independent verification.",
    "<b>Only pushed commits count as snapshots.</b> Uncommitted work is never “the reviewed state.”",
    "<b>Fallback:</b> when a model can't reach GitHub, it gets a GitHub archive of a named commit. The handoff says "
    "which method was used.",
])

s.append(P("6. The pilot: what actually happened", h1))
s.append(P("The pilot used real work: ChatGPT's review of Claude's Phase A implementation. Times are US Eastern."))
s.append(table([
    ["PR", "Author", "What it did", "Merged"],
    ["#1", "Claude", "Imported the project's existing git history into Corbin's course repository with one merge "
     "commit, so no existing commit ID changed. Added a test configuration the combined layout needed.", "20 Oct 15:08"],
    ["—", "Corbin", "Created the ruleset protecting " + code("main") + ".", "21 Oct 08:24"],
    ["#2", "ChatGPT", "Phase A review of commit 4abb4f1: <b>AMEND</b>, five findings (three medium, two low). "
     "Execution was not possible yet.", "08:48"],
    ["#3", "Claude", "Reproduced findings A1–A3 (each bad record was accepted), fixed A1–A4, added 15 tests and "
     "automated checks (CI).", "08:49"],
    ["#5", "ChatGPT", "Re-review at 29e256e: <b>AGREE</b> with the fixes; flagged stale records; test execution "
     "<b>blocked</b> (see below).", "09:01"],
    ["#4", "Claude", "Recorded Corbin's answers and the re-review results.", "09:01"],
    ["#7", "ChatGPT", "<b>Independent execution:</b> 80 tests passed, integrity check passed, 9 of 9 malformed-data "
     "probes rejected, all run by ChatGPT itself.", "09:12"],
    ["#6", "Claude", "Owner rulings on physical bounds; verification statuses upgraded; D-051 and D-052 accepted.",
     "09:13"],
    ["#8", "Claude", "Phase B roles recorded: ChatGPT builds, Claude reviews.", "09:16"],
], [0.4 * inch, 0.75 * inch, 4.35 * inch, 1.0 * inch]))
s.append(Spacer(1, 4))
s.append(P("<b>The execution problem and its fix.</b> ChatGPT could read any commit through its GitHub connector, "
           "push branches and open pull requests. Its code sandbox, though, could reach neither GitHub nor the Python "
           "package index, and one required package (pint, for physical units) was missing. ChatGPT reported its "
           "first attempt honestly as <i>blocked</i>; it did not work around the gap. Claude built a bundle of the "
           "official package files, checked each file's SHA-256 fingerprint against the one PyPI publishes, and "
           "tested the bundle offline with ChatGPT's exact package versions. Corbin uploaded the bundle with a GitHub "
           "archive of the commit. ChatGPT then installed it, verified the fingerprints, matched three files against "
           "GitHub's records of that commit, and ran every check itself."))

s.append(P("7. What the pilot taught us", h1))
s += bullets([
    "<b>Cross-model review finds real defects.</b> Three of ChatGPT's five findings were demonstrated to let bad "
    "records through. The 15 new tests were shown to catch them: run against the old code, the 11 tests aimed at the "
    "defects fail, and the 4 acceptance tests pass.",
    "<b>Status labels stay honest.</b> Results moved from “reported by author” to “independently checked "
    "(software)” only when the other model ran them. One check, which needs full git history, still carries the "
    "author-reported label, because nobody else has run it.",
    "<b>The records police themselves.</b> ChatGPT caught out-of-date state files. A duplicated review copy was "
    "removed so that one authoritative record remained. A formatting slip by Claude was caught and fixed in the open.",
    "<b>Process slips are visible and recoverable.</b> One pull request was merged before its re-review. The log "
    "recorded that, and the decision stayed “Proposed” until the review and the owner's acceptance came in.",
    "<b>Tooling surprises surface early.</b> Claude's session could not push git tags, so tags were dropped; commit "
    "IDs do the same job. A test tool that silently checked the wrong code after a refactor was found and changed to "
    "fail loudly.",
])

s.append(P("8. The case for GitHub", h1))
for head, txt in [
    ("Reproducibility.", "A commit ID pins code, data and documentation together. Anyone (a peer, an advisor, a third "
     "model) can retrieve that exact state and rerun the checks. This is the project's own rule applied to its "
     "process: the simulation must be able to say what number it used, and why."),
    ("Verification you can check.", "Independent review only means something if both parties examined the same thing. "
     "SHA-pinned reviews make that provable, and it is what let ChatGPT's independent run confirm Claude's results "
     "rather than merely echo them."),
    ("Human authority, enforced and traceable.", "AI models propose; the owner decides. Branch protection makes "
     "" + code("main") + " change only through a reviewed pull request that Corbin merges, and each approval is tied "
     "to a specific revision and quoted word for word in the decision log."),
    ("Better reviews.", "A pull request shows exactly what changed, line by line. Reviews are durable files, not "
     "chat messages that scroll away."),
    ("Less overhead, fewer errors.", "No downloading, re-uploading or recreating files, so no transcription mistakes."),
    ("An audit trail for academic work.", "The history shows who proposed, built, reviewed and approved each change, and "
     "keeps human and model contributions distinguishable. That matters when AI-assisted work is assessed."),
    ("Roles are interchangeable.", "Phase B swaps builder and reviewer with no change to the process. Another model "
     "could join under the same rules."),
    ("Standard, free and transferable.", "Git, pull requests and continuous integration are everyday software-engineering "
     "practice, not a bespoke system."),
]:
    s.append(P(f"<b>{head}</b> {txt}"))

s.append(P("9. Limitations and open risks", h1))
s.append(P("These are recorded in D-051 and in the project state file, not hidden:", ParagraphStyle("kwn", parent=body, keepWithNext=1)))
s += bullets([
    "<b>Shared account.</b> Both models act through Corbin's GitHub account, so GitHub's author labels cannot tell them "
    "apart. Every review and handoff therefore names its author in the text. “Only Corbin merges” is enforced against "
    "direct pushes, but between Corbin and the models it remains a rule followed, not a technical barrier.",
    "<b>Public repository.</b> Corbin chose to keep the repository public, so anyone can read it. Its full history was "
    "scanned for credentials before the import, and none were found.",
    "<b>Uneven tool access.</b> ChatGPT's test runs depend on owner-supplied archives and offline packages, and tools "
    "that need git history cannot run in its sandbox.",
    "<b>CI is supporting evidence only.</b> Automated checks run in a third environment, but they do not replace a "
    "reviewer reproducing results.",
    "<b>Scope of verification.</b> Every check here concerns software behaviour. None of it establishes anatomical, "
    "biomechanical or clinical validity, which needs sources read and judged by people.",
    "<b>Process weight.</b> ChatGPT's guiding principle for the workflow applies: “It must remain simpler than the "
    "research process it supports.”",
])

s.append(P("10. Doing this yourself", h1))
s.append(table([
    ["Step", "What to do"],
    ["1", "Put the project in a GitHub repository and scan its full history for passwords or keys before sharing it."],
    ["2", "Protect " + code("main") + ": require pull requests, block force-pushes and deletion, and allow merge commits only."],
    ["3", "Connect each AI model's GitHub integration, then <i>test</i> what each can actually do: read a commit, "
     "check one out, run the tests, push a branch, open a PR. Write the results down."],
    ["4", "Agree on a handoff format: start and head SHA, changes, commands run with results, open questions."],
    ["5", "Have reviews name the exact SHA and separate what was executed from what was only read."],
    ["6", "Keep a decision log and a short project-state file in the repository, and update both in the same pull requests."],
    ["7", "Run a small pilot on real work before relying on the process, and keep a fallback (commit archives)."],
], [0.5 * inch, 6.0 * inch]))

s.append(P("Records referenced", h2))
s.append(P("All in github.com/Corb1nW/Independent-Study:", small))
for r in [
    "docs/DECISIONS.md: D-041 (multi-model protocol), D-042 to D-048 (record-keeping rules), D-051 (this workflow, "
    "with Amendments 1–3), D-052 (Phase A review response); §4 approval record Q9–Q17 and owner actions A-1 to A-4",
    "PROJECT_STATE.md: capability table, pilot pass criteria, validation results",
    "docs/reviews/2026-10-20_Claude_Proposal_D-051.md, 2026-10-20_ChatGPT_Review_of_D-051.md, "
    "2026-10-20_Claude_Revised_Proposal_D-051.md",
    "docs/reviews/2026-10-21_ChatGPT_Phase_A_Review_4abb4f1.md, 2026-10-21_Claude_Response_to_Phase_A_Review.md, "
    "2026-10-21_ChatGPT_ReReview_D052_29e256e.md, 2026-10-21_ChatGPT_D052_Execution_Addendum_29e256e.md",
    "Pull requests #1 to #8; .github/workflows/tests.yml",
]:
    s.append(Paragraph(r, ParagraphStyle("ref", parent=small, leftIndent=12, bulletIndent=2, spaceAfter=2),
                       bulletText="•"))

doc.build(s)
print("ok", OUT)
