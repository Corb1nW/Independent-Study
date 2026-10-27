# Independent Study development protocol — v0.2 candidate

**Status: proposed, not adopted, not active.** Until Corbin approves a pinned SHA of these files through a decision entry (proposed D-054), work continues under D-041 (as amended by D-045), D-045, D-047, D-048 and D-051.

These files are the single, version-controlled procedure that both models follow, whichever model holds which role.

| File | Purpose | Author |
|---|---|---|
| `CORE.md` | Rules for every role: authority, D-047 scope, statuses, approvals, authorship, independence, light path, records | ChatGPT; amendments [G1]–[G10] by Claude |
| `BUILDER.md` | Builder procedure | ChatGPT; amendments by Claude |
| `REVIEWER.md` | Reviewer procedure | Claude |
| `checklists/handoff_contract.md` | Builder handoff, filled in the PR description | ChatGPT; two lines by Claude |
| `checklists/review_record.md` | Reviewer record template | Claude |
| `checklists/verification.md` | Conditional checks for both roles | ChatGPT |
| `checklists/edge_cases.md` | Role-swap and repository edge cases | ChatGPT; items by Claude |

**Read order:** `CORE.md`, then your role file, then the checklists it names. Always read these files from the repository at the current `main`, or at the candidate SHA you were given, never from a copy in a chat.

**Precedence:** accepted decisions in `docs/DECISIONS.md`, then owner instructions recorded verbatim, then these files. Report any conflict as a proposed amendment (CORE).

## Platform entry points (proposed; not installed)

The rules live only in these files. Entry points just point to them, and carry no rules of their own.

**ChatGPT.** Text for the Independent Study project instructions:

> At the start of any Independent Study task, read `docs/protocols/CORE.md` and the role file for your assigned role (`BUILDER.md` or `REVIEWER.md`) from `Corb1nW/Independent-Study` at the current `main` or the SHA you are given. Confirm your role from an owner record. If you cannot read the repository, ask for a commit archive and say which method you used.

**Claude.** `BUILDER.md` and `REVIEWER.md` carry `name` and `description` frontmatter, the format of a Claude skill. If they are installed as skills, each must still read `docs/protocols/CORE.md` from the repository, because a skill copy can go stale. Equivalent text for the claude.ai Project instructions:

> At the start of any Independent Study task, read `docs/protocols/CORE.md` and the file for your assigned role from the repository at the current `main` or the given SHA, and confirm the role from an owner record.

Neither platform is known to load these files automatically. A session that has not read them is not following the protocol, whatever its role.
