# Protocol v0.2 Integration Record

**Author:** Claude (integrator of ChatGPT's Builder text; author of the Reviewer material and amendments G1–G10)
**Verified base:** `main` at `6c8b6ef96b2a8f41667fb7e80ae002d068b0fbfb` (merge of PR #14, 2026-10-27 18:17:58 −04:00), `docs/DECISIONS.md` revision 10
**Branch:** `protocol/claude-v0.2-integration`. The PR description gives the head SHA, because a file cannot cite the commit that contains it.
**Status:** review candidate. Not adopted, not active, no decision status changed.

## 1. Commits on this branch

| Commit | Author of content | What |
|---|---|---|
| `f5a5911` | ChatGPT and Claude (per file) | Review history, v0.1 to the v0.2 handoff, byte-identical to the exchanged files (§5) |
| `629e66d` | **ChatGPT** (transcribed by Claude) | `CORE.md`, `BUILDER.md`, three checklists, byte-identical to the v0.2 zip (hashes in the commit message) |
| `22bd25c` | Claude | Independent review of `629e66d`: AMEND (minor), G1–G10 |
| `41b7ee2` | Claude | Amendments G1–G10 to ChatGPT's files (`git diff 629e66d 41b7ee2 -- docs/protocols` isolates them) |
| `bf41184` | Claude | `REVIEWER.md`, `checklists/review_record.md`, `README.md` |
| `3ed7388` | Claude | Correction: disclosure that some ChatGPT passages use Claude's R1–R4 wording |
| this commit | Claude | This record |

**What ChatGPT should independently review:** everything Claude authored, i.e. `41b7ee2`, `bf41184`, `3ed7388`, this record, and the passages listed in the disclosure in `22bd25c`/`3ed7388`. It should also confirm the transcription hashes in `f5a5911` and `629e66d` against its own copies. **What Claude independently reviewed:** ChatGPT's text at `629e66d`, except the disclosed passages.

## 2. Decision verification at `6c8b6ef`

Each decision was read in full at the base SHA and compared with the protocol text that relies on it.

| Decision | Status at `6c8b6ef` | Relied on by | Result |
|---|---|---|---|
| D-041 | Accepted (amended by D-045) | One model builds, the other reviews against the phase exit criterion; Corbin decides | Consistent. Exit criterion now explicit in REVIEWER §1 |
| D-042 | Accepted | Verbatim approvals; model identity not inferred beyond records | Consistent (CORE Records; unknown authorship) |
| D-043 | Accepted | Three status fields | **G1**: CORE's list was incomplete; fixed by citing §3 |
| D-044 | Accepted | Append-only bodies, labeled corrections | Consistent; light-path exclusion; G7 uses its amendment mechanism |
| D-045 | Accepted | Scoped reproduction; "cheap → do it" | Consistent (BUILDER §4, REVIEWER §2) |
| D-046 | Accepted | Exact commit/file/command references | Consistent (handoff, review record) |
| D-047 | Accepted | Delegated list, reserved list, "when unsure, propose", **record delegated choices** | **G2**: recording duty missing and "where specified" weakened reservation; fixed |
| D-048 | Accepted | `PROJECT_STATE.md` handoff; receiving model checks snapshot | **G3**: rule too literal; fixed. Observed: `PROJECT_STATE.md` is stale at `6c8b6ef` (see §6) |
| D-049 | Accepted (Q13, Q14) | Bounds carry a stated basis | Consistent; not restated |
| D-050 | Accepted (delegated) | Worked example of recorded delegated choices | Cited by G2 |
| D-051 | Accepted (Q15) | Items 3–12 (branches, light path, handoff, pinned reviews, one record, approval per SHA, verification kinds, capabilities), Amendment 3 | Consistent. **G9**: item 3's "when unsure, standard path" added |
| D-052 | Accepted (Q16) | Dataset-scoped validation | Consistent; not restated |
| D-053 | Accepted (Q18) | Approval covers only what it names; overlays never mutate source data; domain-exit rules | Consistent (CORE; verification checklist). Index row still says "Not started" at `6c8b6ef`; PR #15 updates it |

**Next free IDs.** `D-054` is free on `main` and in open PR #15. `Q19` and `A-5` are taken by PR #15 (not yet merged), so the provisional approval IDs below start at `Q20` (G6 applied to this PR).

## 3. Change map: F1–F13 and R1–R7 at `6c8b6ef`

| Item | Implemented in | Note |
|---|---|---|
| F1 D-047 scope | CORE Applicability; BUILDER §2 | Wording tightened by G2 |
| F2 Verbatim owner records | CORE Records; BUILDER §2 | — |
| F3 Status vocabulary | CORE Records | Completed by G1 |
| F4 Light path | CORE Light path; handoff short form | Per R1; G9 added |
| F5 Authorship in text | CORE Provenance; BUILDER §5; handoff; review record | — |
| F6 PR is the authoritative handoff | CORE Review candidate; BUILDER §5 | — |
| F7 ID collisions | CORE Record IDs; BUILDER §5; edge case 7 | Extended to Q/A/C and open PRs by G6 |
| F8 Role-swap edge cases | `edge_cases.md` 1–6; BUILDER §1, §3 | Item 1 amended by G3 |
| F9 Conditional checks | `verification.md` | — |
| F10 Cite, don't restate | CORE header; README precedence; G1 | — |
| F11 Layout | `docs/protocols/` + `README.md` | — |
| F12 Portability | Frontmatter on BUILDER and REVIEWER; README entry points | Not installed |
| F13 Adoption decision | README status; proposed D-054 (§4) | Review-request text removed from the role files |
| R1 Declaration plus escalation | CORE Light path | — |
| R2 Moving `main` | edge case 2; REVIEWER §6 | — |
| R3 Blockers | BUILDER §3; edge case 3 | — |
| R4 Independence | CORE Provenance; REVIEWER §0, §1, §6; review record | Transcription rule added by G5 |
| R5 Reviewer scope | CORE Role permissions; REVIEWER §0 | — |
| R6 Self-application | Author lines in every file; proposed Q21–Q23 | — |
| R7.1 Verified SHA | This record (`6c8b6ef`) | — |
| R7.2 Adopt together | REVIEWER drafted in full; D-054 adopts all files at once | — |
| R7.3 Protocol amendments | CORE Protocol changes | Revised by G7 (amendments to the adoption decision) |
| R7.4 Offset timestamps | CORE Records example | — |
| R7.5 BLOCKED draft PR | BUILDER Review cycle; edge case 4 | — |
| R7.6 Review candidate | CORE Review candidate | — |

## 4. Proposed records (apply after PR #15 merges and on owner approval)

These are not yet in `docs/DECISIONS.md` because open PR #15 edits that file (G6 / edge case 10).

**Proposed §4 entries.** Source: Claude session transcript, America/New_York, `https://claude.ai/code/session_01QzLsFRwL41kF7Mg78i73z7`. Quotes are verbatim.

| Provisional ID | Time | Corbin's statement (verbatim) | Context | Supports |
|---|---|---|---|---|
| Q20 | 2026-10-27 18:27 −04:00 | “I want to generate a set skill that both ChatGPT and Clause [sic] can use to keep our building and checking roles consistent as we chnage [sic] who does them. Here is the proposal for the builder role” | Shared ChatGPT's Builder Skill draft v0.1 | Origin of the protocol work |
| Q21 | 2026-10-27 18:36 −04:00 | “Chat built it and claude reviewed it” | Claude's R6: who authored v0.1? | v0.1 authored by ChatGPT |
| Q22 | 2026-10-27 18:36 −04:00 | “yes” | Claude: “Should [v0.2] follow the same pattern, with ChatGPT drafting and me reviewing?” | v0.2: ChatGPT drafts, Claude reviews |
| Q23 | 2026-10-27 18:40 −04:00 | “I want you to proceed with repository implementation and develop the complementary Reviewer Skill.” … “ChatGPT will independently review your Reviewer Skill, your changes to shared governance, and the integrated protocol. Neither model should classify its own work as independently verified.” … “Important: Do not merge or activate the new protocol yet.” … “Final adoption remains subject to my approval.” | Delivery of ChatGPT's v0.2 candidate | Claude integrates and authors the Reviewer skill; ChatGPT reviews Claude's material; no activation |
| Q24 | 2026-10-27 18:53 −04:00 | “1) we should keep the semantics as clear as possible, only I can accpet [sic] or reject” | Q-A: reviewer verdicts AGREE / AMEND / DISAGREE, with Accept/Reject reserved for Corbin? (G4) | Reviewer verdicts AGREE / AMEND / DISAGREE; Accept and Reject used only for owner decisions (interpretation below) |
| Q25 | 2026-10-27 18:53 −04:00 | “2) I approve” | Q-B: approve the records-update rule? (G10) | CORE “Records updates” rule (G10) approved as drafted |

