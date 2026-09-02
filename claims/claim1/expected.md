# Expected result for Claim 1

A successful run creates:

```text
artifact-results/claim1/
├── environment.txt
├── quick.txt
├── summary.csv
└── summary.md
```

The terminal must end with:

```text
✅ [smoke] PASS: 6 protocol cases and 1 parameter guard
✅ Quick reproduction complete
```

Each of the six protocol cases must contain `Total 4/4 matches found!`. The
wrapper exits nonzero if a protocol crashes, a planted match is missing, or the
invalid prefix parameter is accepted. Runtime and communication values may vary
across hosts; they are not correctness criteria for this claim.
