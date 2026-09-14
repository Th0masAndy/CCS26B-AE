# Plotting against the paper

`claim2/paper-results.csv` and `claim3/paper-results.csv` contain the 90 **Ours**
and **Ours-Px** entries from [Table 2](./claim2/table2.png) and
[Table 3](./claim3/table3.png), respectively. They are transcribed paper values,
not measurements from this artifact run. Other protocols are excluded.
`normal` means Ours, `prefix` means Ours-Px, and metric `0` means L-infinity.

## Automatic figures

After Claim 2 or Claim 3 completes, the wrapper writes:

| Output | Contents |
|---|---|
| `paper-plots/*.svg` | Paper and measured runtime curves |
| `paper-comparison.md` | Figures and a table of matched time and communication values |

Each figure fixes the set size and metric. Rows correspond to dimensions;
columns separate Ours and Ours-Px. Claim 2 produces three figures for the full
matrix, or one for `--light`; Claim 3 produces three figures for its three metrics.

- **Horizontal axis:** `delta` values (`32`, `64`, `128`, `256`, `512`) shown as
  equally spaced categories, not a numeric linear or logarithmic scale.
- **Vertical axis:** original runtime in seconds, on a linear scale starting at zero.
- **Curves:** dashed gray for the paper; solid blue for measured results.
- **Limits:** each panel uses both series to set its y-axis, with at least 15%
  headroom and rounded ticks. There is no fixed paper-based cap: measurements
  taking 1.5x, 2x, or longer automatically expand the axis.
- **No normalization:** times are not divided by the value at `delta=32`.

Figures are generated only as SVG, viewable in a browser or Markdown preview.
Plotting uses the Python standard library and the project's `summarize_results`
module, which also depends only on the standard library. No third-party packages
or PNG conversion are required. No coefficients, speedup rankings, or automatic
trend pass/fail judgments are produced. Previous generated comparison CSV and statistics/speedup reports
are removed when the same output directory is reused.

Configurations are matched exactly by mode, assumption, side, metric, dimension,
threshold, and set size. Missing, unexpected, or duplicate configurations fail
rather than silently changing the plotted data. Claim 2 `--light` selects only
the 30 matching paper entries at `n=4096`.

## Runtime scope

Reported time follows the original per-protocol scope, not end-to-end wall time.
Synthetic input generation and socket creation are excluded. Unique-cell normal
and L-infinity prefix, and unique-block L-infinity prefix, also exclude the
programmed key/value construction; their query construction is timed on every
trial. Unique-block normal and both Lp prefix families time all input preparation
on every trial. The sender-side unique-cell protocols follow the same split.

The verbose `input preparation done` marker is inside each timed trial. OPRF,
OKVS encoding/decoding, MPC, final transfer, and enabled correctness checks remain
timed. The reported result divides the timed interval by the number of trials.

Older measurements that excluded additional input preparation must be rerun
before using them for this comparison; replotting cannot correct their timings.

## Plot saved measurements

No protocol rerun is required:

```bash
python3 scripts/reproduction/compare_paper_results.py \
    --reference claims/claim2/paper-results.csv \
    --results artifact-results/claim2-light/unique-cell.txt \
    --size 4096 --output-dir artifact-results/claim2-light
```

For the complete Table 2 matrix, omit `--size`. For Table 3, use
`claims/claim3/paper-results.csv` and the Claim 3 `unique-block.txt` log.
Add `--trials N` if the log was produced with `TRIALS=N` (default: 1).
Plots read the original log values, not the rounded Markdown table.
Legacy summary CSV files remain supported as inputs; no paired CSV reports are generated.
