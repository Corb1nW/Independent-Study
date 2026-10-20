"""Mutation check for the Phase A tests (DECISIONS.md D-025).

Shows the Phase A tests can fail: it temporarily replaces the current
QuantitativeSchema.validate_datum with the baseline (d04fb78) version, runs
tests/test_phase_a.py, and restores the file. Expected at 4abb4f1: 30 of 47 fail
(the remaining 17 check data content and structure, not the validator).

    python tools/mutation_check_phase_a.py      # from the repository root; needs git
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "quantitative.py"
BASELINE = "d04fb78"

current = TARGET.read_text(encoding="utf-8")
old = subprocess.run(["git", "show", f"{BASELINE}:src/quantitative.py"], cwd=ROOT,
                     capture_output=True, text=True, check=True).stdout
old_fn = old[old.index("    def validate_datum(self, datum):"):old.index("    def dataset_observations")]
mutated = current.replace("    def validate_datum(self, datum):",
                          old_fn + "\n    def _phase_a_validate_datum(self, datum):", 1)
try:
    TARGET.write_text(mutated, encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                             "tests/test_phase_a.py"], cwd=ROOT, capture_output=True, text=True)
    print("With baseline validate_datum:", result.stdout.strip().splitlines()[-1])
finally:
    TARGET.write_text(current, encoding="utf-8")
print("src/quantitative.py restored.")
