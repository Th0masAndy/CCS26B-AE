#!/usr/bin/env python3

"""Compare actual protocol output with generated exact boundary-test answers."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

from generate_boundary_data import METRICS, MODES, expected_intersection, generate


ROOT_DIR = Path(__file__).resolve().parent.parent


def read_points(path):
    return [tuple(map(int, line.split())) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def run_case(binary, source, destination, case, mode, trial, timeout):
    destination.mkdir(parents=True, exist_ok=True)
    for filename in ("sender_data.txt", "recver_data.txt"):
        shutil.copyfile(source / filename, destination / filename)
    output = destination / "output.txt"
    output.unlink(missing_ok=True)
    command = [str(binary), *MODES[mode], "-delta", str(case["delta"]),
               "-try", "1", "-v", "0", "-i", str(destination)]
    (destination / "command.txt").write_text(shlex.join(command) + "\n", encoding="utf-8")
    expected = read_points(source / f"expected-{mode.rsplit('-', 1)[1]}.txt")
    row = {"case": case["name"], "mode": mode, "trial": trial, "status": "FAIL",
           "expected_count": len(expected), "actual_count": "", "elapsed_s": "", "error": ""}
    started = time.monotonic()
    try:
        with (destination / "protocol.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(command, cwd=destination, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=timeout, check=False)
        if result.returncode != 0:
            raise ValueError(f"protocol exited with code {result.returncode}")
        actual = read_points(output)
        row["actual_count"] = len(actual)
        if actual != expected:
            raise ValueError("output points differ from the exact reference")
        row["status"] = "PASS"
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        row["error"] = str(error)
    row["elapsed_s"] = f"{time.monotonic() - started:.6f}"
    (destination / "result.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
    return row


def run_suite(binary, data_dir, output_dir, trials=1, timeout=60):
    manifest = json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))
    if not manifest["cases"]:
        raise ValueError("boundary manifest contains no cases")
    for case in manifest["cases"]:
        source = data_dir / case["name"]
        sender = read_points(source / "sender_data.txt")
        receiver = read_points(source / "recver_data.txt")
        for metric in METRICS:
            if read_points(source / f"expected-{metric}.txt") != expected_intersection(
                    sender, receiver, metric, case["delta"]):
                raise ValueError(f"stale reference: {case['name']}/{metric}")

    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    with (output_dir / "summary.csv").open("w", encoding="utf-8", newline="") as summary:
        writer = None
        for case in manifest["cases"]:
            for mode in case["modes"]:
                for trial in range(1, trials + 1):
                    destination = output_dir / case["name"] / mode / f"run-{trial}"
                    row = run_case(binary, data_dir / case["name"], destination,
                                   case, mode, trial, timeout)
                    if writer is None:
                        writer = csv.DictWriter(summary, fieldnames=list(row))
                        writer.writeheader()
                    writer.writerow(row)
                    summary.flush()
                    rows.append(row)
                    if row["status"] != "PASS":
                        print(f"FAIL: {case['name']} / {mode}: {row['error']} ({destination})", flush=True)
            print(f"Checked boundary dataset: {case['name']}", flush=True)
    failures = sum(row["status"] != "PASS" for row in rows)
    modes = {row["mode"] for row in rows}
    passed = bool(rows) and failures == 0 and modes == set(MODES)
    print(f"{'✅' if passed else '❌'} [boundary] {'PASS' if passed else 'FAIL'}: "
          f"{len(rows)} executions across {len(modes)} modes; {failures} failures", flush=True)
    return 0 if passed else 1


def positive_integer(value):
    parsed = int(value)
    if parsed < 1 or parsed > 2147483647:
        raise argparse.ArgumentTypeError("must be between 1 and 2147483647")
    return parsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT_DIR / "code/build/fpsi")
    parser.add_argument("--data-dir", type=Path, help="use files from generate_boundary_data.py")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--trials", type=positive_integer, default=1)
    parser.add_argument("--timeout", type=positive_integer, default=60, help="seconds per execution")
    arguments = parser.parse_args()
    output_dir = arguments.output_dir.resolve()
    data_dir = arguments.data_dir.resolve() if arguments.data_dir else output_dir / "data"
    if not arguments.data_dir:
        generate(data_dir)
    try:
        return run_suite(arguments.binary.resolve(), data_dir, output_dir / "runs",
                         arguments.trials, arguments.timeout)
    except (OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
