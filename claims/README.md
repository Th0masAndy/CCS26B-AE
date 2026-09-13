# Artifact claims

This directory maps the artifact's three evaluation claims to executable
experiments and explicit success criteria. Build the artifact once before
running a claim:

```bash
./scripts/preflight.sh
./scripts/build.sh
```

| Claim | Paper evidence | Command | Typical scope |
|---|---|---|---|
| [1. Protocol correctness](./claim1/claim.md) | All implemented one-sided protocol families | `bash claims/claim1/run.sh` | Smoke + matching boundaries, a few minutes |
| [2. Unique-cell evaluation](./claim2/claim.md) | Main-paper unique-cell performance table | `bash claims/claim2/run.sh` | 90 runs, several hours |
| [3. Unique-block evaluation](./claim3/claim.md) | Main-paper unique-block performance table | `bash claims/claim3/run.sh` | 90 runs, several hours |

## Resource profiles

| Experiment | Largest set size | Peak-RSS basis | Recommended RAM |
|---|---:|---:|---:|
| Claim 1 | small correctness cases | below the build requirement | 16 GiB |
| Claim 2, full | $2^{16}$ | 62.8 GiB measured | 80 GiB |
| Claim 2, `--light` | $2^{12}$ | 8.45 GiB measured | 16 GiB |
| Claim 3, prefix only | $2^{12}$ | 9.85 GiB measured | 16 GiB |
| Claim 3, including normal | $2^{12}$ | 198.5 GiB measured | 256 GiB |

For an all-$n=2^{12}$ evaluation, run:

```bash
bash claims/claim1/run.sh
bash claims/claim2/run.sh --light
bash claims/claim3/run.sh
```

This performs 120 performance runs (30 unique-cell and 90 unique-block), plus
the smoke and matching-boundary correctness suites. Although every performance case uses $n=2^{12}$,
unique-block normal needs 198.5 GiB at $d=6,\delta=512$; provision
256 GiB for this combined workflow. The command reduces unique-cell runtime,
but does not reduce the overall peak below Claim 3's normal-mode requirement.

Each claim directory contains:

- `claim.md`: the claim, paper mapping, experiment matrix, resources, and command;
- `expected.md`: generated files and objective success criteria;
- `run.sh`: the executable experiment wrapper.

Claims 2 and 3 use one process with both parties connected through local
sockets. Runtime depends on the CPU, memory bandwidth, system load, and network
emulation. Communication and qualitative trends should be compared on the same
revision and machine; exact wall-clock equality with the paper is not expected.
The full experiments use deterministic synthetic inputs and fresh
cryptographic randomness.
