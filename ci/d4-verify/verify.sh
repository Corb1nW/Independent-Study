#!/usr/bin/env bash
# Stage D4 verification job (D-062; requested by Corbin for ChatGPT's independent re-runs, PR #48).
#
#   bash ci/d4-verify/verify.sh TARGET_DIR TARGET_SHA COMPARE_REF OUT_DIR [required|optional]
#
# TARGET_DIR is a Git checkout of TARGET_SHA (full 40 characters). COMPARE_REF is a commit SHA, branch or tag in
# that checkout (a branch may also be found as origin/<branch>) holding the committed official D4 manifests to
# compare with. It is resolved to a commit before anything runs; a ref that does not resolve stops the job
# (ChatGPT D4-B05). With "required" (the default) the job also stops at once if that commit holds no official
# manifest of either D4 run for TARGET_SHA; with "optional" a missing manifest is reported as "unavailable".
# Every check then runs; each writes its log to OUT_DIR/logs; the job fails at the end if any step failed. Python
# packages must already be installed from ci/d4-verify/requirements.lock.
set -u
TARGET_DIR=$(cd "$1" && pwd); SHA="$2"; COMPARE="$3"; OUT=$(mkdir -p "$4" && cd "$4" && pwd); MODE="${5:-required}"
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT/logs" "$OUT/manifests" "$OUT/references" "$OUT/comparisons"
FAILED=()
KINDS=(assembled iliopsoas)
stop() {  # stop MESSAGE : a precondition failed; record it and end the job before any check runs
  echo "$1" | tee "$OUT/logs/00_inputs.log"
  printf '# D4 verification of %s\n\n**Stopped before the checks:** %s\n' "$SHA" "$1" > "$OUT/SUMMARY.md"
  [ -n "${GITHUB_STEP_SUMMARY:-}" ] && cat "$OUT/SUMMARY.md" >> "$GITHUB_STEP_SUMMARY"
  exit 1
}
case "$MODE" in required|optional) ;; *) stop "comparison mode must be required or optional" ;; esac
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || stop "TARGET_SHA must be a full 40-character lowercase SHA"
[[ "$COMPARE" =~ ^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$ ]] || stop "COMPARE_REF must be a commit SHA or a branch or tag name"
COMPARE_SHA=$(git -C "$TARGET_DIR" rev-parse --verify --quiet "$COMPARE^{commit}" \
              || git -C "$TARGET_DIR" rev-parse --verify --quiet "origin/$COMPARE^{commit}" || true)
[ -n "$COMPARE_SHA" ] || stop "COMPARE_REF $COMPARE does not resolve to a commit in the checkout"
short=${SHA:0:7}
LISTING=$(git -C "$TARGET_DIR" ls-tree -r --name-only "$COMPARE_SHA" -- results/phase_d) \
  || stop "cannot list results/phase_d at $COMPARE_SHA"
declare -A COMMITTED
for kind in "${KINDS[@]}"; do
  found=$(printf '%s\n' "$LISTING" | grep -E "_d4_${kind}_runs_${short}\.json$" || true)
  [ "$(printf '%s' "$found" | grep -c .)" -le 1 ] || stop "more than one official D4 $kind manifest for $short at $COMPARE_SHA"
  COMMITTED[$kind]="$found"
  if [ -z "$found" ] && [ "$MODE" = required ]; then
    stop "comparison required, but $COMPARE_SHA holds no official D4 $kind manifest for $short"
  fi
done
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
  echo "compare_ref=$COMPARE -> $COMPARE_SHA (comparison $MODE)"
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
for cfg in "$TARGET_DIR"/config/phase_d4_*.yaml; do
  name=$(basename "$cfg" .yaml)
  step "08_run_$name" python -m tools.run_phase_d4 --config "config/$name.yaml" --commit-sha "$SHA" \
       --output "$OUT/manifests/${name}_runs_$short.json"
done

# 9. Compare with the committed official manifests for this commit at COMPARE_SHA.
for kind in "${KINDS[@]}"; do
  committed="${COMMITTED[$kind]}"
  regen="$OUT/manifests/phase_d4_${kind}_runs_$short.json"
  log="$OUT/logs/09_compare_manifest_$kind.log"
  if [ -z "$committed" ]; then      # only reachable with "optional"
    { echo "comparison unavailable: $COMPARE_SHA holds no official D4 $kind manifest for $short"; echo "result: unavailable"; } | tee "$log"
  elif [ ! -f "$regen" ]; then
    { echo "the run did not write $regen, so it cannot be compared with $committed"; echo "exit code: 1"; } | tee "$log"
    FAILED+=("09_compare_manifest_$kind")
  else
    git -C "$TARGET_DIR" show "$COMPARE_SHA:$committed" > "$OUT/comparisons/committed_$(basename "$committed")"
    step "09_compare_manifest_$kind" python "$HERE/compare_manifest.py" \
         "$OUT/comparisons/committed_$(basename "$committed")" "$regen" "$OUT/comparisons/manifest_$kind.json"
  fi
done

# Summary.
{
  echo "# D4 verification of $SHA"
  echo
  echo "Official manifests compared from \`$COMPARE\` = \`$COMPARE_SHA\` (comparison $MODE)."
  echo
  echo "| Step | Result |"; echo "|---|---|"
  for f in "$OUT"/logs/[0-9][0-9]_*.log; do
    n=$(basename "$f" .log); rc=$(tail -1 "$f" | sed -n 's/^exit code: //p; s/^result: //p')
    echo "| $n | ${rc:-n/a} |"
  done
  echo
  if [ ${#FAILED[@]} -eq 0 ]; then echo "**All required steps passed.**"; else echo "**Failed: ${FAILED[*]}**"; fi
} > "$OUT/SUMMARY.md"
cat "$OUT/SUMMARY.md"
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && cat "$OUT/SUMMARY.md" >> "$GITHUB_STEP_SUMMARY"
[ ${#FAILED[@]} -eq 0 ]
