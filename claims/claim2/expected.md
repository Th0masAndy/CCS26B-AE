# Expected result for Claim 2

A successful default run creates:

```text
artifact-results/claim2/
├── environment.txt
├── unique-cell.txt
├── summary.csv
└── summary.md
```

The raw log and summary must contain 90 distinct configurations: 45 normal and
45 prefix rows. Every raw result must report `Total 4/4 matches found!`, and the
script must finish with:

```text
✅ Claim 2 full complete
```

The optional `--light` run instead writes to `artifact-results/claim2-light/`
and must contain 30 configurations: 15 normal and 15 prefix rows. It finishes
with `✅ Claim 2 light complete`. The same correctness requirement applies to
every row.

`summary.csv` and `summary.md` report communication and runtime for every
configuration. Communication should remain stable for the same revision and
parameters. Absolute runtime is hardware-dependent; reproduce paper trends and
compare normal versus prefix on the same machine rather than requiring exact
wall-clock equality.
