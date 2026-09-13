#!/usr/bin/env python3

"""Regression tests for paper references and automatically scaled runtime plots."""

from __future__ import annotations

import csv
import itertools
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from compare_paper_results import (
    KEY_FIELDS, SVG_NAMESPACE, compare, draw_panel, load_results, match_results, time_axis,
)


ROOT_DIR = Path(__file__).resolve().parent.parent


class PaperComparisonTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="fpsi-paper-comparison-")
        self.addCleanup(self.workspace.cleanup)
        self.directory = Path(self.workspace.name)
        self.reference = ROOT_DIR / "claims/claim2/paper-results.csv"
        self.paper = load_results(self.reference, paper=True)

    def measurements(self, scale=2):
        return {key: {**row, "runtime": row["runtime"] * scale, "trials": 10}
                for key, row in self.paper.items()}

    def write_measurements(self, rows):
        destination = self.directory / "summary.csv"
        fields = (*KEY_FIELDS, "trials", "communication_mb_mean", "runtime_s_mean")
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({**{field: row[field] for field in KEY_FIELDS}, "trials": row["trials"],
                                 "communication_mb_mean": row["communication"], "runtime_s_mean": row["runtime"]})
        return destination

    def test_complete_paper_matrices_and_anchor_values(self):
        for claim, sizes, metrics, assumption in (
                (2, (256, 4096, 65536), (0,), "uniqCel"),
                (3, (4096,), (0, 1, 2), "uniqBlk")):
            paper = load_results(ROOT_DIR / f"claims/claim{claim}/paper-results.csv", paper=True)
            expected = {(mode, assumption, "recv", metric, dimension, delta, size)
                        for mode, metric, dimension, delta, size in itertools.product(
                            ("normal", "prefix"), metrics, (2, 4, 6), (32, 64, 128, 256, 512), sizes)}
            self.assertEqual(len(paper), 90)
            self.assertEqual(set(paper), expected)
        self.assertEqual(self.paper[("prefix", "uniqCel", "recv", 0, 2, 512, 256)]["communication"], 3.77)
        self.assertEqual(self.paper[("prefix", "uniqCel", "recv", 0, 6, 512, 65536)]["runtime"], 1399.69)
        self.assertEqual(paper[("normal", "uniqBlk", "recv", 0, 6, 512, 4096)]["runtime"], 1304.04)

    def assert_delta_ticks(self, panel, deltas):
        self.assertEqual(panel.get("data-x-scale"), "categorical")
        labels = panel.findall(f"{{{SVG_NAMESPACE}}}text[@class='delta-tick']")
        self.assertEqual([int(label.text) for label in labels], list(deltas))
        left, right = float(panel.get("data-plot-left")), float(panel.get("data-plot-right"))
        positions = {}
        for index, label in enumerate(labels):
            delta = int(label.get("data-delta"))
            self.assertEqual(delta, deltas[index])
            position = float(label.get("x"))
            self.assertAlmostEqual(position, left + (index + 0.5) / len(deltas) * (right - left))
            positions[delta] = position
        return positions

    def test_delta_categories_use_equal_spacing(self):
        for deltas in ((32,), (32, 48, 256), (32, 64, 128, 256, 512)):
            with self.subTest(deltas=deltas):
                root = ET.Element(f"{{{SVG_NAMESPACE}}}svg")
                rows = [{"delta": delta, "paper_runtime_s": 2.0, "measured_runtime_s": 3.0}
                        for delta in deltas]
                draw_panel(root, rows, "normal", 2, 0, 0, 500, 250)
                panel = root.find(f"{{{SVG_NAMESPACE}}}g[@class='panel']")
                positions = self.assert_delta_ticks(panel, deltas)
                points = panel.findall(f".//{{{SVG_NAMESPACE}}}circle[@class='data-point']")
                self.assertEqual(len(points), 2 * len(deltas))
                for point in points:
                    self.assertAlmostEqual(float(point.get("cx")), positions[int(point.get("data-delta"))])

    def assert_plot_values_and_bounds(self, figures, measured):
        count = 0
        for figure in figures:
            root = ET.parse(self.directory / figure["path"]).getroot()
            for panel in root.findall(f".//{{{SVG_NAMESPACE}}}g[@class='panel']"):
                top, bottom = float(panel.get("data-plot-top")), float(panel.get("data-plot-bottom"))
                left, right = float(panel.get("data-plot-left")), float(panel.get("data-plot-right"))
                limit = float(panel.get("data-y-max"))
                delta_positions = self.assert_delta_ticks(panel, (32, 64, 128, 256, 512))
                times = []
                for series in panel.findall(f"{{{SVG_NAMESPACE}}}g[@class='series']"):
                    source = self.paper if series.get("data-source") == "paper" else measured
                    for point in series.findall(f"{{{SVG_NAMESPACE}}}circle"):
                        key = (panel.get("data-mode"), root.get("data-assumption"), root.get("data-side"),
                               int(root.get("data-metric")), int(panel.get("data-dimension")),
                               int(point.get("data-delta")), int(root.get("data-size")))
                        runtime = float(point.get("data-time"))
                        self.assertEqual(runtime, source[key]["runtime"])
                        horizontal, vertical = float(point.get("cx")), float(point.get("cy"))
                        self.assertLess(top, vertical)
                        self.assertLess(vertical, bottom)
                        self.assertLess(left, horizontal)
                        self.assertLess(horizontal, right)
                        self.assertAlmostEqual(vertical, bottom - runtime / limit * (bottom - top))
                        self.assertAlmostEqual(horizontal, delta_positions[key[5]])
                        times.append(runtime)
                        count += 1
                self.assertGreaterEqual(limit, max(times) * 1.15)
        self.assertEqual(count, 2 * len(measured))

    def test_original_times_and_adaptive_axes_on_slower_machines(self):
        for scale in (0.5, 1, 1.5, 2, 10):
            with self.subTest(scale=scale):
                measured = self.measurements(scale)
                path = self.write_measurements(measured.values())
                rows, figures = compare(self.reference, path, self.directory)
                self.assertEqual(len(figures), 3)
                self.assertEqual(len(rows), 90)
                self.assertNotIn("runtime_ratio", rows[0])
                self.assert_plot_values_and_bounds(figures, measured)

    def test_unique_block_plots_cover_all_three_metrics(self):
        self.reference = ROOT_DIR / "claims/claim3/paper-results.csv"
        self.paper = load_results(self.reference, paper=True)
        measured = self.measurements(scale=2)
        path = self.write_measurements(measured.values())
        rows, figures = compare(self.reference, path, self.directory)
        self.assertEqual(len(rows), 90)
        self.assertEqual(len(figures), 3)
        self.assertEqual({ET.parse(self.directory / figure["path"]).getroot().get("data-metric")
                          for figure in figures}, {"0", "1", "2"})
        self.assert_plot_values_and_bounds(figures, measured)

    def test_time_axis_starts_at_zero_and_handles_flat_series(self):
        for values in ([0.01, 0.01], [3, 3, 3], [1304.04, 2608.08]):
            limit, ticks = time_axis(values)
            self.assertEqual(ticks[0], 0)
            self.assertEqual(ticks[-1], limit)
            self.assertGreaterEqual(limit, max(values) * 1.15)
        measured = self.measurements()
        for row in measured.values():
            row["runtime"] = 3.0
        path = self.write_measurements(measured.values())
        _, figures = compare(self.reference, path, self.directory)
        self.assert_plot_values_and_bounds(figures, measured)

    def test_light_profile_requires_exact_measured_keys(self):
        paper = load_results(self.reference, paper=True, size=4096)
        measured = {key: row for key, row in self.measurements().items() if row["size"] == 4096}
        self.assertEqual(len(match_results(paper, measured)), 30)
        with self.assertRaisesRegex(ValueError, "unexpected"):
            match_results(paper, self.measurements())

    def test_missing_extra_and_wrong_mode_fail(self):
        measured = self.measurements()
        removed_key, row = measured.popitem()
        with self.assertRaisesRegex(ValueError, "1 missing"):
            match_results(self.paper, measured)
        wrong_key = ("wrong-mode", *removed_key[1:])
        measured[wrong_key] = row
        with self.assertRaisesRegex(ValueError, "1 missing, 1 unexpected"):
            match_results(self.paper, measured)

    def test_duplicate_and_nonpositive_or_nonfinite_measurements_fail(self):
        rows = list(self.measurements().values())
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_results(self.write_measurements([*rows, rows[0]]))
        for value in (0, float("nan"), float("inf")):
            with self.subTest(value=value):
                rows[0]["runtime"] = value
                with self.assertRaisesRegex(ValueError, "finite and positive"):
                    load_results(self.write_measurements(rows))

    def test_rerun_removes_obsolete_generated_reports_and_plots(self):
        measured = self.measurements()
        path = self.write_measurements(measured.values())
        compare(self.reference, path, self.directory)
        for filename in ("paper-statistics.csv", "paper-speedups.csv"):
            (self.directory / filename).write_text("obsolete generated report")
        custom = self.directory / "paper-plots/custom.svg"
        custom.write_text("keep")
        selected = {key: row for key, row in measured.items() if row["size"] == 4096}
        path = self.write_measurements(selected.values())
        rows, figures = compare(self.reference, path, self.directory, size=4096)
        self.assertEqual(len(rows), 30)
        self.assertEqual(len(figures), 1)
        self.assertEqual(len(list((self.directory / "paper-plots").glob("runtime-*.svg"))), 1)
        self.assertEqual(custom.read_text(), "keep")
        for filename in ("paper-statistics.csv", "paper-speedups.csv"):
            self.assertFalse((self.directory / filename).exists())
        self.assert_plot_values_and_bounds(figures, selected)

    def test_cli_creates_reports_without_optional_dependencies(self):
        measured = self.write_measurements(self.measurements().values())
        result = subprocess.run(
            [sys.executable, "-S", str(ROOT_DIR / "scripts/compare_paper_results.py"),
             "--reference", str(self.reference), "--results", str(measured),
             "--output-dir", str(self.directory)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        for filename in ("paper-comparison.csv", "paper-comparison.md"):
            self.assertTrue((self.directory / filename).is_file())
        report = (self.directory / "paper-comparison.md").read_text()
        self.assertIn("90 selected configurations", report)
        self.assertEqual(report.count("!["), 3)
        self.assertEqual(len(list((self.directory / "paper-plots").glob("*.svg"))), 3)
        self.assertIn("equally spaced δ categories", report)
        self.assertFalse(list((self.directory / "paper-plots").glob("*.png")))
        self.assertNotIn("Spearman", report)
        self.assertNotIn("Pearson", report)
        self.assertNotIn("winner", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