**Interpretation of Q24.** Corbin did not name the three verdict words. Claude reads “only I can accept or reject” as approving G4: reviewers say AGREE / AMEND / DISAGREE, and the words Accept and Reject are reserved for his decisions. **Corbin may correct this interpretation.**

**Scope of Q24 and Q25.** They approve these two rules inside the candidate. They do not adopt the protocol: that still needs ChatGPT's review and Corbin's approval of a pinned SHA (D-054).

**Proposed decision D-054 (Proposed).**

```
### D-054  Shared development protocol (docs/protocols/)
- Decision status:        Proposed
- Implementation status:  In progress (candidate PR, protocol/claude-v0.2-integration)
- Verification status:    Not applicable (process decision); reviews below
- Date:                   proposed 2026-10-27
- Proposed by:            ChatGPT (Builder text, v0.1 and v0.2); Claude (Reviewer text, amendments G1–G10)
- Reviewed by:            Claude (F1–F13, R1–R7, G1–G10); ChatGPT (pending: Claude's material)
- Approval basis:         pending; Q20–Q23 for the process so far; Q24, Q25 for G4 and G10
- Evidence:               docs/reviews/2026-10-27_* records; this integration record
- Amends / supersedes:    operationalizes D-041, D-045, D-047, D-048, D-051; changes none of them
- Phase:                  All
- Open concerns:          none from the owner questions (Q24, Q25)

Decision. CORE.md, BUILDER.md, REVIEWER.md and the four checklists in
docs/protocols/, at the SHA Corbin approves, are the procedure both models
follow in either role. Accepted decisions take precedence over them.
Later protocol changes are amendments to this entry (CORE, G7).
```

