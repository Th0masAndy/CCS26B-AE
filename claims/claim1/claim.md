# Claim 1: protocol correctness

We claim that **the artifact correctly executes every implemented one-sided
FPSI protocol family represented by the smoke suite and recovers all planted
fuzzy matches**.

## Paper and implementation coverage

The experiment covers receiver-sided unique-cell and unique-block protocols in
normal and prefix modes, plus sender-sided unique-cell protocols. Across these
cases it exercises $L_\infty$, $L_1$, and $L_2$ code paths. It also checks that
a prefix execution rejects a non-power-of-two `delta`.

## Experiment command

From the artifact root, run:

```bash
bash claims/claim1/run.sh
```

The wrapper invokes the deterministic quick reproduction and writes its output
to `artifact-results/claim1/`. To use another result directory:

```bash
FPSI_RESULT_DIR=/path/to/results bash claims/claim1/run.sh
```

## Resources

- Machine: one supported x86-64 host;
- Memory: 16 GiB is sufficient;
- Typical runtime: below 2 minutes after compilation.

See [expected.md](./expected.md) for the pass criteria.
