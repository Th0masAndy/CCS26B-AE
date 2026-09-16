# Claim 1: protocol correctness

We claim that **the implemented protocols correctly compute fuzzy private set
intersection: they output all sender elements that are close to the receiver set**.

## Requirements

- Machine: one supported x86-64 host;
- Memory: 16 GiB is sufficient;
- Runtime: approximately 3–5 minutes after compilation with `TRIALS=1`.

## Correctness test cases

Inputs are nonempty sets of unsigned integer points satisfying the selected
protocol's one-sided assumption. These tests focus on correct matching behavior,
especially at and around the distance threshold; they do not cover invalid
inputs or integer-domain limits.

We construct the following cases:

- No matches and full intersections, including exact and fuzzy matches.
- Distances `delta-1`, `delta`, and `delta+1`: match, match, and no match.
- Many-to-one and one-to-many matches: return every matching sender point once.
- Multidimensional thresholds and matches across cell/block boundaries.
- Coordinates close to different receiver points, which must not form a false match.
- Partial intersections with independently shuffled input order.

The generator uses `delta=32`, dimensions 2, 3, 4, and 6, and a fixed data seed.
Its 16 datasets produce 240 applicable dataset/mode combinations, covering
receiver unique-cell/unique-block normal and prefix modes, plus sender unique-cell
normal modes and its $L_\infty$ prefix mode. Many-to-one/one-to-many cases run only
where their geometry satisfies the corresponding assumption.

The checker invokes FPSI with `-i` and compares every point in `output.txt` with
an independent Python integer-distance reference, rather than checking only
the match count or a console success message.

## Evaluation workflow

After building FPSI, run the complete Claim 1 evaluation from the artifact root:

```bash
bash claims/claim1/run.sh
```

The wrapper automatically:

1. Runs the quick smoke test and the prefix-parameter guard.
2. Generates the correctness test data and exact reference intersections.
3. Executes every applicable protocol configuration using file input.
4. Compares every element in `output.txt` with the reference result.

A successful default run performs 240 executions with no failures. Results are
saved to `artifact-results/claim1/`; set `FPSI_RESULT_DIR` to use another
directory. `TRIALS` defaults to 1 and repeats the complete correctness check.

## Reusing test data (optional)

Generate the point files and reference answers without running FPSI:

```bash
python3 scripts/data/generate_boundary_data.py --output-dir /tmp/fpsi-matching-data
```

Then run the checker on those files:

```bash
python3 scripts/data/check_boundary_inputs.py --data-dir /tmp/fpsi-matching-data \
    --output-dir artifact-results/matching-check
```

See [expected.md](./expected.md) for the pass criteria.
