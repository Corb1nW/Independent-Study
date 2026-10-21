# Phase B — right-hip data-to-dynamics proof (D-036 / D-053)

**Builder submission; unreviewed by Claude. Outputs are NOT validated anatomical, physiological or clinical predictions.** Corbin controls merge.

The pelvis is a fixed reference frame (LB:FRAME:PELVIS); thigh is the single moving effective body in the sagittal plane. The right hip angle (LB:DOF:HIP_FLEX_EXT_R) has flexion-positive q and an explicit model-neutral reference pose. All numbers in config/phase_b_hip.yaml, including the constant 0.04 m extension arm, 1 kg*m^2 effective thigh inertia and activation 0.02, are **round demonstration assumptions** and each has a rationale and unit. No source claims support them as anatomical measurements. The actual force source is the validated Arnold 2010 whole-gluteus model observation (LB-QD:GMAX:FMAX:ARNOLD2010); whether Arnold Fmax means fiber or effective tendon force needs later scientific verification. The Phase B law is a deliberately simplified gain, not a Hill force-length-velocity formulation.

Dynamics: I qdd = -r0 a Fmax_right + external_torque. Acceleration is constant, so the model uses the exact constant-acceleration quadratic inside each fixed time step (no new packages). Crossing of [-pi/6,pi/3] terminates the trajectory at its first analytically located boundary time and records domain_exit. Boundary start outward direction uses velocity; if velocity is zero, net angular acceleration (Claude N2). No clamping or implied joint-limit force. The domain is a demonstration operating range, not an anatomical ROM.

Scenario YAML is separate from canonical evidence. The right-only multiplier (baseline 1.0; perturbed 1.2) is a model sensitivity assumption, **not an altered Arnold measurement**; loader validates ontology laterality, datum ID and positive finite multiplier (N3). Canonical bilateral evidence remains unchanged. The scenario affects only the right-side effective input. Config and scenario source files remain reviewable and versioned.

After Claude reviews and Corbin accepts this build, run in a checked-out repository:

    python -m pytest -q
    python -m src.integrity
    python tools/review_cycle1_probes.py
    python -m tools.run_phase_b --commit-sha FULL_40_CHARACTER_SHA --output /tmp/phase_b_runs.json

The manifest includes every numeric config input with units and assumption rationale, validated source ID and source claims, dataset/config/scenario SHA256, right and left forces, equations, event time/state and tolerance, plus an explicit full SHA. It verifies that the supplied SHA matches git HEAD when git history exists; archive-only runs label that SHA as caller supplied and unverified. Disclosure: omitting cos(pennation) can give approximately 7.8% higher torque at Ward's illustrative 21.9 degree mean **if** Fmax represents fiber force; this is not a verified Arnold correction. Pennation is not used in this simulation.

**Limitations:** no gravity or other joint moments beyond configured external torque, passive structures, muscle-path geometry, tendon, activation dynamics, segment shape or validated inertia. These tests verify software wiring and elementary mechanics only. Before treating baseline or perturbation outcomes as project results, Claude must independently review the build PR.
