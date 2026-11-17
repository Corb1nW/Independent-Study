# D-063 Stage D5 scope review

- **Reviewed by (model):** ChatGPT
- **Proposed by (model):** Claude
- **Reviewed SHA (full):** `c3adca05556d9affdaa7e21cec757ce9d04a6e75`
- **Base SHA (full):** `1076704133c1e0af9fb2bf9623e30e16243285a7`
- **Proposal PR:** [#53](https://github.com/Corb1nW/Independent-Study/pull/53)
- **Scope:** Blocking findings only on D-063, Q79 and Q80, its anatomy and actuator boundaries, lumped representation, C3 policy, A1–A8 and H2–H4.
- **Independence:** I did not write this proposal. I ran the checks and the probes described below.
- **Verdict:** AMEND
- **Must fix before Corbin decides:** D5-R01 and D5-R02.
- **Status:** REVIEWED, NOT APPROVED

The direction fits Q80. The proposal includes both sides’ lower-limb anatomy, supplies Gait2392 actuators where available, retains the prescribed squat and D4 physics, and labels the later measured-data and forward-simulation stages as future work. The new anatomy and lumped-actuator mappings will require their source checks during the build.

## D5-R01 (High) — Bound the C3 exceptions so incorrect actions still fail

Item 4 sends undeclared sagittal actions through C3’s reference mechanism, and A3 requires those disagreements to appear in C5. The current mechanism computes the reference disagreement set using the same ontology capabilities being checked. Agreement with OpenSim geometry therefore cannot establish that an anatomical capability is correct. [Proposal item 4](https://github.com/Corb1nW/Independent-Study/blob/c3adca05556d9affdaa7e21cec757ce9d04a6e75/docs/DECISIONS.md#L2774) · [Current C3](https://github.com/Corb1nW/Independent-Study/blob/c3adca05556d9affdaa7e21cec757ce9d04a6e75/src/consistency.py#L216-L235)

I used the committed moving-knee OpenSim reference’s 301 D1 samples with the D4 specification. Unmodified C3 passed. I changed biceps femoris long head’s declared knee action from flexion to extension, leaving all geometry fixed. C3’s ordinary moving-knee policy failed. Supplying the matched moving-knee reference made the same altered case pass with both `reference_confirmed` and `same_samples_as_reference` true, despite 301 biceps-femoris disagreements. This is the broader use of the reference mechanism proposed for D5.

**Fix I would agree to.** Define explicit expected deviations for the affected actuators and coordinates, with their source or model basis, and require a deviation to be both declared and confirmed by the OpenSim reference. A newly introduced or expanded disagreement outside those declarations must fail. Add that requirement to A3/A6 so a wrong non-exempt capability remains detectable after the new muscles enter. The representation and numeric tolerances can be settled in the build.

## D5-R02 (High) — Authorize the generic preparation the data-only steps need

Item 5 says the lumped schema and check change is the stage’s only code change. The proposed inherited specification and complete C5 inventory need additional generic support. [Items 3–6 and step 1](https://github.com/Corb1nW/Independent-Study/blob/c3adca05556d9affdaa7e21cec757ce9d04a6e75/docs/DECISIONS.md#L2773-L2779) · [A1, A2 and A4](https://github.com/Corb1nW/Independent-Study/blob/c3adca05556d9affdaa7e21cec757ce9d04a6e75/docs/DECISIONS.md#L2792-L2795)

- I added an in-memory executable specification extending `squat_d4_iliopsoas`, without adding any actuator. The shared specification resolver inherited the 16 actuators correctly. The oracle generator’s `actuators_for()` raised `KeyError('actuators')`, because it expects its immediate parent to hold a direct actuator list. The proposed `squat_d5` uses this same nested inheritance.
- I added an in-memory skeletal-muscle inventory probe whose only crossing was the existing unmodelled MTP joint. It appeared nowhere in the current C5 register. C5 restricts its unactuated-muscle list to muscles crossing a retained joint, so the anatomy-only foot entries promised by item 6 and A4 cannot enter that list through data alone.

[Oracle actuator resolution](https://github.com/Corb1nW/Independent-Study/blob/c3adca05556d9affdaa7e21cec757ce9d04a6e75/tools/make_d2_oracle.py#L54-L64) · [Recursive specification resolver](https://github.com/Corb1nW/Independent-Study/blob/c3adca05556d9affdaa7e21cec757ce9d04a6e75/src/model_spec.py#L165-L188) · [C5 filter](https://github.com/Corb1nW/Independent-Study/blob/c3adca05556d9affdaa7e21cec757ce9d04a6e75/src/consistency.py#L377-L383)

**Fix I would agree to.** Expand step 1 to cover generic infrastructure for lumped representation, nested specification consumers, the bounded C3 policy, a complete anatomy-to-actuator inventory, and any reporting support needed for A8. Require the inventory to identify muscles without an actuator even when they cross no retained joint. Reuse the shared recursive specification resolver for the oracle. Then keep the actuator and foot additions in steps 3–5 subject to the existing no-`src/`/`tools/` change requirement. Correct the “only code change” statement accordingly. This is a scope change to authorize preparation before the anatomy additions.

## Checks and evidence

At the pinned proposal SHA, `python -m pytest -q` passed **454 tests** with Python 3.13.5 and the locked packages. Integrity passed, all nine invalid-input probes were rejected, and the dataset check exited 0. The checkout stayed clean. These checks cover the existing software. The D5 implementation is proposed.

I parsed the vendored OpenSim XML and current ontology. There are 46 actuators on each side, including three trunk actuators per side. Of the 43 lower-limb actuators per side, 16 are in the growth specification and 27 remain, matching the proposal’s list. The two C5 inventories contain 17 and 15 unactuated entries. The H3 baseline also matches the records. Middle and lower gluteus-maximus peaks are 1.0 in the male and Gait2392 moving-knee runs, and about 0.49 in the female run.

I checked the primary [OpenSim model documentation](https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53086215), already registered as `SRC:OPENSIM_GAIT2392`. I also checked the indexed text of the proposed [StatPearls Foot Muscles chapter](https://www.ncbi.nlm.nih.gov/books/NBK539705/) for the cited count. That chapter is absent from `sources/SOURCES.md` at this SHA and needs registration before its anatomy is used. I have not checked every proposed muscle’s attachments, crossings or innervation. D-063 A4 assigns that work to the build.

The exact source interpretation for `gem_r`, the foot inventory’s counting convention, and the torque-share report belong in the build review. H2–H4 are stated as hypotheses to report regardless of outcome, which is appropriate. Deferring passive force and tendon compliance gives the anatomical additions a clear comparison against D4.

Q79 and Q80 agree with the PR handoff, including the all-lower-limb selection and scope review before the build. Their quotations are attributed to Claude’s session. [Owner direction](https://github.com/Corb1nW/Independent-Study/blob/c3adca05556d9affdaa7e21cec757ce9d04a6e75/docs/DECISIONS.md#L196-L197)

Corbin decides D-063 after this review.
