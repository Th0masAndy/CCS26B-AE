#!/usr/bin/env python3

"""Plot FPSI runtimes, optionally against the paper, using dependency-free SVG."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from summarize_results import KEY_FIELDS, parse_lines, positive_trials


PLOT_FIELDS = ("assumption", "side", "metric", "size", "dimension")
RUNTIME_SERIES = (
    ("paper", "paper_runtime_s", "#64748b", "7 5"),
    ("measured", "measured_runtime_s", "#2563eb", "none"),
)
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NAMESPACE)


def load_results(path, paper=False, size=None, trials=1, dimensions=None):
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
                if paper and dimensions is not None and row["dimension"] not in dimensions:
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
    """Round the upper limit above all plotted values, with at least 15% headroom."""
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
    sample = rows[0]
    styles = [style for style in RUNTIME_SERIES if style[1] in sample]
    times = [row[style[1]] for row in rows for style in styles]
    limit, ticks = time_axis(times)
    plot_left, plot_right = left + 76, left + width - 22
    plot_top, plot_bottom = top + 36, top + height - 47
    deltas = sorted({row["delta"] for row in rows})
    delta_positions = {
        delta: plot_left + (index + 0.5) / len(deltas) * (plot_right - plot_left)
        for index, delta in enumerate(deltas)
    }
    panel = element(root, "g", class_="panel", data_mode=mode, data_dimension=dimension,
                    data_assumption=sample["assumption"], data_side=sample["side"],
                    data_metric=sample["metric"], data_size=sample["size"],
                    data_y_max=limit, data_plot_top=plot_top, data_plot_bottom=plot_bottom,
                    data_plot_left=plot_left, data_plot_right=plot_right, data_x_scale="categorical")
    element(panel, "rect", x=left, y=top, width=width, height=height, rx=8,
            fill="white", stroke="#e2e8f0")
    name = "Ours (normal)" if mode == "normal" else "Ours-Px (prefix)"
    metric = {0: "L∞", 1: "L1", 2: "L2"}.get(sample["metric"], f"L{sample['metric']}")
    element(panel, "text", f"{name} · {metric} · n = {sample['size']} · d = {dimension}", x=left + width / 2,
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
    for source, field, color, dash in styles:
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
    sample = rows[0]
    assumption = {"uniqCel": "Unique cell", "uniqBlk": "Unique block"}.get(sample["assumption"], sample["assumption"])
    if len({row["assumption"] for row in rows}) > 1:
        assumption = "FPSI"
    has_paper = "paper_runtime_s" in sample
    title = f"{assumption} · {'paper vs. measured runtimes' if has_paper else 'measured runtimes'}"
    dimensions = sorted({row["dimension"] for row in rows})
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in PLOT_FIELDS[:-1])].append(row)
    panel_rows = [
        [row for row in groups[key] if row["mode"] == mode]
        for key in sorted(groups)
        for mode in modes if any(row["mode"] == mode for row in groups[key])
    ]
    gap, margin, header, panel_width, panel_height = 24, 24, 104, 500, 280
    width = 2 * margin + len(dimensions) * panel_width + (len(dimensions) - 1) * gap
    height = header + len(panel_rows) * (panel_height + gap)
    root = ET.Element(f"{{{SVG_NAMESPACE}}}svg", {
        "width": str(width), "height": str(height), "viewBox": f"0 0 {width} {height}",
        "role": "img", "aria-labelledby": "figure-title",
    })
    for field in PLOT_FIELDS:
        if len({row[field] for row in rows}) == 1:
            root.set(f"data-{field}", str(sample[field]))
    element(root, "title", title, id="figure-title")
    element(root, "desc", "All selected configurations in one figure. Columns group dimensions; rows group set sizes, metrics, and modes. Delta values are equally spaced categories; each panel has its own automatic linear time scale.")
    element(root, "style", "text { font-family: Arial, Helvetica, sans-serif; fill: #0f172a; }")
    element(root, "rect", width=width, height=height, fill="#f8fafc")
    element(root, "text", title, x=margin, y=35, font_size=23, font_weight=600)
    subtitle = ("Original runtimes · equally spaced δ values · independently scaled panels"
                if has_paper else "Measured results only · no paper reference for this benchmark")
    element(root, "text", subtitle,
            x=margin, y=59, font_size=13, fill="#475569")
    styles = [style for style in RUNTIME_SERIES if style[1] in sample]
    legend_left = (width - (110 + 140 * (len(styles) - 1))) / 2
    for index, (source, field, color, dash) in enumerate(styles):
        position = legend_left + index * 140
        element(root, "line", x1=position, x2=position + 36, y1=83, y2=83,
                stroke=color, stroke_width=2.4, stroke_dasharray=dash)
        element(root, "text", source.capitalize(), x=position + 46, y=87, font_size=13)
    for row_index, group in enumerate(panel_rows):
        for column_index, dimension in enumerate(dimensions):
            selected = sorted((row for row in group if row["dimension"] == dimension),
                              key=lambda row: row["delta"])
            if selected:
                draw_panel(root, selected, selected[0]["mode"], dimension,
                           margin + column_index * (panel_width + gap),
                           header + row_index * (panel_height + gap), panel_width, panel_height)
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return title


def write_markdown(path, rows, figures, reference_path, measured_path):
    has_paper = reference_path is not None
    lines = ["# Paper runtime plots" if has_paper else "# Measured runtime plots", "",
             f"Paper reference: {reference_path}" if has_paper else
             "Measured results only. No paper reference is used for this benchmark.",
             f"Measurements: {measured_path}",
             f"{'Matched' if has_paper else 'Plotted'} {len(rows)} selected configurations.", "",
             "Horizontal axis: equally spaced δ categories. Vertical axis: original runtime in seconds, on a linear scale.",
             "Dashed gray lines show the paper; solid blue lines show the measurements." if has_paper else
             "Solid blue lines show the measurements; there is no paper curve or comparison.",
             "All configurations share one figure: dimensions form columns; set sizes, metrics, and modes form rows.",
             "Ours and Ours-Px have separate panels. Each panel scales to the plotted values with at least 15% headroom.",
             "Times are not normalized, and slower machines automatically receive a higher y-axis limit.", ""]
    for figure in figures:
        lines.extend([f"## {figure['title']}", "",
                      f"![{figure['title']}]({figure['path']})", ""])
    columns = ("Paper time (s) | Measured time (s) | Paper comm. (MB) | Measured comm. (MB) |"
               if has_paper else "Measured time (s) | Measured comm. (MB) |")
    lines.extend([
        "## Matched measurements" if has_paper else "## Measurements", "",
        "| Mode | Assumption | Side | Metric | d | Delta | n | Trials | " + columns,
        "|---|---|---|---:|---:|---:|---:|---:|" + "---:|" * (4 if has_paper else 2),
    ])
    for row in rows:
        values = (f"{row['paper_runtime_s']} | {row['measured_runtime_s']} | "
                  f"{row['paper_communication_mb']} | {row['measured_communication_mb']} |"
                  if has_paper else
                  f"{row['measured_runtime_s']} | {row['measured_communication_mb']} |")
        lines.append(
            f"| {row['mode']} | {row['assumption']} | {row['side']} | "
            f"L{row['metric']} | {row['dimension']} | {row['delta']} | "
            f"{row['size']} | {row['trials']} | "
            + values
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compare(reference_path, measured_path, output_dir, size=None, trials=1, dimensions=None, name=None):
    measured = load_results(measured_path, trials=trials)
    if reference_path is not None:
        rows = match_results(load_results(reference_path, paper=True, size=size, dimensions=dimensions),
                             measured)
    else:
        rows = []
        for key, actual in sorted(measured.items()):
            if ((size is not None and actual["size"] != size) or
                    (dimensions is not None and actual["dimension"] not in dimensions)):
                raise ValueError(f"configuration outside selected size/dimensions: {key}")
            rows.append({
                **{field: actual[field] for field in KEY_FIELDS}, "trials": actual["trials"],
                "measured_runtime_s": actual["runtime"],
                "measured_communication_mb": actual["communication"],
            })
    output_dir.mkdir(parents=True, exist_ok=True)
    if name is not None:
        filename = f"{name}-runtime.svg"
        report_name = f"{name}-{'comparison' if reference_path is not None else 'runtime'}.md"
    else:
        filename = "runtime-comparison.svg" if reference_path is not None else "runtime.svg"
        report_name = "paper-comparison.md" if reference_path is not None else "runtime.md"
    title = write_figure(output_dir / filename, rows)
    figures = [{"title": title, "path": filename}]
    write_markdown(output_dir / report_name, rows, figures, reference_path, measured_path)
    legacy_dir = output_dir / "paper-plots"
    if legacy_dir.is_dir() and not legacy_dir.is_symlink():
        for pattern in ("runtime-*-L*-n*.svg", "runtime-comparison.svg"):
            for previous in legacy_dir.glob(pattern):
                previous.unlink()
        if not any(legacy_dir.iterdir()):
            legacy_dir.rmdir()
    inputs = {measured_path.resolve()}
    if reference_path is not None:
        inputs.add(reference_path.resolve())
    for filename in ("paper-comparison.csv", "paper-statistics.csv", "paper-speedups.csv"):
        previous = output_dir / filename
        if previous.resolve() not in inputs:
            previous.unlink(missing_ok=True)
    if name is not None:
        previous = output_dir / f"{name}-{'runtime' if reference_path is not None else 'comparison'}.md"
        if previous.resolve() not in inputs:
            previous.unlink(missing_ok=True)
    print(f"📈 Runtime plot: {output_dir / report_name} (1 figure)")
    return rows, figures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, help="paper CSV; omit to plot measured results only")
    parser.add_argument("--results", type=Path, required=True, help="raw FPSI log (or a legacy summary CSV)")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--size", type=int, help="expected set size; also filters the paper reference")
    parser.add_argument("--dimensions", type=int, nargs="+",
                        help="expected dimensions; also filters the paper reference")
    parser.add_argument("--name", choices=("unique-cell", "unique-block"),
                        help="name outputs when saving both protocol families in one directory")
    parser.add_argument("--trials", type=positive_trials, default=1,
                        help="internal trials per raw result row (default: 1; ignored for CSV input)")
    arguments = parser.parse_args()
    try:
        compare(arguments.reference, arguments.results, arguments.output_dir,
                arguments.size, arguments.trials, arguments.dimensions, arguments.name)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
