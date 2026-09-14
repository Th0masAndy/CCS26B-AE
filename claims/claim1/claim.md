# Claim 1: protocol correctness

We claim that **all 16 implemented one-sided FPSI modes recover the exact fuzzy
intersection on the generated matching-boundary cases**, in addition to passing
the planted-match smoke suite.

## Matching-boundary coverage

Inputs are nonempty sets of unsigned integer points satisfying the selected
protocol's one-sided assumption. These tests concern matching behavior, not
invalid inputs or integer-domain limits.

We construct the following matching-boundary cases:

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

## Experiment command

From the artifact root, run:

```bash
bash claims/claim1/run.sh
```

The wrapper runs the existing quick smoke suite followed by the matching-boundary
suite. Results are saved to `artifact-results/claim1/`; override the location with
`FPSI_RESULT_DIR`. The existing smoke suite also checks prefix-parameter rejection.

To generate reusable point files and expected answers without running FPSI:

```bash
python3 scripts/data/generate_boundary_data.py --output-dir /tmp/fpsi-matching-data
```

To check those files:

```bash
python3 scripts/data/check_boundary_inputs.py --data-dir /tmp/fpsi-matching-data \
    --output-dir artifact-results/matching-check
```

`TRIALS` defaults to 1. Each boundary trial starts a separate process with
`-try 1`, so the actual recovered points are checked on every execution.
Input data is reproducible; protocol randomness remains fresh.

## Resources

- Machine: one supported x86-64 host;
- Memory: 16 GiB is sufficient;
- Typical runtime: a few minutes after compilation with `TRIALS=1`.

See [expected.md](./expected.md) for the pass criteria.
