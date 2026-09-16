# Claim 3: unique-block evaluation

We claim that **the runtime and communication evaluation of the receiver-sided
unique-block protocols in the main-paper unique-block table is reproducible
with this artifact**.

## Requirements

- Hardware: one supported x86-64 host; 256 GiB RAM recommended.
- Runtime: approximately 2–3 hours after compilation with `TRIALS=1`.

## Parameter configurations

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

For smaller runs, use the shared
[partial reproduction or mini benchmark](../../README.md#-full-reproduction).

## Comparison with Table 3 in the Paper

After the run, open `paper-comparison.md` in the results directory to view
one runtime comparison figure covering all parameter groups. Columns show
dimensions; rows show metrics and modes. Open
`runtime-comparison.svg` in a browser to zoom in.

See [expected.md](./expected.md) for expected outputs.
