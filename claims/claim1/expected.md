# Expected result for Claim 1

A successful run creates:

```text
artifact-results/claim1/
├── environment.txt
├── quick.txt
├── summary.csv
├── summary.md
├── boundary.txt
└── boundary/
    ├── data/
    │   ├── manifest.json
    │   └── <case>/          sender_data.txt, recver_data.txt, expected-*.txt
    └── runs/
        ├── summary.csv
        └── <case>/<mode>/run-<trial>/
                            inputs, output.txt, command.txt, protocol.log, result.json
```

With the default `TRIALS=1`, the terminal must end with:

```text
✅ [boundary] PASS: 240 executions across 16 modes; 0 failures
✅ Claim 1 complete
```

The smoke log must contain its six successful planted-match cases and the prefix
parameter guard. Each protocol case contains `Total 4/4 matches found!` exactly
`TRIALS` times.

The boundary summary must contain `240 * TRIALS` rows, all marked `PASS`.
Every execution must exit successfully and produce an `output.txt` exactly equal
to the sorted reference sender points. Missing, extra, duplicate, or incorrect
points fail even if the reported match count is correct. No matches require an
existing, empty output file; stale output is removed before each execution.

The wrapper exits nonzero on a failed comparison, protocol error, or timeout.
Inputs, expected answers, commands, and logs remain available for diagnosis.
Runtime and communication are not correctness criteria for this claim.
