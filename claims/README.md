# Artifact claims

Build the artifact using the [Quick start](../README.md#-quick-start), then run
these commands from the repository root:

| Claim | Command | Scope | Recommended RAM |
|---|---|---|---:|
| [1. Protocol correctness](./claim1/claim.md) | `bash claims/claim1/run.sh` | Smoke + matching-boundary tests | 16 GiB |
| [2. Unique-cell evaluation](./claim2/claim.md) | `bash claims/claim2/run.sh` | Table 2: 90 configurations | 80 GiB |
| [3. Unique-block evaluation](./claim3/claim.md) | `bash claims/claim3/run.sh` | Table 3: 90 configurations | 256 GiB |

`TRIALS` defaults to 1; set it for repeated measurements. Use `FPSI_RESULT_DIR`
to change the output directory. Each claim's `claim.md` describes the experiment;
`expected.md` lists output files and pass criteria.

## Smaller runs

For Claim 2 at only $n=2^{12}$ (30 configurations, recommended RAM: 16 GiB):

```bash
bash claims/claim2/run.sh --light
```

This does not reduce Claim 3's memory requirements. For lower-cost evaluation
across both tables, see [partial reproduction and mini benchmark](../README.md#full-reproduction).

Compare communication and runtime trends with the paper; exact wall-clock
agreement is not required.
