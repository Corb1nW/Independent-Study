#!/usr/bin/env bash
# Resolve and validate the d4-verify job's inputs (ChatGPT D4-B05). Reads only environment variables, never
# expands an input into code, and prints "name=value" lines for $GITHUB_OUTPUT:
#   sha         the full 40-character commit under test
#   compare     the ref or SHA holding the official D4 manifests to compare with
#   comparison  "required" when compare_ref was given explicitly (a missing manifest fails the job),
#               "optional" when it defaults to the verifier's own commit (a missing manifest is reported as
#               unavailable)
#   openblas    an OpenBLAS kernel name to force (OPENBLAS_CORETYPE), or empty for the processor's own
# Environment: EVENT (github.event_name), REF_NAME (github.ref_name), INPUT_SHA, INPUT_COMPARE, INPUT_OPENBLAS
# (workflow_dispatch inputs), VERIFIER_SHA (github.sha).
set -euo pipefail
if [ "${EVENT:-}" = "workflow_dispatch" ]; then T="${INPUT_SHA:-}"; else T="${REF_NAME#verify/}"; fi
if ! [[ "$T" =~ ^[0-9a-f]{40}$ ]]; then
  echo "The commit under test must be a full 40-character lowercase SHA." >&2
  exit 1
fi
if [ -n "${INPUT_COMPARE:-}" ]; then
  if ! [[ "$INPUT_COMPARE" =~ ^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$ ]]; then
    echo "compare_ref must be a commit SHA or a branch or tag name (letters, digits, . _ / -; not starting with -)." >&2
    exit 1
  fi
  C="$INPUT_COMPARE"; M=required
else
  C="${VERIFIER_SHA:?}"; M=optional
fi
O="${INPUT_OPENBLAS:-}"
if ! [[ "$O" =~ ^[A-Za-z0-9]{0,32}$ ]]; then
  echo "openblas_coretype must be an OpenBLAS kernel name (letters and digits only), or empty." >&2
  exit 1
fi
printf 'sha=%s\ncompare=%s\ncomparison=%s\nopenblas=%s\n' "$T" "$C" "$M" "$O"
