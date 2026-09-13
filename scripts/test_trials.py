#!/usr/bin/env python3

"""Regression tests for trial counts in artifact workflow scripts."""

from __future__ import annotations

import csv
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT_DIR = Path(__file__).resolve().parent.parent
WORKFLOW_FILES = (
    "scripts/bench_unique_cell.sh",
    "scripts/bench_unique_block.sh",
    "scripts/run_reproduction.sh",
    "scripts/run_smoke.sh",
    "scripts/summarize_results.py",
    "scripts/compare_paper_results.py",
    "claims/claim2/paper-results.csv",
    "claims/claim3/paper-results.csv",
    "claims/claim2/run.sh",
    "claims/claim3/run.sh",
)
EXPECTED_MARKER = "Total 4/4 matches found!"
FAKE_BINARY = r"""#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$FPSI_TEST_CALLS"
if (( FPSI_TEST_FAIL )); then
    exit 7
fi
mode=normal
assumption=uniqCel
side=recv
metric=0
dimension=2
delta=32
size=256
trials=1
verify=0
while (( $# )); do
    case "$1" in
        -prefix) mode=prefix; shift ;;
        -sender) side=send; shift ;;
        -assumption)
            if [[ $2 == 1 ]]; then assumption=uniqBlk; fi
            shift 2 ;;
        -p) metric=$2; shift 2 ;;
        -d) dimension=$2; shift 2 ;;
        -delta) delta=$2; shift 2 ;;
        -nn) size=$((1 << $2)); shift 2 ;;
        -try) trials=$2; shift 2 ;;
        -v) verify=$2; shift 2 ;;
        *) shift ;;
    esac
done
if [[ $mode == prefix && $delta == 30 ]]; then
    exit 2
fi
if (( verify )); then
    for ((trial = 0; trial < trials - FPSI_TEST_MISSING_MARKERS; ++trial)); do
        echo "Total 4/4 matches found!"
    done
fi
if (( ! FPSI_TEST_MISSING_RESULTS )); then
    printf '[%s] %s-%s L%s %s %s %s 10.00 1.00\n' \
        "$mode" "$assumption" "$side" "$metric" "$dimension" "$delta" "$size"
fi
"""


class TrialsWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = tempfile.TemporaryDirectory(prefix="fpsi-trials-test-")
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        for source_file in WORKFLOW_FILES:
            destination = self.root / source_file
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT_DIR / source_file, destination)
        binary = self.root / "code/build/fpsi"
        binary.parent.mkdir(parents=True)
        binary.write_text(FAKE_BINARY, encoding="utf-8")
        binary.chmod(0o755)
        environment = self.root / "scripts/collect_environment.sh"
        environment.write_text("#!/usr/bin/env bash\necho test-environment\n", encoding="utf-8")
        environment.chmod(0o755)
        self.calls = self.root / "calls.txt"
        self.run_count = 0

    def run_workflow(
        self, script: str, *arguments: str, trials: str | None = "2", **overrides: str
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        self.run_count += 1
        result_dir = self.root / f"results-{self.run_count}"
        self.calls.write_text("", encoding="utf-8")
        environment = os.environ.copy()
        for variable in ("TRIALS", "FPSI_BIN", "FPSI_NS"):
            environment.pop(variable, None)
        environment.update(
            FPSI_RESULT_DIR=str(result_dir),
            VERIFY="1",
            FPSI_TEST_CALLS=str(self.calls),
            FPSI_TEST_FAIL="0",
            FPSI_TEST_MISSING_MARKERS="0",
            FPSI_TEST_MISSING_RESULTS="0",
        )
        if trials is not None:
            environment["TRIALS"] = trials
        environment.update(overrides)
        result = subprocess.run(
            ["bash", str(self.root / script), *arguments],
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
        )
        if result.returncode == 0:
            self.assertNotIn("trial(s)", result.stdout)
        return result, result_dir

    def assert_summary(self, result_dir: Path, configurations: int, trials: int) -> None:
        with (result_dir / "summary.csv").open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            self.assertEqual(
                reader.fieldnames,
                [
                    "mode", "assumption", "side", "metric", "dimension", "delta", "size",
                    "trials", "communication_mb_mean", "runtime_s_mean",
                ],
            )
        self.assertEqual(len(rows), configurations)
        self.assertEqual({int(row["trials"]) for row in rows}, {trials})
        self.assertEqual({float(row["communication_mb_mean"]) for row in rows}, {10.0})
        self.assertEqual({float(row["runtime_s_mean"]) for row in rows}, {1.0})

    def test_claim_matrices(self) -> None:
        for claim, mode, configurations, log_name in (
            (2, "--full", 90, "unique-cell.txt"),
            (2, "--light", 30, "unique-cell.txt"),
            (3, "", 90, "unique-block.txt"),
        ):
            with self.subTest(claim=claim, mode=mode):
                arguments = [mode] if mode else []
                result, result_dir = self.run_workflow(f"claims/claim{claim}/run.sh", *arguments)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assert_summary(result_dir, configurations, 2)
                with (result_dir / "paper-comparison.csv").open(encoding="utf-8") as handle:
                    compared = list(csv.DictReader(handle))
                self.assertEqual(len(compared), configurations)
                self.assertFalse((result_dir / "paper-statistics.csv").exists())
                self.assertFalse((result_dir / "paper-speedups.csv").exists())
                figures = list((result_dir / "paper-plots").glob("*.svg"))
                self.assertEqual(len(figures), 1 if mode == "--light" else 3)
                self.assertTrue((result_dir / "paper-comparison.md").is_file())
                log_lines = (result_dir / log_name).read_text(encoding="utf-8").splitlines()
                self.assertEqual(log_lines.count(EXPECTED_MARKER), configurations * 2)
                calls = self.calls.read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(calls), configurations)
                self.assertTrue(all("-try 2 " in call for call in calls))

    def test_default_trial_count(self) -> None:
        result, result_dir = self.run_workflow("claims/claim2/run.sh", "--light", trials=None)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assert_summary(result_dir, 30, 1)
        self.assertEqual(result.stdout.splitlines().count(EXPECTED_MARKER), 30)

    def test_reproduction_modes(self) -> None:
        for mode, configurations in (("--quick", 6), ("--light", 120), ("--full", 180)):
            with self.subTest(mode=mode):
                result, result_dir = self.run_workflow("scripts/run_reproduction.sh", mode)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assert_summary(result_dir, configurations, 2)
                smoke_name = "quick.txt" if mode == "--quick" else "smoke.txt"
                smoke_lines = (result_dir / smoke_name).read_text(encoding="utf-8").splitlines()
                self.assertEqual(smoke_lines.count(EXPECTED_MARKER), 12)
                self.assertIn("PASS: 6 protocol cases and 1 parameter guard", result.stdout)

    def test_missing_markers_fail(self) -> None:
        for script, arguments in (
            ("claims/claim2/run.sh", ["--light"]),
            ("claims/claim3/run.sh", []),
            ("scripts/run_reproduction.sh", ["--quick"]),
        ):
            with self.subTest(script=script):
                result, result_dir = self.run_workflow(
                    script, *arguments, FPSI_TEST_MISSING_MARKERS="1"
                )
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("correctness markers", result.stdout)
                self.assertFalse((result_dir / "summary.csv").exists())

    def test_missing_results_fail(self) -> None:
        for script in ("claims/claim2/run.sh", "claims/claim3/run.sh"):
            with self.subTest(script=script):
                result, result_dir = self.run_workflow(script, FPSI_TEST_MISSING_RESULTS="1")
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("result rows", result.stdout)
                self.assertFalse((result_dir / "summary.csv").exists())

    def test_protocol_failures_propagate(self) -> None:
        for script in WORKFLOW_FILES:
            if not script.endswith(".sh"):
                continue
            with self.subTest(script=script):
                result, result_dir = self.run_workflow(script, FPSI_TEST_FAIL="1")
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual(len(self.calls.read_text(encoding="utf-8").splitlines()), 1)
                self.assertFalse((result_dir / "summary.csv").exists())

    def test_invalid_trials_fail_before_execution(self) -> None:
        for script in WORKFLOW_FILES:
            if not script.endswith(".sh"):
                continue
            for trials in ("0", "-1", "abc", "1.5", "01", "2147483648", "999999999999999999999"):
                with self.subTest(script=script, trials=trials):
                    result, _ = self.run_workflow(script, trials=trials)
                    self.assertEqual(result.returncode, 2, result.stdout)
                    self.assertIn("TRIALS must be an integer", result.stdout)
                    self.assertEqual(self.calls.read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()
