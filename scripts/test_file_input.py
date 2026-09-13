#!/usr/bin/env python3

"""Check point-file I/O against plaintext results in every supported PSI mode."""

from __future__ import annotations

import itertools
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


BINARY = Path(sys.argv[1]).resolve()
MODES = [(assumption, False, prefix, metric)
         for assumption, prefix, metric in itertools.product((0, 1), (False, True), (0, 1, 2))]
MODES += [(0, True, prefix, metric)
          for prefix in (False, True) for metric in ((0,) if prefix else (0, 1, 2))]


def expected_intersection(sender, receiver, metric, delta):
    def matches(left, right):
        differences = [abs(first - second) for first, second in zip(left, right)]
        if metric == 0:
            return max(differences) <= delta
        return sum(value ** metric for value in differences) <= delta ** metric

    return sorted(point for point in sender if any(matches(point, other) for other in receiver))


class FileInputTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="fpsi file input ")
        self.addCleanup(self.workspace.cleanup)
        self.directory = Path(self.workspace.name)
        self.output = self.directory / "output.txt"

    def write_inputs(self, sender, receiver):
        for filename, points in (("sender_data.txt", sender), ("recver_data.txt", receiver)):
            text = "\n" + "\n".join("\t ".join(map(str, point)) for point in points) + "\n\n"
            (self.directory / filename).write_text(text, encoding="utf-8")

    def run_fpsi(self, *arguments):
        defaults = [] if "-delta" in arguments else ["-delta", "32"]
        return subprocess.run(
            [str(BINARY), "-i", str(self.directory), *defaults, *arguments],
            cwd=self.directory, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=60,
        )

    def run_mode(self, mode, *arguments):
        assumption, sender, prefix, metric = mode
        options = ["-assumption", str(assumption), "-p", str(metric)]
        if sender:
            options.append("-sender")
        if prefix:
            options.append("-prefix")
        return self.run_fpsi(*options, *arguments)

    def assert_points(self, expected):
        self.assertTrue(self.output.is_file())
        actual = [tuple(map(int, line.split())) for line in self.output.read_text().splitlines()]
        self.assertEqual(actual, expected)
        self.assertEqual(list(self.directory.glob(".output.txt.*")), [])

    def assert_trial_timing(self, output, trials):
        entries = re.findall(
            r"^\s*(local preprocess done|input preparation done|OPPRF done|OT done)"
            r"\s+([0-9]+(?:\.[0-9]+)?)\s+",
            output, re.MULTILINE,
        )
        expected_labels = (["local preprocess done"]
                           + ["input preparation done", "OPPRF done"] * trials
                           + ["OT done"])
        self.assertEqual([label for label, _ in entries], expected_labels, output)
        times = [float(value) for _, value in entries]
        self.assertEqual(times, sorted(times))
        result_rows = [line for line in output.splitlines()
                       if line.startswith(("[normal]", "[prefix]"))]
        self.assertEqual(len(result_rows), 1, output)
        reported_time = float(result_rows[0].split()[-1])
        self.assertAlmostEqual(reported_time, (times[-1] - times[0]) / 1000 / trials, delta=0.006)

    def test_all_modes_and_metric_boundaries(self):
        offsets = [(0, 0, 0), (32, 0, 0), (33, 0, 0), (16, 16, 16),
                   (23, 23, 23), (32, 1, 0), (1, 1, 32), (64, 0, 0)]
        for dimension in (2, 3):
            sender = [tuple(index * 512 + axis * (1 << 54) for axis in range(dimension))
                      for index in range(len(offsets))]
            receiver = [tuple(value + difference for value, difference in zip(point, offset))
                        for point, offset in zip(sender, offsets)]
            self.write_inputs(list(reversed(sender)), receiver)
            for mode in MODES:
                with self.subTest(dimension=dimension, mode=mode):
                    result = self.run_mode(mode, "-try", "2", "-v", "1")
                    self.assertEqual(result.returncode, 0, result.stdout)
                    expected = expected_intersection(sender, receiver, mode[3], 32)
                    self.assert_points(expected)
                    marker = f"Total {len(expected)}/{len(expected)} matches found!"
                    self.assertEqual(result.stdout.splitlines().count(marker), 2, result.stdout)
                    self.assert_trial_timing(result.stdout, 2)

    def test_single_point_all_modes_without_verification(self):
        self.write_inputs([(0,)], [(1,)])
        for mode in MODES:
            with self.subTest(mode=mode):
                result = self.run_mode(mode)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assert_points([(0,)])
                self.assertNotIn("matches found!", result.stdout)

    def test_empty_and_full_intersections_all_modes(self):
        sender = [(index * 512, index * 512 + 7) for index in range(3)]
        for full in (False, True):
            receiver = sender if full else [(first + 128, second) for first, second in sender]
            self.write_inputs(sender, receiver)
            for mode in MODES:
                with self.subTest(full=full, mode=mode):
                    self.output.write_text("old result\n")
                    result = self.run_mode(mode)
                    self.assertEqual(result.returncode, 0, result.stdout)
                    self.assert_points(sender if full else [])

    def test_empty_files(self):
        self.write_inputs([], [])
        result = self.run_fpsi()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assert_points([])

    def test_infer_shape_and_ignore_synthetic_parameters(self):
        self.write_inputs([(128, 257, 513)], [(128, 258, 513)])
        result = self.run_fpsi("-n", "999", "-nn", "999", "-d", "99", "-inter", "999", "-v", "1")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assert_points([(128, 257, 513)])

    def test_output_symlink_does_not_overwrite_inputs(self):
        self.write_inputs([(0,)], [(128,)])
        source = self.directory / "sender_data.txt"
        original = source.read_bytes()
        self.output.symlink_to(source)
        result = self.run_fpsi()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(source.read_bytes(), original)
        self.assertFalse(self.output.is_symlink())
        self.assert_points([])

    def test_output_directory_is_rejected_without_partial_files(self):
        self.write_inputs([(0,)], [(1,)])
        self.output.mkdir()
        result = self.run_fpsi()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.output.is_dir())
        self.assertEqual(list(self.directory.glob(".output.txt.*")), [])

    def test_invalid_inputs_preserve_previous_output(self):
        cases = [
            ("-1 2\n", "1 2\n", (), "coordinate"),
            ("1.5 2\n", "1 2\n", (), "coordinate"),
            ("1,2\n", "1 2\n", (), "coordinate"),
            ("18446744073709551616\n", "1\n", (), "coordinate"),
            ("18446744073709551615\n", "1\n", (), "range"),
            ("1 2\n3\n", "1 2\n3 4\n", (), "dimension"),
            ("1 2\n", "1 2 3\n", (), "dimension"),
            ("1\n2\n", "1\n", (), "same number"),
            ("1\n1\n", "1\n512\n", (), "duplicate"),
            ("0\n512\n", "0\n1\n", (), "unique-cell"),
            ("0\n1\n", "0\n512\n", ("-sender",), "unique-cell"),
            ("0\n512\n", "60\n70\n", ("-assumption", "1"), "unique-block"),
            ("0\n", "1\n", ("-assumption", "1", "-sender"), "not implemented"),
            ("0\n", "1\n", ("-sender", "-prefix", "-p", "1"), "only L-infinity"),
            ("0\n", "1\n", ("-p", "3"), "requires -p"),
            ("0\n", "1\n", ("-assumption", "3"), "requires -p"),
            ("0\n", "1\n", ("-try", "0"), "positive -try"),
            ("0\n", "1\n", ("-delta", "0"), "delta"),
        ]
        for sender, receiver, options, message in cases:
            with self.subTest(sender=sender, options=options):
                (self.directory / "sender_data.txt").write_text(sender)
                (self.directory / "recver_data.txt").write_text(receiver)
                self.output.write_text("old result\n")
                result = self.run_fpsi(*options)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(message, result.stdout)
                self.assertEqual(self.output.read_text(), "old result\n")
                self.assertEqual(list(self.directory.glob(".output.txt.*")), [])

    def test_missing_file(self):
        (self.directory / "sender_data.txt").write_text("1\n")
        result = self.run_fpsi()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("recver_data.txt", result.stdout)
        self.assertFalse(self.output.exists())

    def test_missing_directory_argument(self):
        result = subprocess.run([str(BINARY), "-i"], text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires exactly one input directory", result.stdout)

    def test_synthetic_default_intersection_tracks_size(self):
        cases = [
            ((), 10),
            (("-nn", "8"), 8),
            (("-nn", "12"), 12),
            (("-n", "1000"), 9),
            (("-n", "512", "-nn", "3"), 9),
            (("-nn", "8", "-inter", "4"), 4),
            (("-nn", "8", "-inter", "0"), 0),
        ]
        for options, expected in cases:
            with self.subTest(options=options):
                result = subprocess.run(
                    [str(BINARY), "-delta", "32", "-v", "1", *options],
                    cwd=self.directory, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn(f"Total {expected}/{expected} matches found!", result.stdout)
                self.assertFalse(self.output.exists())

    def test_synthetic_mode_does_not_write_output(self):
        self.output.write_text("keep me\n")
        result = subprocess.run(
            [str(BINARY), "-nn", "8", "-delta", "32", "-v", "1"],
            cwd=self.directory, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Total 8/8 matches found!", result.stdout)
        self.assertEqual(self.output.read_text(), "keep me\n")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]], verbosity=2)