## 5. Transcription evidence (`f5a5911`)

SHA-256 of each committed file, identical to the file exchanged in the session:

| File | SHA-256 |
|---|---|
| `2026-10-27_ChatGPT_Builder_Skill_Draft_v0.1.md` | `e66abab9902b98b74cec56948c901c2de82c7f4160aae679ea19f679bf4ecadf` |
| `2026-10-27_Claude_Review_Builder_Skill_v0.1.md` | `a90f1f8aec25caabad9496f18055d662fc31c7f8a0182b41221017f988525322` |
| `2026-10-27_ChatGPT_Response_to_Claude_Builder_Skill_Review_v0.1.md` | `dc9964c34d61db034e2c87b722ad95045c13b72e0d60e6e535ece108551378cb` |
| `2026-10-27_Claude_ReReview_Builder_Skill_Response.md` | `f0db23de5b02ead69045220355725006c1f6e3d9acb5ce643cd2275cd05414a3` (version with the owner records added) |
| `2026-10-27_ChatGPT_Builder_Protocol_v0.2_Handoff.md` | `9a6360de0d371294210669455368f18669220c5128ad8b03ab88e5f73be46b47` |

All source files use LF line endings, so the Git blobs equal the source bytes under `.gitattributes` (`* text=auto`).

## 6. Unresolved questions and observations

- ~~**Q-A (owner):** reviewer verdicts AGREE / AMEND / DISAGREE (G4)?~~ Answered: Q24 (see interpretation in §4).
- ~~**Q-B (owner):** approve the records-update rule (G10)?~~ Answered: Q25, approved.
- **Observation (G3):** at `6c8b6ef`, `PROJECT_STATE.md` still describes Phase B as awaiting review, and the D-036/D-053 index rows say "Not started". Open PR #15 corrects both. This does not affect this task, so under the amended rule it is reported, not fixed here.
- **Merge order:** PR #15 first. Then the proposed records in §4 go in a records PR, with IDs rechecked.
- **Not done:** no protocol file is installed as a skill or as project instructions; no decision status changed.
