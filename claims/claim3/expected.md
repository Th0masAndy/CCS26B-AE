# Expected result for Claim 3

A successful default run creates:

```text
artifact-results/claim3/
├── environment.txt
├── unique-block.txt
├── summary.csv
└── summary.md
```

The raw log and summary must contain 90 distinct configurations: 45 normal and
45 prefix rows, covering all three metrics. Every raw result must report
`Total 4/4 matches found!`, and the script must finish with:

```text
✅ Claim 3 complete
```

`summary.csv` and `summary.md` report communication and runtime for every
configuration. Communication should remain stable for the same revision and
parameters. Absolute runtime is hardware-dependent; reproduce paper trends and
compare modes and metrics on the same machine rather than requiring exact
wall-clock equality.
