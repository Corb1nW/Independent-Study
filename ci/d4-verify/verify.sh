#!/usr/bin/env bash
# Stage D4 verification job (D-062; requested by Corbin for ChatGPT's independent re-runs, PR #48).
#
#   bash ci/d4-verify/verify.sh TARGET_DIR TARGET_SHA COMPARE_REF OUT_DIR
#
# TARGET_DIR is a Git checkout of TARGET_SHA (full 40 characters). COMPARE_REF is a ref or SHA, fetched in that
# checkout, holding the committed official D4 manifests to compare with. Every step runs; each writes its log to
# OUT_DIR/logs; the job fails at the end if any required step failed. Python packages must already be installed from
# ci/d4-verify/requirements.lock.
set -u
TARGET_DIR=$(cd "$1" && pwd); SHA="$2"; COMPARE="$3"; OUT=$(mkdir -p "$4" && cd "$4" && pwd)
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT/logs" "$OUT/manifests" "$OUT/references" "$OUT/comparisons"
FAILED=()
step() {  # step NAME COMMAND... : run in the target checkout, log, record failure
  local name="$1"; shift
  echo "::group::$name"
  ( cd "$TARGET_DIR" && "$@" ) 2>&1 | tee "$OUT/logs/$name.log"
  local rc=${PIPESTATUS[0]}
  echo "exit code: $rc" | tee -a "$OUT/logs/$name.log"
  echo "::endgroup::"
  [ "$rc" -eq 0 ] || FAILED+=("$name")
}

# 0. What is being verified, and with what.
{
  echo "target_sha=$SHA"
  echo "checked_out_head=$(git -C "$TARGET_DIR" rev-parse HEAD)"
  echo "compare_ref=$COMPARE ($(git -C "$TARGET_DIR" rev-parse "$COMPARE" 2>/dev/null || echo unresolved))"
  echo "verifier_commit=${GITHUB_SHA:-local}"
  python -c "import sys, platform; print('python', sys.version.replace(chr(10), ' ')); print('platform', platform.platform())"
  python -c "import opensim; print('opensim', opensim.__version__)"
  python -m pip freeze
} 2>&1 | tee "$OUT/logs/00_environment.log"
[ "$(git -C "$TARGET_DIR" rev-parse HEAD)" = "$SHA" ] || { echo "checked-out HEAD is not $SHA"; exit 1; }
git -C "$TARGET_DIR" status --porcelain | tee "$OUT/logs/00_worktree_status.log"
[ -z "$(git -C "$TARGET_DIR" status --porcelain)" ] || { echo "checkout is not clean"; exit 1; }

# 1-4. The standard checks.
step 01_pytest python -m pytest -q
step 02_integrity python -m src.integrity
step 03_invalid_input_probes python tools/review_cycle1_probes.py
step 04_dataset_check python -m tools.build_segment_datasets --check

# 5. Oracle references: coverage of each committed file, then a fresh OpenSim regeneration compared value by value.
for ref in "$TARGET_DIR"/tests/data/*_oracle_reference.json; do
  base=$(basename "$ref" .json)
  mode=$(python -c "import json,sys; print(json.load(open(sys.argv[1]))['provenance']['knee_mode'])" "$ref")
  spec=$(python -c "import json,sys; print(json.load(open(sys.argv[1]))['provenance'].get('model_specification', 'squat_d2'))" "$ref")
  step "05_coverage_$base" python -m tools.oracle_coverage "tests/data/$base.json" --knee "$mode"
  step "06_regenerate_$base" python -m tools.make_d2_oracle --knee "$mode" --spec "$spec" --output "$OUT/references/$base.json"
  step "07_compare_$base" python "$HERE/compare_reference.py" "$ref" "$OUT/references/$base.json" "$OUT/comparisons/$base.json"
done

# 8. Both D4 runs at the target commit (each verifies its own provenance against TARGET_SHA).
short=${SHA:0:7}
for cfg in "$TARGET_DIR"/config/phase_d4_*.yaml; do
  name=$(basename "$cfg" .yaml)
  step "08_run_$name" python -m tools.run_phase_d4 --config "config/$name.yaml" --commit-sha "$SHA" \
       --output "$OUT/manifests/${name}_runs_$short.json"
done

# 9. Compare with the committed official manifests for this commit, if COMPARE_REF holds them.
for kind in assembled iliopsoas; do
  committed=$(git -C "$TARGET_DIR" ls-tree -r --name-only "$COMPARE" -- results/phase_d 2>/dev/null \
              | grep -E "_d4_${kind}_runs_${short}\.json$" | head -1)
  regen="$OUT/manifests/phase_d4_${kind}_runs_$short.json"
  if [ -n "$committed" ] && [ -f "$regen" ]; then
    git -C "$TARGET_DIR" show "$COMPARE:$committed" > "$OUT/comparisons/committed_$(basename "$committed")"
    step "09_compare_manifest_$kind" python "$HERE/compare_manifest.py" \
         "$OUT/comparisons/committed_$(basename "$committed")" "$regen" "$OUT/comparisons/manifest_$kind.json"
  else
    echo "no committed D4 $kind manifest for $short at $COMPARE; comparison skipped" | tee "$OUT/logs/09_compare_manifest_$kind.log"
  fi
done

# Summary.
{
  echo "# D4 verification of $SHA"
  echo
  echo "| Step | Result |"; echo "|---|---|"
  for f in "$OUT"/logs/[0-9][0-9]_*.log; do
    n=$(basename "$f" .log); rc=$(tail -1 "$f" | sed -n 's/^exit code: //p')
    echo "| $n | ${rc:-n/a} |"
  done
  echo
  if [ ${#FAILED[@]} -eq 0 ]; then echo "**All required steps passed.**"; else echo "**Failed: ${FAILED[*]}**"; fi
} > "$OUT/SUMMARY.md"
cat "$OUT/SUMMARY.md"
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && cat "$OUT/SUMMARY.md" >> "$GITHUB_STEP_SUMMARY"
[ ${#FAILED[@]} -eq 0 ]
