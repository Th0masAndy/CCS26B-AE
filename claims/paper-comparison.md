# Runtime comparison

Claim 2 and Claim 3 automatically compare measured runtimes and communication
with the **Ours** (`normal`) and **Ours-Px** (`prefix`) results in Table 2 and Table 3 of the paper.
The values are saved in [claim2/paper-results.csv](./claim2/paper-results.csv)
and [claim3/paper-results.csv](./claim3/paper-results.csv).

## View results

Open the Markdown report in the corresponding results directory, or open its
SVG figure in a browser to zoom in.

| Run | Report | Figure |
|---|---|---|
| Claim 2 or Claim 3 | `paper-comparison.md` | `runtime-comparison.svg` |
| Partial | `unique-cell-comparison.md`, `unique-block-comparison.md` | `unique-cell-runtime.svg`, `unique-block-runtime.svg` |
| Mini | `unique-cell-runtime.md`, `unique-block-runtime.md` | `unique-cell-runtime.svg`, `unique-block-runtime.svg` |

- **Partial:** compares only the tested subset: $n=2^{12}$, $d=2,4$.
- **Mini:** plots measurements at $n=2^{10}$, $d=2,4$, without paper data.

Each figure combines all its panels, keeping dimensions, set sizes or metrics,
and normal/prefix modes separate. The horizontal axis shows equally spaced
`delta` values; the vertical axis shows seconds on an automatically scaled
linear axis starting at zero. Dashed gray lines show paper results; solid blue
lines show measurements. Absolute runtimes depend on the machine.

Plotting requires only the Python standard library; no additional packages are needed.

## Replot saved results

Run from the repository root; no protocol rerun is needed:

```bash
python3 scripts/reproduction/compare_paper_results.py \
    --reference claims/claim2/paper-results.csv \
    --results artifact-results/claim2/unique-cell.txt \
    --output-dir artifact-results/claim2
```

For Claim 3, use its reference file, `unique-block.txt` log, and output directory.
For Partial or Mini, use the corresponding logs and output directory, then:

- **Partial:** add `--size 4096 --dimensions 2 4` and
  `--name unique-cell` or `--name unique-block`.
- **Mini:** omit `--reference`; add `--size 1024 --dimensions 2 4` and the same `--name` option.

Add `--trials N` if the log was produced with `TRIALS=N` (default: 1).

## Timing scope

Reported seconds are protocol time averaged over trials, not process wall time.
Synthetic input generation and socket creation are excluded. OPRF, OKVS, MPC,
final transfer, and enabled correctness checks are included.

| Protocol | Input preparation included in timing |
|---|---|
| Unique-cell normal; unique-cell/block $L_\infty$ prefix | Query construction only; programmed key/value construction is excluded |
| Unique-block normal; unique-cell/block $L_p$ prefix | All protocol input preparation |

Sender-sided unique-cell protocols use the same timing split.
