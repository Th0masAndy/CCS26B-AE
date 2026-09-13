#!/usr/bin/env python3

"""Unit tests for boundary-data generation and the external correctness checker."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from generate_boundary_data import (
    MODES, boundary_cases, expected_intersection, generate, write_points,
)
from test_boundary_inputs import run_case, run_suite


class BoundaryDataTests(unittest.TestCase):
    def test_exact_metric_oracle(self):
        sender = [(0, 0), (3, 4), (5, 1), (4, 4)]
        self.assertEqual(expected_intersection(sender, [(0, 0)], "linf", 5), sorted(sender))
        self.assertEqual(expected_intersection(sender, [(0, 0)], "l1", 5), [(0, 0)])
        self.assertEqual(expected_intersection(sender, [(0, 0)], "l2", 5), [(0, 0), (3, 4)])
        self.assertEqual(expected_intersection([], [], "linf", 32), [])
        self.assertEqual(expected_intersection([(1,)], [(0,), (2,)], "l1", 1), [(1,)])

    def test_matching_scenarios_have_expected_cardinalities(self):
        counts = {"empty-intersection": 0, "full-intersection": 3, "all-fuzzy-matches": 3,
                  "just-inside": 3, "at-threshold": 3, "just-outside": 0, "many-to-one": 3,
                  "many-to-one-adjacent-cells": 2, "one-to-many": 1, "coordinate-mixing": 0}
        for case in boundary_cases():
            self.assertGreater(len(case.sender), 0)
            if case.name in counts:
                for metric in ("linf", "l1", "l2"):
                    with self.subTest(case=case.name, metric=metric):
                        self.assertEqual(len(expected_intersection(
                            case.sender, case.receiver, metric, case.delta)), counts[case.name])

    def test_all_generated_inputs_satisfy_assumptions(self):
        self.assertEqual(len(MODES), 16)
        for case in boundary_cases():
            with self.subTest(case=case.name):
                self.assertEqual(len(case.sender), len(case.receiver))
                for points in (case.sender, case.receiver):
                    self.assertEqual(len(points), len(set(points)))
                    for point in points:
                        self.assertEqual(len(point), len(case.sender[0]))
                        self.assertTrue(all(0 <= coordinate < (1 << 64)
                                            for coordinate in point))
                for side in case.sides:
                    points = case.sender if side == "cell-send" else case.receiver
                    occupied = set()
                    for point in points:
                        if side == "block-recv":
                            cells = itertools.product(*[
                                range((coordinate - case.delta) // (2 * case.delta),
                                      (coordinate + case.delta) // (2 * case.delta) + 1)
                                for coordinate in point])
                        else:
                            cells = [tuple(coordinate // (2 * case.delta) for coordinate in point)]
                        for cell in cells:
                            self.assertNotIn(cell, occupied, (case.name, side, cell))
                            occupied.add(cell)

    def test_generation_is_reproducible_and_covers_all_modes(self):
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            manifest = generate(root / "first", seed=2026)
            generate(root / "second", seed=2026)
            self.assertEqual({mode for case in manifest["cases"] for mode in case["modes"]}, set(MODES))
            self.assertEqual(len({case["name"] for case in manifest["cases"]}), len(manifest["cases"]))
            for source in (root / "first").rglob("*"):
                if source.is_file():
                    self.assertEqual(source.read_bytes(),
                                     (root / "second" / source.relative_to(root / "first")).read_bytes())
            generate(root / "second", seed=2027)
            self.assertNotEqual((root / "first/seeded-mixed/sender_data.txt").read_bytes(),
                                (root / "second/seeded-mixed/sender_data.txt").read_bytes())


class BoundaryCheckerTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="fpsi-boundary-checker-")
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.source = self.root / "data"
        self.source.mkdir()
        self.destination = self.root / "result"
        self.destination.mkdir()
        self.case = {"name": "checker-test", "delta": 32}
        self.mode = "cell-recv-normal-linf"
        write_points(self.source / "sender_data.txt", [(0, 0), (512, 512)])
        write_points(self.source / "recver_data.txt", [(1, 0), (640, 640)])
        write_points(self.source / "expected-linf.txt", [(0, 0)])

    def check_with_output(self, points, returncode=0):
        def invoke(command, **options):
            if points is not None:
                write_points(self.destination / "output.txt", points)
            return subprocess.CompletedProcess(command, returncode)

        with patch("test_boundary_inputs.subprocess.run", side_effect=invoke):
            return run_case(self.root / "fake-fpsi", self.source, self.destination,
                            self.case, self.mode, 1, 1)

    def test_accepts_exact_points(self):
        self.assertEqual(self.check_with_output([(0, 0)])["status"], "PASS")

    def test_rejects_wrong_points_even_when_count_matches(self):
        row = self.check_with_output([(512, 512)])
        self.assertEqual(row["expected_count"], row["actual_count"])
        self.assertEqual(row["status"], "FAIL")

    def test_rejects_missing_extra_and_duplicate_points(self):
        for points in ([], [(0, 0), (512, 512)], [(0, 0), (0, 0)]):
            with self.subTest(points=points):
                self.assertEqual(self.check_with_output(points)["status"], "FAIL")

    def test_does_not_accept_stale_output_or_failed_process(self):
        write_points(self.destination / "output.txt", [(0, 0)])
        self.assertEqual(self.check_with_output(None)["status"], "FAIL")
        self.assertEqual(self.check_with_output([(0, 0)], returncode=2)["status"], "FAIL")

    def test_empty_intersection_requires_an_output_file(self):
        write_points(self.source / "expected-linf.txt", [])
        self.assertEqual(self.check_with_output(None)["status"], "FAIL")
        self.assertEqual(self.check_with_output([])["status"], "PASS")

    def test_timeout_is_recorded_as_failure(self):
        with patch("test_boundary_inputs.subprocess.run", side_effect=subprocess.TimeoutExpired("fpsi", 1)):
            row = run_case(self.root / "fake-fpsi", self.source, self.destination,
                           self.case, self.mode, 1, 1)
        self.assertEqual(row["status"], "FAIL")
        self.assertIn("timed out", row["error"])
        self.assertEqual(json.loads((self.destination / "result.json").read_text())["status"], "FAIL")

    def test_stale_reference_is_rejected_before_execution(self):
        generate(self.source)
        write_points(self.source / "full-intersection/expected-linf.txt", [])
        with patch("test_boundary_inputs.subprocess.run") as execute:
            with self.assertRaisesRegex(ValueError, "stale reference"):
                run_suite(self.root / "fake-fpsi", self.source, self.destination)
            execute.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
