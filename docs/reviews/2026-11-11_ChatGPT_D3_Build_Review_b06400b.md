# Stage D3 build review — D-060 Amendment 1

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Reviewed SHA:** `b06400b4c7bf00a023a570b47fdb95a95c6cb079`
- **Base SHA:** `ad11987d1a458ab4fb65462219c2ac533bc5f0c8`
- **Official run SHA:** `525e2c302a8062f8d962da4dfbc8d813b54a97c0`
- **PR:** [#41](https://github.com/Corb1nW/Independent-Study/pull/41)
- **Date:** 2026-11-11
- **Verdict:** **AMEND**. Both scope notes are resolved and the D3 computations reproduce. Correct the results record and viewer and report the remaining simplification comparison before Corbin decides.
- **Status:** **REVIEWED, NOT APPROVED**

## Scope and independence

Reviewed the D-060 Amendment 1 build against the scope accepted in Q62, including the dataset, kinematics, inverse dynamics, muscle geometry, OpenSim references, runner, comparison and viewer. D-058 supplies the frozen baseline and mechanics criteria. D-059 supplies the force law, recruitment rule and muscle checks. D-055 supplies the manifest and traceability requirements. The release commit is the review head's parent. The four differences from release to review head are the two records and the two generated D3 artifacts.

Claude authored the D3 implementation and release artifacts. Their execution and comparison were independent of Claude. I self-checked the guidance I authored in D3-N01 and D3-N02, the comparison code and probes I used for this review, and inherited ChatGPT work exercised by the regression suite.

## Execution

Both detached checkouts had the expected full HEAD and a clean Git status. Git objects were reconstructed from the repository's Git data and matched their object IDs. The sparse checkouts excluded the binary phase-overview PDF. It is outside the D3 execution inputs. Linux x86-64, CPython 3.12.14, NumPy 2.3.5, SciPy 1.17.0, quadprog 0.1.14, Clarabel 0.11.1, OpenSim 4.6, pytest 9.2.0, PyYAML 6.0.3, Pydantic 2.13.4, Pint 0.26.2 and SymPy 1.14.0.

At `b06400b4c7bf00a023a570b47fdb95a95c6cb079`, I ran the following commands with output files outside the checkout.

```bash
python -m pytest -q
python -m src.integrity
python tools/review_cycle1_probes.py
python -m tools.build_segment_datasets --check
python -m tools.make_d2_oracle --knee moving --output /tmp/d3_moving_oracle.json
python -m tools.make_d2_oracle --knee fixed --output /tmp/d3_fixed_oracle.json
```

263 tests passed. Integrity passed. The validator rejected all nine deliberate bad inputs. Generated datasets were current. Both OpenSim runs exited zero. OpenSim warned that optional visualization meshes were unavailable. Its regenerated position, geometry and force values matched exactly.

At `525e2c302a8062f8d962da4dfbc8d813b54a97c0`, I ran the official commands with the committed fixed-knee inputs.

```bash
python -m tools.run_phase_d3 \
  --commit-sha 525e2c302a8062f8d962da4dfbc8d813b54a97c0 \
  --d1-manifest results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json \
  --d2-manifest results/phase_d/2026-11-10_d2_muscle_runs_7ac0f2d.json \
  --output /tmp/d3_rerun.json
python -m tools.build_d2_page \
  --manifest results/phase_d/2026-11-10_d2_muscle_runs_7ac0f2d.json \
  --moving-manifest /tmp/d3_rerun.json --output /tmp/d3_rerun.html
```

| Output | Comparison with the file at the reviewed SHA |
|---|---|
| D3 run manifest | Byte-identical, including 157,376 numeric values and all statuses. SHA-256 `c8766da3adba0e1a4285195944af24c4edc404c01f38b5e43d5dcd9d2e85fd3f` |
| D3 viewer | Byte-identical. SHA-256 `4a84b3924b155e54347a39c4314d51f870c5d57c44a79ec273cd2284e5519524` |
| Moving-knee OpenSim oracle | All 75,817 numeric values identical. Differences in the Python, NumPy and platform strings. Both model hashes and the tool hash match. |
| Fixed-knee OpenSim oracle | All 70,098 numeric values identical. The same environment fields differ, plus the new `knee_mode` field and the updated oracle-tool hash. Both model hashes match. |

My recursive comparator checked the full JSON structures and values, and recomputed each of the 28 D3 input SHA-256 hashes and committed Git blob IDs at the run SHA. The inputs have the same bytes at the review head. The D1 reference is `dd89fff908eb9f5002c2f62d36bccf5bc6694330` and the D2 reference is `7ac0f2d2d83752d43f85a4221923f43f54e26b61`. All 301 stored times and poses align for each body across the three runs. D1 and D2 store the same fixed-knee torques. I recalculated the peak reserve, flagged sample count and heel margin directly from the outputs.

| Body | Peak stage-1 reserve, fixed → moving (N·m) | Flagged samples, fixed → moving | Moving heel margin (mm) |
|---|---:|---:|---:|
| Female | 0 → 0 | 0 → 0 | 17.176 |
| Male | 5.814680 → 0 | 27 → 0 | 17.840 |
| Gait2392 | 6.361827 → 0 | 28 → 0 | 20.334 |

All three bodies passed the D1 mechanics tolerances, the kinematics check and the optimizer verification. Contact was feasible and the force law had zero domain flags. The maximum Newton–Euler/Kane difference was `4.27e-14 N·m`, the kinematics difference was `6.67e-16 m`, and the maximum KKT residual was `1.43e-13`. Against the fresh moving-knee OpenSim oracle, the implementation agreed within `2.78e-16 m` in path length, `1.98e-16 m` in moment arm and `1.57e-11 N` in tendon force. The tests exercise the force law at the conditional-point boundaries and in both passive settings. The D3 baseline uses zero passive force and the accepted D2 optimizer. These results support the fixed-knee explanation for the demonstrated squat under the declared assumptions.

I executed the regenerated page's script with a Node DOM fixture, selected the male body at 1.50 s and switched moving → fixed → moving. The selection, time, feasibility readouts and run SHAs switched correctly. The assumptions panel reproduced D3-B02 below. Desktop and phone layout rendering remains Claude-reported. Local Chromium failed at startup with `socket() failed: Operation not permitted`.

## Earlier notes

| Note | Disposition | Evidence |
|---|---|---|
| D3-N01 | **Resolved** | Direct OpenSim tibia-origin queries in femur axes give +6.289864 mm anterior and −21.120820 mm inferior from 0° to 100°. The built spline agrees with the native positions at 0°, 30°, 60° and 100° within `5.21e-18 m`. |
| D3-N02 | **Resolved** | Smooth T(0) minus the historical D1 datum is −0.401592 mm horizontal and +0.080506 mm vertical. The frozen mode uses D1's datum and returns zero translation derivatives. Across all three bodies it matches D1 within `2.85e-14 N·m` in torque and `8.68e-17 m` in centre of pressure. The frozen torques round to every stored official D1 torque. Transforming each moving thigh COM back into femur axes returns its D1 hip-relative location at the four tested poses. |

The previous D2 fixes remain resolved. All existing observations in the Gait2392 segment dataset were preserved and the generated moving-knee observation was added.

## Blocking findings

### D3-B01 — High — The activation summary overstates saturation and removal of co-contraction

The results paragraph below the D-060 Amendment 1 comparison table in `docs/DECISIONS.md` says the gluteus maximus is fully active at the bottom for all three bodies. The D3 manifest's `series.activation` gives these values at sample 150, 1.50 s.

| Body | Gluteus maximus upper / middle / lower | Rectus femoris | All three vasti |
|---|---|---:|---:|
| Female | 0.188682 / 0.474273 / 0.477005 | 0.443337 | 1 |
| Male | 0.568897 / 1 / 1 | 1 | 1 |
| Gait2392 | 0.806062 / 1 / 1 | 1 | 1 |

At 1.50 s both gastrocnemius heads and tibialis anterior are at zero, and soleus is active in all three bodies. Across the full trajectory there is still simultaneous gastrocnemius and tibialis activity. The maximum of the smaller of tibialis activation and the larger gastrocnemius activation is 0.113, 0.130 and 0.136 for female, male and Gait2392.

**Fix I would accept.** State that the vasti reach full activation at the bottom for all bodies. State that rectus femoris and the middle and lower gluteus maximus compartments reach full activation there for male and Gait2392. Limit the co-contraction claim to the disappearance of the large bottom-of-squat pattern and say that simultaneous activity remains elsewhere. Use the measured activations to describe saturation. Omit the quantitative implication of “little margin” unless a capacity margin is actually measured.

### D3-B02 — High — Moving-knee viewer describes the fixed knee and fixed-knee torques

The generated D3 viewer identifies `525e2c3` and displays the moving-knee torques, while its assumptions say “D1's fixed-centre knee” and “D1's inertial torques are kept”. The panel reads `DATA.assumptions` from the fixed manifest on every switch (`tools/build_d2_page.py:413`). The data adapter also selects the D2 assumptions for the moving manifest (`tools/build_d2_page.py:46–53`).

**Fix I would accept.** Populate each mode's assumptions from that mode's manifest and render `V.assumptions`. In D3, explicitly say the D1 motion is retained and both inverse dynamics and muscle geometry use the moving knee. Include the D3 configuration's assumptions and the applicable D2 muscle assumptions, with the fixed-knee and fixed-torque clauses removed. Regenerate the viewer and check that the assumptions, feasibility and provenance change together when switching modes.

### D3-B03 — Medium — The D-060 item 5 simplification comparison is missing from the run report

D-060 item 5 applies D-059 check 8f to the remaining ankle and foot effects. The moving-knee oracle records matched and unmodified moment arms, and the D3 manifest assembly (`tools/run_phase_d3.py:217–243`) omits the per-actuator simplification sizes. Check 8f requires reporting the measured differences as a diagnostic.

I paired the fresh oracle's 31 `unmodified_geometry` rows with the same-index `geometry` rows of kind `d1_sample` and verified that their poses were identical. The largest absolute moment-arm differences were 4.39304 mm at the ankle (tibialis anterior), 0.01877 mm at the knee (lateral gastrocnemius), and numerical round-off at the hip. Both OpenSim models use the moving knee, so the differences reflect the remaining ankle and foot changes.

**Fix I would accept.** Include the 8f comparison in the D3 manifest as maximum absolute moment-arm difference in mm for each actuator and coordinate on the existing 31 poses. Identify the two knee-kept models and mark it reported-only. The existing reference rows and D2 reporting approach are sufficient. Regenerate the manifest and viewer from the amended release SHA and confirm the original D3 series and verification outcomes.

## Nonblocking note

**D3-N03 — Medium — Check that the kinematics oracle covers the motion grid.** `tests/test_phase_d3.py:76–84` checks the count and model hash, and `tools/run_phase_d3.py:64–77` evaluates the poses provided by the rows. An in-memory reference with 301 copies of the upright row passed both the test and the residual check (`2.61e-18 m`). The actual regenerated reference covers each of the 301 expected poses in order, independently checked against the D1 motion. When updating the verification, require unique ordered indices, matching poses and finite position components so that a repeated or stale reference fails.

## Sources and limits

Checked the vendored Gait2392 XML, generated moving and fixed knee observations, original D1/D2 result files, OpenSim 4.6 comparisons, and the D3 use of the existing source records in `sources/SOURCES.md`. The knee joint XML is identical in the source and the moving-knee oracle copy. All cited sources are already registered. The Q62 quote and approval basis were read in the Git handoff. The original Claude conversation was unavailable for direct quote verification. Claude's four mutation runs and browser layout checks are author-reported. This Linux execution verifies the stated computation. Measured squat data, individual applicability and physiological and clinical validation are outside this review.

## Handoff

**D3-B01, D3-B02 and D3-B03 must be fixed before Corbin decides.** Claude can address all three findings in the current PR. ChatGPT should check the amended SHA and regenerated artifacts, and Corbin makes the merge decision.
