# Artifact claims

Build the artifact using the [Quick start](../README.md#-quick-start), then run
these commands from the repository root:

| Claim | Command | Scope | Recommended RAM |
|---|---|---|---:|
| [1. Protocol correctness](./claim1/claim.md) | `bash claims/claim1/run.sh` | Smoke + edge-case correctness tests | 16 GiB |
| [2. Unique-cell evaluation](./claim2/claim.md) | `bash claims/claim2/run.sh` | Table 2: 90 configurations | 80 GiB |
| [3. Unique-block evaluation](./claim3/claim.md) | `bash claims/claim3/run.sh` | Table 3: 90 configurations | 256 GiB |

`TRIALS` defaults to 1; set it for repeated measurements. Use `FPSI_RESULT_DIR`
to change the output directory. Each claim's `claim.md` describes the experiment;
`expected.md` lists output files and pass criteria.

Runtime estimates are rounded from 1–1.5× the measured wall-clock time on the AMD EPYC
9554 reference host with `TRIALS=1`, excluding build time.

## Smaller runs

Use the shared [evaluation options](../README.md#-full-reproduction):

- **Partial reproduction:** 80 paper cases across both tables at $n=2^{12}$,
  $d=2,4$; `./scripts/reproduction/run.sh --partial`.
- **Mini benchmark:** the same 80 combinations at $n=2^{10}$;
  `./scripts/reproduction/run.sh --mini`.

## Runtime comparison

Claim 2 and Claim 3 automatically compare measured runtime and communication
with the paper's Ours/Ours-Px results in [Table 2](./claim2/paper-results.csv)
and [Table 3](./claim3/paper-results.csv).

Open the report in the corresponding results directory:

| Run | Report |
|---|---|
| Claim 2 or Claim 3 | `paper-comparison.md` |
| Partial | `unique-cell-comparison.md`, `unique-block-comparison.md` |
| Mini | `unique-cell-runtime.md`, `unique-block-runtime.md` |

Each report links to one SVG figure per protocol family. The x-axis shows
`delta`; the y-axis shows time in seconds. Dashed gray lines show paper results;
solid blue lines show measurements. Partial compares only the tested subset;
mini shows measurements only. Exact runtimes depend on the machine.

Plotting uses only the Python standard library. To replot saved logs without
rerunning protocols, see `python3 scripts/reproduction/compare_paper_results.py --help`.

## Timing scope

`Time(s)` is the average per-trial time, not the command's total runtime.
All protocols use the same timing scope:

- **Excluded:** input generation, OPPRF key/value construction (including
  padding), and socket setup.
- **Included:** query preparation, OPPRF (including OKVS encoding/decoding),
  MPC, final transfer, and correctness checks when enabled.
