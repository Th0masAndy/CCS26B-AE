#!/usr/bin/env python3

"""Generate reproducible point files and exact answers for Claim 1."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import itertools
import json
from pathlib import Path
import random


METRICS = ("linf", "l1", "l2")
SIDES = ("cell-recv", "cell-send", "block-recv")
MODES = {
    f"{side}-{'prefix' if prefix else 'normal'}-{metric}":
    ["-assumption", str(int(side == "block-recv")), "-p", str(metric_index)]
    + (["-sender"] if side == "cell-send" else [])
    + (["-prefix"] if prefix else [])
    for side, prefix, (metric_index, metric) in itertools.product(
        SIDES, (False, True), enumerate(METRICS))
    if not (side == "cell-send" and prefix and metric_index != 0)
}


@dataclass
class Case:
    name: str
    description: str
    sender: list[tuple[int, ...]]
    receiver: list[tuple[int, ...]]
    delta: int = 32
    sides: tuple[str, ...] = SIDES


def expected_intersection(sender, receiver, metric, delta):
    """Use Python integers, without floating-point distances or protocol helpers."""
    result = []
    for point in sender:
        for other in receiver:
            differences = [abs(left - right) for left, right in zip(point, other)]
            distance = (max(differences) if metric == "linf" else
                        sum(value ** (2 if metric == "l2" else 1) for value in differences))
            if distance <= (delta * delta if metric == "l2" else delta):
                result.append(point)
                break
    return sorted(result)


def write_points(path, points):
    path.write_text("".join(" ".join(map(str, point)) + "\n" for point in points),
                    encoding="utf-8")


def paired_case(name, description, offsets, delta=32, **options):
    """Separate pairs by 16*delta so both constrained sides remain valid."""
    sender = [tuple((index + 1) * 16 * delta for _ in offset)
              for index, offset in enumerate(offsets)]
    receiver = [tuple(value + shift for value, shift in zip(point, offset))
                for point, offset in zip(sender, offsets)]
    for index in range(1, len(sender), 2):
        sender[index], receiver[index] = receiver[index], sender[index]
    return Case(name, description, sender, receiver, delta, **options)


def boundary_cases(seed=2026):
    generator = random.Random(seed)
    cases = [
        paired_case("empty-intersection", "Nonempty sets with no fuzzy matches.", [(128, 0)] * 3),
        paired_case("full-intersection", "Every sender point has an identical receiver point.", [(0, 0)] * 3),
        paired_case("all-fuzzy-matches", "Every sender point matches, without any identical points.", [(1, 1)] * 3),
        paired_case("just-inside", "Distance delta-1: every point must match.", [(31, 0), (0, 31), (31, 0)]),
        paired_case("at-threshold", "Distance delta: the threshold is inclusive.", [(32, 0), (0, 32), (32, 0)]),
        paired_case("just-outside", "Distance delta+1: no point may match.", [(33, 0), (0, 33), (33, 0)]),
    ]
    for dimension in (2, 4, 6):
        offsets = []
        for index, difference in enumerate((0, 31, 32, 33, 31, 32, 33)):
            offset = [0] * dimension
            offset[index % dimension] = difference
            offsets.append(tuple(offset))
        cases.append(paired_case(
            f"mixed-axis-d{dimension}", "Mixed matches and nonmatches on different axes and sides.", offsets))

    cases.extend([
        paired_case("metric-corners", "Multidimensional L1 and squared L2 distances below, at, and above threshold.",
                    [(31, 1, 0, 0), (31, 2, 0, 0), (16, 16, 16, 15), (16, 16, 16, 16),
                     (16, 16, 16, 17), (32, 32, 0, 0), (32, 1, 0, 0), (0, 0, 0, 0)]),
        Case("many-to-one", "Several unconstrained sender points match one receiver point.",
             [(63, 64), (64, 64), (65, 64)], [(64, 64), (1024, 1024), (2048, 2048)],
             sides=("cell-recv", "block-recv")),
        Case("many-to-one-adjacent-cells", "Two sender points in distinct cells match one receiver point.",
             [(63, 64), (64, 64), (2048, 2048)], [(64, 64), (4096, 4096), (8192, 8192)]),
        Case("one-to-many", "One sender point matches two receivers; output it only once.",
             [(63, 64), (2048, 2048), (4096, 4096)], [(32, 64), (64, 64), (8192, 8192)],
             sides=("cell-recv", "cell-send")),
        Case("coordinate-mixing", "Coordinates matching different points must not create a match.",
             [(63, 63), (2048, 2048), (4096, 4096)], [(63, 128), (128, 63), (8192, 8192)],
             sides=("cell-recv", "cell-send")),
    ])

    sender, receiver = [], []
    for index, (phase, distance) in enumerate(itertools.product((63, 64, 65, 127, 128, 129), (31, 32, 33))):
        point = (512 * (index + 1) + phase,) * 2
        sender.append(point)
        receiver.append((point[0] + distance, point[1]))
    cases.append(Case("cross-cell-threshold", "Threshold decisions when matching regions cross cell/block edges.",
                      sender, receiver))

    offsets = [tuple(generator.randint(0, 33) for _ in range(3)) for _ in range(17)]
    offsets[0], offsets[8], offsets[16] = (0, 0, 0), (32, 0, 0), (0, 32, 0)
    cases.append(paired_case("seeded-mixed", "Reproducible partial intersection with independently shuffled sets.",
                             offsets))
    for case in cases:
        generator.shuffle(case.sender)
        generator.shuffle(case.receiver)
    return cases


def generate(output_dir, seed=2026):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"seed": seed, "cases": []}
    for case in boundary_cases(seed):
        directory = output_dir / case.name
        directory.mkdir(exist_ok=True)
        write_points(directory / "sender_data.txt", case.sender)
        write_points(directory / "recver_data.txt", case.receiver)
        for metric in METRICS:
            write_points(directory / f"expected-{metric}.txt",
                         expected_intersection(case.sender, case.receiver, metric, case.delta))
        modes = [name for name in MODES if any(name.startswith(side + "-") for side in case.sides)]
        manifest["cases"].append({
            "name": case.name, "description": case.description, "delta": case.delta,
            "size": len(case.sender), "dimension": len(case.sender[0]) if case.sender else 0,
            "modes": modes,
        })
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=2026)
    arguments = parser.parse_args()
    manifest = generate(arguments.output_dir, arguments.seed)
    print(f"Generated {len(manifest['cases'])} boundary datasets: {arguments.output_dir}")


if __name__ == "__main__":
    main()
