# Expected result for Claim 2

A successful default run creates:

```text
artifact-results/claim2/
├── environment.txt
├── unique-cell.txt
├── summary.md
├── paper-comparison.md
└── paper-plots/
    └── runtime-*.svg
```

The raw log and summary must contain 90 distinct configurations: 45 normal and
45 prefix rows, regardless of `TRIALS`. Each configuration must report
`Total 16/16 matches found!` once per trial (`-inter 16`):
`90 * TRIALS` markers in total.
The script must finish with:

```text
✅ Claim 2 full complete
```

The optional `--light` run instead writes to `artifact-results/claim2-light/`
and must contain 30 configurations: 15 normal and 15 prefix rows. It finishes
with `✅ Claim 2 light complete`. Its raw log must contain `30 * TRIALS`
correctness markers, all `Total 16/16 matches found!`.

`summary.md` reports the trial count and mean communication
and runtime for every configuration. Communication should remain stable for
the same revision and parameters. Absolute runtime is hardware-dependent;
reproduce paper trends and compare normal versus prefix on the same machine rather than requiring exact
wall-clock equality.

The table in `paper-comparison.md` must contain 90 matched rows (30 for `--light`),
with the original paper and measured values. `paper-comparison.md` embeds
three SVG figures (one for `--light`), plotting time in seconds against `delta`.
Each dimension/mode panel contains the paper and measured curves with equally
spaced δ values and a shared, automatically scaled linear time axis. All plotted
values must remain inside the axes, including when measurements are slower than
the paper.

No correlation coefficients or mode-winner summaries are generated.
Missing or mismatched configurations fail the comparison. See the
[plotting guide](../paper-comparison.md) for the layout and axis behavior.
