# Role skills

Both AI models (ChatGPT and Claude) follow these skills on this project. Each model uses whichever skill matches the role Corbin assigned it. Corbin assigns roles, decides, and merges.

| Skill | Use when |
|---|---|
| [`independent-study-builder/SKILL.md`](independent-study-builder/SKILL.md) | You are building: changing code, data or documents |
| [`independent-study-reviewer/SKILL.md`](independent-study-reviewer/SKILL.md) | You are reviewing the other model's work |

**These files are the master copies.** Corbin installs the same files in each model's skills section. When a skill changes, update it here through a PR, then reinstall it in both models so neither runs an old version.

If a skill conflicts with an accepted decision in `docs/DECISIONS.md`, the decision wins.

History: the skills were condensed on 2026-10-27 from a longer protocol drafted and reviewed in PR #16, which was closed without merging. That protocol is kept, not in force, in `docs/archive/protocol-v0.2-candidate/`; its review records are in `docs/reviews/2026-10-27_*`. The decision record is D-054.
