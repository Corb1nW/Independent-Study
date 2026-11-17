# Stage D4 squat demonstration re-review

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Reviewed SHA (full):** `3216c83054e16bff1feccae1f5dd8570fab841ab`
- **Base SHA (full):** `cf60811244c3eb6900fafa322c87bd5fb5d535e5`
- **Previous reviewed SHA:** `3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5`
- **Build PR:** [#51](https://github.com/Corb1nW/Independent-Study/pull/51)
- **Scope:** D4-DEMO-01 to D4-DEMO-03, the presentation and builder, and the Q77 record.
- **Independence:** Claude implemented the changes following my earlier review. I ran the tests and independently checked the archived inputs and the generated data.
- **Verdict:** AMEND
- **Must fix before Corbin decides:** Keep official verification and provenance claims off pages built from custom manifests.
- **Status:** REVIEWED, NOT APPROVED

## Finding dispositions

**D4-DEMO-01 resolved.** I checked all 90 actuator entries across the three moving-knee bodies and two muscle sets against the archived D4 manifests. All four parameters match at display precision. The template reads `r.params[selected]` from the chosen body and set. Biceps femoris fibre and slack lengths are 109.0 and 326.0 mm for Gait2392, 105.4 and 315.3 mm for the male body, and 105.1 and 314.2 mm for the female body. The C2 maxima are labelled with their full scope. [Builder](https://github.com/Corb1nW/Independent-Study/blob/3216c83054e16bff1feccae1f5dd8570fab841ab/tools/build_squat_demo_d4.py#L276-L298) · [Card](https://github.com/Corb1nW/Independent-Study/blob/3216c83054e16bff1feccae1f5dd8570fab841ab/tools/squat_demo_d4_template.html#L572-L594)

**D4-DEMO-02 partly resolved (High).** All three default artifacts match the SHA-256 values of their Git archives at `ba4c921` or `b5967e7`. In a disposable detached checkout I changed the female mass in both D4 files and a D3 knee point at their default paths. The default command still reproduced the committed page byte for byte. An explicitly supplied byte-identical growth file also reproduced the official page. [Pinned loader](https://github.com/Corb1nW/Independent-Study/blob/3216c83054e16bff1feccae1f5dd8570fab841ab/tools/build_squat_demo_d4.py#L42-L53) · [Archive handling](https://github.com/Corb1nW/Independent-Study/blob/3216c83054e16bff1feccae1f5dd8570fab841ab/tools/build_squat_demo_d4.py#L194-L223)

I then passed the altered growth file explicitly with `--growth`, leaving its execution SHA and provenance fields intact. The page generated with `official: false` and the modified female mass of 62.9 kg. Its footer says that the page claims no provenance. The growth card still binds `verified_git_head_and_inputs` from the same altered file and shows 32 verified inputs. The A9 row still has `passed: true` and displays `pass (manifest)`. The playback caption still calls both loaded runs official. The custom test checks the banner switch and omits these surviving claims.

Use the custom status to gate the growth provenance row, the A9 proof, and the official or verified descriptions of the loaded data. Keep the stage history as clearly labelled context. Repeat the explicit edited `--growth` case with unchanged manifest metadata and require the custom output to make no official provenance claim about it. [Playback caption](https://github.com/Corb1nW/Independent-Study/blob/3216c83054e16bff1feccae1f5dd8570fab841ab/tools/squat_demo_d4_template.html#L205-L214) · [Acceptance and growth cards](https://github.com/Corb1nW/Independent-Study/blob/3216c83054e16bff1feccae1f5dd8570fab841ab/tools/squat_demo_d4_template.html#L755-L766) · [Footer](https://github.com/Corb1nW/Independent-Study/blob/3216c83054e16bff1feccae1f5dd8570fab841ab/tools/squat_demo_d4_template.html#L819-L824)

**D4-DEMO-03 resolved.** I checked the pinned D2 configuration blob and recalculated the maxima over the six assembled cases. The table uses the configured dimensionless KKT limit of `1e-8`, second-solver reserve limit of `1e-7 N·m` and dimensionless activation limit of `1e-5`. The A5 copy describes the joint-centre path as a positive control and distinguishes it from the failure probes. [Solver table](https://github.com/Corb1nW/Independent-Study/blob/3216c83054e16bff1feccae1f5dd8570fab841ab/tools/squat_demo_d4_template.html#L742-L748) · [A5 panel](https://github.com/Corb1nW/Independent-Study/blob/3216c83054e16bff1feccae1f5dd8570fab841ab/tools/squat_demo_d4_template.html#L314-L319)

## Verification

At `3216c83054e16bff1feccae1f5dd8570fab841ab` with Python 3.13.5 and the locked packages, `python -m pytest -q` passed **453 tests**. Integrity passed, all nine invalid-input probes were rejected, and the dataset check exited 0. Both rebuild probes matched the committed D4 page byte for byte (SHA-256 `ac0fcebbc570af7340f1f81ff8b71fde07daabf6b9714bc9a73a90dfd4a5b04a`). The working tree stayed clean.

I verified the embedded data, the template bindings and the generated JavaScript syntax. Claude’s desktop and phone Chrome runs are reported in the handoff. Local HTML playback was blocked in my browser environment.

The diff is confined to the demo, tests and project records. Q77’s wording matches the handoff and is attributed to Claude’s session. [Author response](https://github.com/Corb1nW/Independent-Study/pull/51#issuecomment-6958422199) · [Q77](https://github.com/Corb1nW/Independent-Study/blob/3216c83054e16bff1feccae1f5dd8570fab841ab/docs/DECISIONS.md#L193)

Corbin decides on the demonstration.
