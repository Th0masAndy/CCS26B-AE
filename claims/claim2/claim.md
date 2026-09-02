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
- repetitions: one by default.

This gives 45 parameter tuples in each mode and 90 protocol runs in total. Every
run enables correctness checking with four planted matches.

## Experiment command

From the artifact root, run:

```bash
bash claims/claim2/run.sh
```

For repeated measurements:

```bash
REPETITIONS=10 bash claims/claim2/run.sh
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

## Resources

- Machine: one supported x86-64 host, preferably otherwise idle;
- Typical runtime: several hours, depending on the host.

Peak RSS is for the single `fpsi` process, which contains both local protocol
parties. The following values are intended for machine planning:

| Profile / largest case | Peak RSS | Status | Recommended RAM |
|---|---:|---|---:|
| Full, normal, $n=2^{16},d=6,\delta=512$ | 62.8 GiB | measured, 4/4 correct | 80 GiB |
| Full, prefix, $n=2^{16},d=6,\delta=512$ | 56.8 GiB | measured | 80 GiB |
| Light, normal, $n=2^{12},d=6,\delta=512$ | 8.45 GiB | measured | 16 GiB |
| Light, prefix, $n=2^{12},d=6,\delta=512$ | 3.75 GiB | measured | 16 GiB |

The normal measurements completed with all four planted matches. Its OPPRF
masking phase evaluates the local PRF in bounded batches; this changes only the
temporary working set, not the encoded key/value set or communication. The full
prefix peak was captured after OPPRF; an earlier complete run measured
57.1 GiB, consistent with the value above. Allocator, compiler, and host
differences can change these values slightly.

See [expected.md](./expected.md) for output files and comparison criteria.
