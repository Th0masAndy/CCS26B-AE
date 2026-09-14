# Claim 3: unique-block evaluation

We claim that **the runtime and communication evaluation of the receiver-sided
unique-block protocols in the main-paper unique-block table is reproducible
with this artifact**.

## Experiment matrix

The experiment evaluates normal and prefix modes over:

- set size: $n=2^{12}$;
- dimension: $d=2,4,6$;
- threshold: $\delta=32,64,128,256,512$;
- metric: $L_\infty$, $L_1$, and $L_2$;
- internal trials per configuration: one by default (`TRIALS`).

This gives 45 parameter tuples in each mode and 90 program executions in total.
Each execution runs `TRIALS` internal trials and reports their average. Every
trial enables correctness checking with 16 planted matches (`-inter 16`).

## Experiment command

From the artifact root, run:

```bash
bash claims/claim3/run.sh
```

For repeated measurements:

```bash
TRIALS=10 bash claims/claim3/run.sh
```

Results are written to `artifact-results/claim3/` unless
`FPSI_RESULT_DIR` is set.

## Comparison with Table 3

[paper-results.csv](./paper-results.csv) contains the 90 Ours/Ours-Px entries
transcribed from [Table 3](./table3.png). After the benchmark, the wrapper
plots paper and measured runtimes against `delta`, using original seconds.
Dimensions and modes have separate panels; each linear y-axis starts at zero
and automatically expands to include both series with headroom.

The run produces three SVG figures, one per distance metric.
Open `paper-comparison.md` to view the figures, or open the SVG files in a browser.
See the [plotting guide](../paper-comparison.md) for details.

## Resources

- Machine: one supported x86-64 host, preferably otherwise idle;
- Typical runtime: several hours, depending on the host.

This claim already uses $n=2^{12}$. Peak RSS for the largest
$d=6,\delta=512$ cases is:

| Mode / metric | Peak RSS | Status |
|---|---:|---|
| Normal, $L_\infty$ | 198.5 GiB | measured, verified |
| Normal, $L_1/L_2$ | approximately 198.5 GiB | same bounded pre-metric OPPRF path; later arrays are small |
| Prefix, $L_\infty$ | 5.42 GiB | measured, verified |
| Prefix, $L_1$ | 9.84 GiB | measured, verified |
| Prefix, $L_2$ | 9.85 GiB | measured, verified |

These resource measurements used the earlier `-inter 4` setting; current runs
use `-inter 16`.

The normal protocols construct 1,612,185,600 key/value pairs at this largest
point before the metric-specific branch. The local PRF is evaluated in bounded
batches, reducing the measured $L_\infty$ peak from the 468.0 GiB unbatched
baseline to 198.5 GiB without changing communication or correctness. L1 and L2
use the same OPPRF input and encoding; their later arithmetic arrays contain
only $n d=24,576$ entries and are comparatively negligible. A dedicated
256 GiB host is recommended to leave headroom for the OS and allocator
variation.
The historical $n=2^{16}$ normal allocation reached 731.6 GiB before hitting
the underlying 32-bit parameter-size limit, which is why this artifact does
not request that configuration.

See [expected.md](./expected.md) for output files and comparison criteria.
