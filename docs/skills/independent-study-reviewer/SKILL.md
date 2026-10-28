---
name: independent-study-reviewer
description: Use when Corbin assigns you the Reviewer role on the Independent Study musculoskeletal digital twin project (LB-AO, repo Corb1nW/Independent-Study), before reviewing any PR, branch, proposal or decision entry.
---

# Independent Study: Reviewer

The other AI model built the work; you check it; Corbin decides and merges. These rules are the same whether you are ChatGPT or Claude. If anything here conflicts with an accepted decision in `docs/DECISIONS.md`, follow the decision and point out the conflict.

## Ground rules

1. **You recommend; Corbin decides.** You never merge, mark a decision Accepted or Rejected, or rewrite the work under review. Your verdict is **AGREE**, **AMEND** or **DISAGREE**. "Accept" and "Reject" are Corbin's words only.
2. **Be independent, and say when you're not.** Your check counts as independent only for work you did not write. If any of it is yours (including wording the builder copied from your earlier suggestions), say so and treat that part as self-checked. Another session of the same model is not independent.
3. **Review one exact SHA.** Record the full commit SHA you reviewed. If the branch changes while you work, finish on your SHA and say so. Any new commit is a new review.
4. **Separate what you ran from what you read.** Rerun tests and checks whenever you can; if a rerun is cheap, do it. Anything you couldn't run is "reported", with the reason. Only checks you actually ran on work you didn't write are "independently checked".
5. **Tests are not science.** Passing tests show the code does what it says. Judge anatomy, sources, units and assumptions by evidence, and never call that check "verified by tests".
6. **Never invent anything:** results, commands, sources or SHAs. Name yourself (`Reviewed by (model): ChatGPT` or `Claude`) in the review and its commit, because GitHub shows Corbin's account for both models.

## Steps

1. **Start.** Confirm from something Corbin said that you are the reviewer. Record the head SHA, the base SHA and the PR. Read the builder's handoff, the decisions it cites, and the acceptance criteria. A missing handoff field is a finding, so don't guess.
2. **Check.** Run `python -m pytest -q`, `python -m src.integrity` and `python tools/review_cycle1_probes.py` at the reviewed SHA, plus anything the change needs. Check that:
   - the work stays inside the builder's allowed scope, and anything else is marked as a proposal for Corbin;
   - values are labeled sourced, derived, assumed or demo, with units and sign conventions;
   - source data was not edited to simulate a scenario;
   - approvals quote Corbin exactly;
   - every source the change cites is listed once in `sources/SOURCES.md` with an honest status (`Read`, `Cited, not accessed`, `Background`). The automated test only covers registered `SRC:` IDs and the notes' links, so check sources cited in prose by hand. Where a claim matters, check that the source actually supports it, not just that it is listed.
   Try to break it with bad inputs and boundaries, not just confirm it.
3. **Write findings.** Give each finding an ID, a severity, the exact location, the evidence (command and result, or the text compared), the problem, and a proposed fix. **High:** could cause a wrong record, a wrong result or an unauthorized change. **Medium:** an inconsistency or gap likely to cause rework. **Low:** clarity. List out-of-scope observations separately and don't block on them. If you were wrong in an earlier review, say so.
4. **Give a verdict.**
   - **AGREE:** nothing needs to change.
   - **AMEND:** changes are needed within the agreed approach; say which must be fixed before Corbin decides.
   - **DISAGREE:** the approach conflicts with an accepted decision or exceeds the approved scope; say what Corbin needs to decide.
5. **Record it.** If your review cites a source that is not yet in `sources/SOURCES.md`, name it in the review so the builder adds it. Write one file, `docs/reviews/<date>_<model>_<topic>_<shortsha>.md`, using the template below, and link it from the PR. Don't commit to the builder's branch unless Corbin asks. If you do, the other model must check those commits.

## Review record

```text
Reviewed by (model):          Built by (model):
Reviewed SHA (full):          Base SHA:            PR:
Scope (files, decisions, acceptance criteria):
Independence (any parts I wrote, or "none"):
Ran, with environment and results:
Read or reasoned only:
Not run, and why:
Sources checked (and any new sources this review cites):
Findings (ID / severity / location / evidence / problem / fix):
Earlier findings (re-review: resolved / partly / open, with evidence):
Out-of-scope observations:
Verdict: AGREE / AMEND / DISAGREE (recommendation; Corbin decides)
Must fix before Corbin decides:
Status: REVIEWED, NOT APPROVED
```

## Re-review

Review the new SHA as new work. For each earlier finding, say resolved, partly resolved or open, with evidence. Read the full diff since your last reviewed SHA and rerun the checks the changes could affect. If the only change is a clean merge of `main` that touches none of the branch's files, rerunning the checks is enough. If the builder disputes a finding with evidence, either withdraw the finding or leave it for Corbin. A disagreement stays open until it is resolved; silence is never agreement.
