# Claim 2: unique-cell evaluation

We claim that **the runtime and communication evaluation of the receiver-sided
unique-cell $L_\infty$ protocols in the main-paper unique-cell table is
reproducible with this artifact**.

## Experiment matrix

The experiment evaluates both normal and prefix modes over:

- set size: $n=2^8,2^{12},2^{16}$;
- dimension: $d=2,4,6$;
- threshold: $\delta=32,64,128,256,512$;
- metric: $L_\infty$;
- internal trials per configuration: one by default (`TRIALS`).

This gives 45 parameter tuples in each mode and 90 program executions in total.
Each execution runs `TRIALS` internal trials and reports their average. Every
trial enables correctness checking with 16 planted matches (`-inter 16`).

## Experiment command

From the artifact root, run:

```bash
bash claims/claim2/run.sh
```

For repeated measurements:

```bash
TRIALS=10 bash claims/claim2/run.sh
```

Results are written to `artifact-results/claim2/` unless
`FPSI_RESULT_DIR` is set.

### Lighter $n=2^{12}$ option

Reviewers with a smaller-memory machine can run only the middle set size:

```bash
bash claims/claim2/run.sh --light
```

This keeps every dimension, threshold, mode, and correctness check, but reduces
the matrix to 15 tuples per mode (30 protocol runs). Results are written to
`artifact-results/claim2-light/` by default.

## Comparison with Table 2

[paper-results.csv](./paper-results.csv) contains the 90 Ours/Ours-Px entries
transcribed from [Table 2](./table2.png). After the benchmark, the wrapper
plots paper and measured runtimes against `delta`, using original seconds.
Dimensions and modes have separate panels; each linear y-axis starts at zero
and automatically expands to include both series with headroom.

The full run produces three SVG figures, one per set size; `--light` produces
one for `n=4096`.
Open `paper-comparison.md` to view the figures, or open the SVG files in a browser.
See the [plotting guide](../paper-comparison.md) for details.

## Resources

- Machine: one supported x86-64 host, preferably otherwise idle;
- Typical runtime: several hours, depending on the host.

Peak RSS is for the single `fpsi` process, which contains both local protocol
parties. The following values are intended for machine planning:

| Profile / largest case | Peak RSS | Status | Recommended RAM |
|---|---:|---|---:|
| Full, normal, $n=2^{16},d=6,\delta=512$ | 62.8 GiB | measured, verified | 80 GiB |
| Full, prefix, $n=2^{16},d=6,\delta=512$ | 56.8 GiB | measured | 80 GiB |
| Light, normal, $n=2^{12},d=6,\delta=512$ | 8.45 GiB | measured | 16 GiB |
| Light, prefix, $n=2^{12},d=6,\delta=512$ | 3.75 GiB | measured | 16 GiB |

These resource measurements used the earlier `-inter 4` setting; current runs
use `-inter 16`. The normal OPPRF
masking phase evaluates the local PRF in bounded batches; this changes only the
temporary working set, not the encoded key/value set or communication. The full
prefix peak was captured after OPPRF; an earlier complete run measured
57.1 GiB, consistent with the value above. Allocator, compiler, and host
differences can change these values slightly.

See [expected.md](./expected.md) for output files and comparison criteria.
