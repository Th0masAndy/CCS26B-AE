# Expected result for Claim 3

A successful default run creates:

```text
artifact-results/claim3/
├── environment.txt
├── unique-block.txt
├── summary.md
├── paper-comparison.md
└── paper-plots/
    └── runtime-*.svg
```

The raw log and summary must contain 90 distinct configurations: 45 normal and
45 prefix rows, covering all three metrics, regardless of `TRIALS`. Each
configuration must report `Total 16/16 matches found!` once per trial:
`90 * TRIALS` markers in total. The script must finish with:

```text
✅ Claim 3 complete
```

`summary.md` reports the trial count and mean communication
and runtime for every configuration. Communication should remain stable for
the same revision and parameters. Absolute runtime is hardware-dependent;
reproduce paper trends and compare modes and metrics on the same machine rather than requiring exact
wall-clock equality.

The table in `paper-comparison.md` must contain 90 matched rows,
with the original paper and measured values. `paper-comparison.md` embeds
three SVG figures, plotting time in seconds against `delta`.
Each dimension/mode panel contains the paper and measured curves with equally
spaced δ values and a shared, automatically scaled linear time axis. All plotted
values must remain inside the axes, including when measurements are slower than
the paper.

No correlation coefficients or mode-winner summaries are generated.
Missing or mismatched configurations fail the comparison. See the
[plotting guide](../paper-comparison.md) for the layout and axis behavior.
