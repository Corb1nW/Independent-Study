# Stage D4 demonstration re-review

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Reviewed SHA (full):** `88767760fe7ac596fbb46d00bce5835c4cb2144b`
- **Base SHA (full):** `cf60811244c3eb6900fafa322c87bd5fb5d535e5`
- **Previous reviewed SHA:** `3216c83054e16bff1feccae1f5dd8570fab841ab`
- **Build PR:** [#51](https://github.com/Corb1nW/Independent-Study/pull/51)
- **Scope:** D4-DEMO-02 remainder, the changes since the preceding review, and the Q78 record.
- **Independence:** Claude implemented the fix following my finding. I ran the tests, CLI probes and comparisons.
- **Verdict:** AGREE
- **Must fix before Corbin decides:** None.
- **Status:** REVIEWED, NOT APPROVED

**D4-DEMO-02 resolved.** I repeated the explicit edited-growth case through the normal command-line entry point. The female mass changed from 61.9 to 62.9 kg while the input’s original execution SHA and provenance fields stayed intact. The resulting page used the supplied mass and marked the data custom. It removed the embedded provenance label, verified-input counts and every acceptance status. The growth provenance row and A1–A9 rows use the custom notice. The source captions and verification explanation identify the supplied files, and the timeline is labelled as context about the official runs.

I repeated the same checks with edited `--assembled` and `--d3` inputs. All three custom outputs contained no `verified_git_head_and_inputs` string and had null provenance, counts and acceptance statuses. I inspected the template bindings governing the captions, acceptance rows and growth card. [Claim stripping](https://github.com/Corb1nW/Independent-Study/blob/88767760fe7ac596fbb46d00bce5835c4cb2144b/tools/build_squat_demo_d4.py#L532-L547) · [Source captions](https://github.com/Corb1nW/Independent-Study/blob/88767760fe7ac596fbb46d00bce5835c4cb2144b/tools/squat_demo_d4_template.html#L443-L453) · [Acceptance and provenance rows](https://github.com/Corb1nW/Independent-Study/blob/88767760fe7ac596fbb46d00bce5835c4cb2144b/tools/squat_demo_d4_template.html#L764-L775) · [Regression](https://github.com/Corb1nW/Independent-Study/blob/88767760fe7ac596fbb46d00bce5835c4cb2144b/tests/test_squat_demo_d4.py#L223-L250)

**D4-DEMO-01 and D4-DEMO-03 remain resolved.** I recursively compared the official embedded data with the previous reviewed page. The only difference was one timeline sentence identifying the official page’s runs. The body-specific actuator parameters and the solver units and tolerances agree with the preceding review.

At the reviewed SHA, `python -m pytest -q` passed **454 tests** using Python 3.13.5 and the project’s locked packages. `python -m src.integrity` passed, all nine invalid-input probes were rejected, and `python -m tools.build_segment_datasets --check` exited 0. The checkout remained clean.

Two default CLI rebuilds matched the committed page byte for byte, with SHA-256 `56dc5967ed616d34e837de25d911a3a6294024c328f71902efd38ac8706ae323`. An explicitly supplied byte-identical growth file reproduced that page as well. I changed a working copy of each default manifest and confirmed that its loader returned the exact archived bytes instead. All three configured digests matched their archive commits.

I checked the generated JavaScript syntax with `node --check`. Browser playback remains Claude’s reported check. The local HTML restriction encountered during the first review prevented an independent visual check in this environment.

The full diff since `3216c83054e16bff1feccae1f5dd8570fab841ab` is confined to the demonstration, its tests and the decision records. Q78 agrees with the handoff and is attributed to Claude’s session. [Author response](https://github.com/Corb1nW/Independent-Study/pull/51#issuecomment-6958924893) · [Q78](https://github.com/Corb1nW/Independent-Study/blob/88767760fe7ac596fbb46d00bce5835c4cb2144b/docs/DECISIONS.md#L194)

Corbin decides whether to merge the demonstration.
