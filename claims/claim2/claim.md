# Claim 2: unique-cell evaluation

We claim that **the runtime and communication evaluation of the receiver-sided
unique-cell $L_\infty$ protocols in the main-paper unique-cell table is
reproducible with this artifact**.

## Parameter configurations

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

For smaller runs, use the shared
[partial reproduction or mini benchmark](../../README.md#-full-reproduction).

## Comparison with Table 2 in the Paper

After the run, open `paper-comparison.md` in the results directory to view
nine runtime comparison figures, one per `(n, d)` pair. The SVG files in
`paper-plots/` can also be opened in a browser.

## Requirements

- Hardware: one supported x86-64 host; 80 GiB RAM recommended.
- Runtime: approximately 3–4 hours after compilation with `TRIALS=1`.

See [expected.md](./expected.md) for expected outputs.
