# Stage D4 squat demonstration review

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Reviewed SHA (full):** `3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5`
- **Base SHA (full):** `cf60811244c3eb6900fafa322c87bd5fb5d535e5`
- **Build PR:** [#51](https://github.com/Corb1nW/Independent-Study/pull/51)
- **Scope:** The D4 demo, its builder and tests, the D3 rename and the Q75, Q76 and A-21 records.
- **Independence:** Claude wrote the presentation and builder. I ran the verification and wrote the independent data and altered-input checks.
- **Verdict:** AMEND
- **Must fix before Corbin decides:** Correct the actuator card’s body-specific parameters, pin the source manifests, and correct the verification explanation.
- **Status:** REVIEWED, NOT APPROVED

## D4-DEMO-01 (High) — The actuator card shows the wrong parameters for two bodies

The builder takes the actuator parameters from the first row of the 16-muscle manifest, the female moving-knee run. The card uses those values for every selection in both sets. The animated paths, forces and activations update with the selection. I compared the embedded fields against each of the six moving-knee runs. All 28 displayed fibre and slack lengths for the male body and for Gait2392 were wrong in the 14-muscle set, and all 32 per body were wrong in the growth set. The default Gait2392 biceps femoris long head shows 105.1 mm fibre and 314.2 mm slack. The official Gait2392 run uses 109.0 mm and 326.0 mm. [Builder](https://github.com/Corb1nW/Independent-Study/blob/3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5/tools/build_squat_demo_d4.py#L351-L376) · [Card binding](https://github.com/Corb1nW/Independent-Study/blob/3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5/tools/squat_demo_d4_template.html#L570-L591)

Read the selected actuator’s parameters from the selected body and set’s run. Keep the ontology facts and the C2 whole-motion maxima labelled with their own scope. Add a regression that checks the card’s parameters for both sets and all three bodies.

## D4-DEMO-02 (High) — The archived manifest contents can drift under the original provenance label

The footer promises a byte-identical rebuild from pinned inputs. The builder pins the ontology and configuration, then reads all three manifests directly from their current working-tree paths. In a scratch fixture at the default path, I changed the assembled female run’s mass from 61.9 to 62.9 kg and left the manifest metadata alone. Running the default builder wrote the altered mass into the page with the same official commit `af21e78` and `verified_git_head_and_inputs` label. The same unpinned read supplies the D3 points. The manifest’s original run provenance does not verify the artifact the demo reads today. [Manifest reads](https://github.com/Corb1nW/Independent-Study/blob/3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5/tools/build_squat_demo_d4.py#L176-L196) · [CLI](https://github.com/Corb1nW/Independent-Study/blob/3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5/tools/build_squat_demo_d4.py#L489-L498) · [Footer](https://github.com/Corb1nW/Independent-Study/blob/3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5/tools/squat_demo_d4_template.html#L815-L819)

Check the three default artifacts against pinned digests or Git blobs from their archive commits before rendering. Treat optional input overrides as custom unless they match the official records. Add a regression that changes a number at a default manifest path with the same embedded execution SHA and demonstrates that the page cannot silently acquire the old verified label.

## D4-DEMO-03 (Medium) — The verification text misstates the KKT unit and the A5 control

The mechanics table shows the aggregate optimizer KKT residual in N·m and leaves the allowed value blank. The D2 configuration used by the D4 run gives this check unit `1` and tolerance `1e-8`. The stated activation agreement also has a nonzero tolerance (`1e-5`). Show the configured unit and limits and describe agreement within tolerance. The A5 panel also says each test holds path data fixed and requires failure. Its joint-centre control constructs a new path, checks that the crossing remains, and passes C2 with negligible leverage. Describe the failure probes and that positive control accurately. [Verification markup](https://github.com/Corb1nW/Independent-Study/blob/3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5/tools/squat_demo_d4_template.html#L740-L743) · [Solver tolerances](https://github.com/Corb1nW/Independent-Study/blob/3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5/config/phase_d2_muscles.yaml#L10-L15) · [A5 introduction](https://github.com/Corb1nW/Independent-Study/blob/3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5/tools/squat_demo_d4_template.html#L312-L317) · [Joint-centre test](https://github.com/Corb1nW/Independent-Study/blob/3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5/tests/test_phase_d4.py#L637-L658)

## Independent checks

At the pinned head on Linux x86-64 with Python 3.13.5 and the project’s locked dependencies, `python -m pytest -q` passed **447 tests**. `python -m src.integrity` passed, all nine invalid-input probes were rejected, and `python -m tools.build_segment_datasets --check` exited 0. A clean rebuild matched the committed D4 HTML byte for byte (SHA-256 `b1d04371e8035f9aeb88d58d619feaec4344b04943d10639062c3c928ae6f446`). The renamed D3 HTML matched `main`’s former `SQUAT_DEMO.html` byte for byte.

I parsed the committed HTML’s data independently and compared all six moving-knee display cases to the source manifests. Time, motion, torques, activations, forces, path points and D3 joint positions match at their display precision. I checked the mechanics maxima, oracle values and nine A2 rows. I also recalculated H1 from the archived activation series. The three D3 values round to 0.113, 0.130 and 0.136, and the growth values round to 0.000.

The browser environment blocked loading the local HTML. I inspected the generated data and the template bindings directly. The desktop and phone Chrome checks in the handoff are Claude’s reported runs.

The PR handoff and decision log agree on the quoted scope and technical audience in Q75 and Q76. The original quotations are attributed to Claude’s session. I independently checked the two A-21 merges and their reported times against GitHub. [Decision record](https://github.com/Corb1nW/Independent-Study/blob/3bbd758f871c2a0cd212cff6d8e7a2540b7b24d5/docs/DECISIONS.md#L190-L192) · [PR #49](https://github.com/Corb1nW/Independent-Study/pull/49) · [PR #50](https://github.com/Corb1nW/Independent-Study/pull/50)

Corbin decides whether to merge the demonstration.
