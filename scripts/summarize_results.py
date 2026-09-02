#!/usr/bin/env python3

"""Convert FPSI text result rows into reproducible CSV/Markdown summaries."""

from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path


ROW = re.compile(
    r"^\[(?P<mode>[^]]+)]\s+"
    r"(?P<assumption>\S+)-(?P<side>send|recv|both)\s+"
    r"L(?P<metric>[012])\s+"
    r"(?P<dimension>\d+)\s+"
    r"(?P<delta>\d+)\s+"
    r"(?P<size>\d+)\s+"
    r"(?P<communication>[0-9]+(?:\.[0-9]+)?)\s+"
    r"(?P<runtime>[0-9]+(?:\.[0-9]+)?)\s*$"
)

KEY_FIELDS = ("mode", "assumption", "side", "metric", "dimension", "delta", "size")


def parse_lines(lines: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in lines:
        match = ROW.match(line.strip())
        if not match:
            continue
        row: dict[str, object] = match.groupdict()
        for field in ("metric", "dimension", "delta", "size"):
            row[field] = int(row[field])
        row["communication"] = float(row["communication"])
        row["runtime"] = float(row["runtime"])
        rows.append(row)
    return rows


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[field] for field in KEY_FIELDS)].append(row)

    summaries: list[dict[str, object]] = []
    for key in sorted(grouped):
        observations = grouped[key]
        communication = [float(row["communication"]) for row in observations]
        runtime = [float(row["runtime"]) for row in observations]
        summary = dict(zip(KEY_FIELDS, key))
        summary.update(
            repetitions=len(observations),
            communication_mb_mean=statistics.fmean(communication),
            communication_mb_std=statistics.pstdev(communication),
            runtime_s_mean=statistics.fmean(runtime),
            runtime_s_std=statistics.pstdev(runtime),
        )
        summaries.append(summary)
    return summaries


OUTPUT_FIELDS = KEY_FIELDS + (
    "repetitions",
    "communication_mb_mean",
    "communication_mb_std",
    "runtime_s_mean",
    "runtime_s_std",
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# 📊 FPSI Result Summary\n\n")
        handle.write("Generated from raw FPSI benchmark logs.\n\n")
        handle.write(
            "| Mode | Assumption | Side | Metric | d | Delta | n | Reps | "
            "Comm. MB (mean ± sd) | Time s (mean ± sd) |\n"
        )
        handle.write("|---|---|---|---:|---:|---:|---:|---:|---:|---:|\n")
        for row in rows:
            handle.write(
                f"| {row['mode']} | {row['assumption']} | {row['side']} | "
                f"L{row['metric']} | {row['dimension']} | {row['delta']} | "
                f"{row['size']} | {row['repetitions']} | "
                f"{row['communication_mb_mean']:.2f} ± "
                f"{row['communication_mb_std']:.2f} | "
                f"{row['runtime_s_mean']:.2f} ± {row['runtime_s_std']:.2f} |\n"
            )


def self_test() -> None:
    rows = parse_lines(
        [
            "[normal]   uniqCell-recv  L1       2     32     256      10.00      2.00",
            "[normal]   uniqCell-recv  L1       2     32     256      12.00      4.00",
            "unrelated diagnostic output",
        ]
    )
    result = summarize(rows)
    assert len(result) == 1
    assert result[0]["repetitions"] == 2
    assert math.isclose(float(result[0]["communication_mb_mean"]), 11.0)
    assert math.isclose(float(result[0]["communication_mb_std"]), 1.0)
    assert math.isclose(float(result[0]["runtime_s_mean"]), 3.0)
    print("✓ Result parser self-test passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="*", type=Path, help="raw FPSI log files")
    parser.add_argument("--csv", type=Path, help="CSV output path")
    parser.add_argument("--markdown", type=Path, help="Markdown output path")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.logs or not args.csv or not args.markdown:
        parser.error("logs, --csv, and --markdown are required")

    lines: list[str] = []
    for path in args.logs:
        lines.extend(path.read_text(encoding="utf-8", errors="replace").splitlines())
    rows = summarize(parse_lines(lines))
    if not rows:
        print("error: no FPSI result rows found", file=sys.stderr)
        return 1

    write_csv(args.csv, rows)
    write_markdown(args.markdown, rows)
    print(f"✓ Summarized {len(rows)} configuration(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
