# Expected result for Claim 1

## Successful run

The default run (`TRIALS=1`) passes all 240 correctness checks and ends with:

```text
✅ Claim 1 complete
```

Each output intersection is checked automatically against the expected sender points.

## Result files

Open files under `artifact-results/claim1/`:

| File / directory | What to check |
|---|---|
| `boundary/runs/summary.csv` | All test rows show `PASS`. |
| `boundary/runs/` | Individual test outputs and logs. |
| `boundary.txt` | Correctness-test log; check here if a test fails. |
| `quick.txt` | Smoke-test log. |
