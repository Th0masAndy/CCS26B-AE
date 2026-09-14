#!/usr/bin/env python3

"""Plot paper and measured FPSI runtimes using dependency-free SVG figures."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from summarize_results import KEY_FIELDS, parse_lines, positive_trials


PLOT_FIELDS = ("assumption", "side", "metric", "size")
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NAMESPACE)


def load_results(path, paper=False, size=None, trials=1):
    time_field = "runtime_s" if paper else "runtime_s_mean"
    comm_field = "communication_mb" if paper else "communication_mb_mean"
    required = set(KEY_FIELDS) | {time_field, comm_field}
    if not paper:
        required.add("trials")
    rows = {}
    with path.open(newline="", encoding="utf-8") as handle:
        if paper or path.suffix.lower() == ".csv":
            reader = csv.DictReader(handle)
            if not required.issubset(reader.fieldnames or []):
                raise ValueError(f"{path}: missing required CSV columns")
            sources = enumerate(reader, 2)
        else:
            time_field, comm_field = "runtime", "communication"
            sources = (
                (line_number, {**row, "trials": trials})
                for line_number, line in enumerate(handle, 1)
                for row in parse_lines([line])
            )
        for line_number, source in sources:
            try:
                row = {field: source[field] for field in KEY_FIELDS}
                for field in ("metric", "dimension", "delta", "size"):
                    row[field] = int(row[field])
                if paper and size is not None and row["size"] != size:
                    continue
                row["runtime"] = float(source[time_field])
                row["communication"] = float(source[comm_field])
                if any(not math.isfinite(row[field]) or row[field] <= 0
                       for field in ("runtime", "communication")):
                    raise ValueError("time and communication must be finite and positive")
                if not paper:
                    row["trials"] = int(source["trials"])
                    if row["trials"] < 1:
                        raise ValueError("trials must be positive")
                key = tuple(row[field] for field in KEY_FIELDS)
                if key in rows:
                    raise ValueError(f"duplicate configuration: {key}")
                rows[key] = row
            except (TypeError, ValueError) as error:
                raise ValueError(f"{path}:{line_number}: {error}") from error
    if not rows:
        raise ValueError(f"{path}: no configurations selected")
    return rows


def match_results(paper, measured):
    missing = paper.keys() - measured.keys()
    extra = measured.keys() - paper.keys()
    if missing or extra:
        raise ValueError(f"configuration mismatch: {len(missing)} missing, {len(extra)} unexpected; "
                         f"examples: missing={sorted(missing)[:2]}, unexpected={sorted(extra)[:2]}")
    rows = []
    for key in sorted(paper):
        reference, actual = paper[key], measured[key]
        rows.append({
            **{field: reference[field] for field in KEY_FIELDS}, "trials": actual["trials"],
            "paper_runtime_s": reference["runtime"], "measured_runtime_s": actual["runtime"],
            "paper_communication_mb": reference["communication"],
            "measured_communication_mb": actual["communication"],
        })
    return rows



def time_axis(values):
    """Round the upper limit above both series, with at least 15% headroom."""
    target = max(values) * 1.15
    magnitude = 10 ** math.floor(math.log10(target / 5))
    fraction = target / 5 / magnitude
    step = next(value for value in (1, 2, 2.5, 5, 10) if value >= fraction) * magnitude
    intervals = math.ceil(target / step)
    ticks = [index * step for index in range(intervals + 1)]
    return ticks[-1], ticks


def element(parent, tag, text=None, **attributes):
    node = ET.SubElement(parent, f"{{{SVG_NAMESPACE}}}{tag}", {
        key.rstrip("_").replace("_", "-"): str(value) for key, value in attributes.items()
    })
    if text is not None:
        node.text = text
    return node


def draw_panel(root, rows, mode, dimension, left, top, width, height):
    times = [row[field] for row in rows for field in ("paper_runtime_s", "measured_runtime_s")]
    limit, ticks = time_axis(times)
    plot_left, plot_right = left + 76, left + width - 22
    plot_top, plot_bottom = top + 36, top + height - 47
    deltas = sorted({row["delta"] for row in rows})
    delta_positions = {
        delta: plot_left + (index + 0.5) / len(deltas) * (plot_right - plot_left)
        for index, delta in enumerate(deltas)
    }
    panel = element(root, "g", class_="panel", data_mode=mode, data_dimension=dimension,
                    data_y_max=limit, data_plot_top=plot_top, data_plot_bottom=plot_bottom,
                    data_plot_left=plot_left, data_plot_right=plot_right, data_x_scale="categorical")
    element(panel, "rect", x=left, y=top, width=width, height=height, rx=8,
            fill="white", stroke="#e2e8f0")
    name = "Ours (normal)" if mode == "normal" else "Ours-Px (prefix)"
    element(panel, "text", f"{name}  ·  d = {dimension}", x=left + width / 2,
            y=top + 23, text_anchor="middle", font_size=14, font_weight=600)
    for tick in ticks:
        position = plot_bottom - tick / limit * (plot_bottom - plot_top)
        element(panel, "line", x1=plot_left, x2=plot_right, y1=position, y2=position,
                stroke="#e2e8f0", stroke_width=1)
        element(panel, "text", f"{tick:g}", x=plot_left - 10, y=position + 4,
                text_anchor="end", font_size=12, fill="#475569")
    for delta in deltas:
        position = delta_positions[delta]
        element(panel, "line", x1=position, x2=position, y1=plot_bottom, y2=plot_bottom + 5,
                stroke="#64748b")
        element(panel, "text", str(delta), class_="delta-tick", data_delta=delta,
                x=position, y=plot_bottom + 20,
                text_anchor="middle", font_size=12, fill="#475569")
    element(panel, "line", x1=plot_left, x2=plot_left, y1=plot_top, y2=plot_bottom, stroke="#64748b")
    element(panel, "line", x1=plot_left, x2=plot_right, y1=plot_bottom, y2=plot_bottom, stroke="#64748b")
    element(panel, "text", "δ", x=(plot_left + plot_right) / 2, y=plot_bottom + 39,
            text_anchor="middle", font_size=14)
    middle = (plot_top + plot_bottom) / 2
    element(panel, "text", "Time (s)", x=left + 18, y=middle, text_anchor="middle",
            font_size=13, transform=f"rotate(-90 {left + 18} {middle})")
    for source, field, color, dash in (
            ("paper", "paper_runtime_s", "#64748b", "7 5"),
            ("measured", "measured_runtime_s", "#2563eb", "none")):
        series = element(panel, "g", class_="series", data_source=source)
        points = [(delta_positions[row["delta"]],
                   plot_bottom - row[field] / limit * (plot_bottom - plot_top))
                  for row in rows]
        element(series, "polyline", points=" ".join(f"{horizontal},{vertical}" for horizontal, vertical in points),
                fill="none", stroke=color, stroke_width=2.4, stroke_dasharray=dash)
        for row, (horizontal, vertical) in zip(rows, points):
            point = element(series, "circle", class_="data-point", cx=horizontal, cy=vertical,
                            r=3.5, fill="white" if source == "paper" else color,
                            stroke=color, stroke_width=1.8, data_delta=row["delta"], data_time=row[field])
            element(point, "title", f"{source.capitalize()}: δ={row['delta']}, time={row[field]:g} s")


def write_figure(path, rows):
    modes = [mode for mode in ("normal", "prefix") if any(row["mode"] == mode for row in rows)]
    dimensions = sorted({row["dimension"] for row in rows})
    sample = rows[0]
    assumption = {"uniqCel": "Unique cell", "uniqBlk": "Unique block"}.get(sample["assumption"], sample["assumption"])
    metric = {0: "L∞", 1: "L1", 2: "L2"}.get(sample["metric"], f"L{sample['metric']}")
    title = f"{assumption} · {metric} · n = {sample['size']}"
    width, gap, margin, header, panel_height = 1120, 24, 24, 104, 250
    panel_width = (width - 2 * margin - gap * (len(modes) - 1)) / len(modes)
    height = header + len(dimensions) * (panel_height + gap)
    root = ET.Element(f"{{{SVG_NAMESPACE}}}svg", {
        "width": str(width), "height": str(height), "viewBox": f"0 0 {width} {height}",
        "role": "img", "aria-labelledby": "figure-title",
        "data-assumption": str(sample["assumption"]), "data-side": str(sample["side"]),
        "data-metric": str(sample["metric"]), "data-size": str(sample["size"]),
    })
    element(root, "title", title, id="figure-title")
    element(root, "desc", "Paper and measured runtimes in seconds. Delta values are equally spaced categories; each panel has its own automatic linear time scale.")
    element(root, "style", "text { font-family: Arial, Helvetica, sans-serif; fill: #0f172a; }")
    element(root, "rect", width=width, height=height, fill="#f8fafc")
    element(root, "text", title, x=margin, y=35, font_size=23, font_weight=600)
    element(root, "text", "Original runtimes · equally spaced δ values · independently scaled panels",
            x=margin, y=59, font_size=13, fill="#475569")
    for source, color, dash, position in (("Paper", "#64748b", "7 5", margin),
                                          ("Measured", "#2563eb", "none", margin + 140)):
        element(root, "line", x1=position, x2=position + 36, y1=83, y2=83,
                stroke=color, stroke_width=2.4, stroke_dasharray=dash)
        element(root, "text", source, x=position + 46, y=87, font_size=13)
    for row_index, dimension in enumerate(dimensions):
        for column_index, mode in enumerate(modes):
            selected = sorted((row for row in rows if row["mode"] == mode and row["dimension"] == dimension),
                              key=lambda row: row["delta"])
            if selected:
                draw_panel(root, selected, mode, dimension,
                           margin + column_index * (panel_width + gap),
                           header + row_index * (panel_height + gap), panel_width, panel_height)
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return title


def write_markdown(path, rows, figures, reference_path, measured_path):
    lines = ["# Paper runtime plots", "",
             f"Paper reference: {reference_path}",
             f"Measurements: {measured_path}",
             f"Matched {len(rows)} selected configurations.", "",
             "Horizontal axis: equally spaced δ categories. Vertical axis: original runtime in seconds, on a linear scale.",
             "Dashed gray lines show the paper; solid blue lines show the measurements.",
             "Ours and Ours-Px have separate panels. Each panel scales to both series with at least 15% headroom.",
             "Times are not normalized, and slower machines automatically receive a higher y-axis limit.", ""]
    for figure in figures:
        lines.extend([f"## {figure['title']}", "",
                      f"![{figure['title']}]({figure['path']})", ""])
    lines.extend([
        "## Matched measurements", "",
        "| Mode | Assumption | Side | Metric | d | Delta | n | Trials | "
        "Paper time (s) | Measured time (s) | Paper comm. (MB) | Measured comm. (MB) |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in rows:
        lines.append(
            f"| {row['mode']} | {row['assumption']} | {row['side']} | "
            f"L{row['metric']} | {row['dimension']} | {row['delta']} | "
            f"{row['size']} | {row['trials']} | "
            f"{row['paper_runtime_s']} | {row['measured_runtime_s']} | "
            f"{row['paper_communication_mb']} | {row['measured_communication_mb']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compare(reference_path, measured_path, output_dir, size=None, trials=1):
    rows = match_results(load_results(reference_path, paper=True, size=size),
                         load_results(measured_path, trials=trials))
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_dir = output_dir / "paper-plots"
    plot_dir.mkdir(exist_ok=True)
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in PLOT_FIELDS)].append(row)
    figures = []
    for index, (key, group) in enumerate(sorted(groups.items()), 1):
        filename = f"runtime-{index}-L{key[2]}-n{key[3]}.svg"
        title = write_figure(plot_dir / filename, group)
        figures.append({"title": title, "path": f"paper-plots/{filename}"})
    write_markdown(output_dir / "paper-comparison.md", rows, figures, reference_path, measured_path)
    current_files = {Path(figure["path"]).name for figure in figures}
    for previous in plot_dir.glob("runtime-*-L*-n*.svg"):
        if previous.name not in current_files:
            previous.unlink()
    for filename in ("paper-comparison.csv", "paper-statistics.csv", "paper-speedups.csv"):
        previous = output_dir / filename
        if previous.resolve() not in {reference_path.resolve(), measured_path.resolve()}:
            previous.unlink(missing_ok=True)
    print(f"📈 Runtime plots: {output_dir / 'paper-comparison.md'} ({len(figures)} figures)")
    return rows, figures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True, help="raw FPSI log (or a legacy summary CSV)")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--size", type=int, help="select this set size from the paper (e.g. 4096 for Claim 2 --light)")
    parser.add_argument("--trials", type=positive_trials, default=1,
                        help="internal trials per raw result row (default: 1; ignored for CSV input)")
    arguments = parser.parse_args()
    try:
        compare(arguments.reference, arguments.results, arguments.output_dir,
                arguments.size, arguments.trials)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
