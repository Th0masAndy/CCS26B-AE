# Efficient Fuzzy PSI under One-Sided Assumptions

FPSI is a research prototype for fuzzy private set intersection under
one-sided assumptions. It implements the unique-cell and unique-block protocol
families for $L_\infty$, $L_1$, and $L_2$ distances.

> **Artifact reviewer? Start with the three commands below.** They check the
> host, build the complete project, validate every protocol family, and create
> a small result summary.

## 🚀 Quick start

The reference platform is Ubuntu 24.04 on x86_64 with GCC 13. The CPU must
provide AES, PCLMUL, SSE2, and SSE4.1. ARM64 and Apple Silicon, including AMD64
emulation, are not supported.

```bash
./scripts/preflight.sh
./scripts/build.sh
./scripts/run_reproduction.sh --quick
```

For a claim-by-claim evaluation roadmap, use [claims/README.md](./claims/README.md).
Each claim has one command, explicit outputs, and objective pass criteria.

Expected time on an 8-core machine:

| Step | Typical time | Success indicator |
|---|---:|---|
| Environment preflight | below 1 minute | `✅ Preflight passed` |
| Fresh build | 10–20 minutes | `✅ Build complete: .../code/build/fpsi` |
| Quick reproduction | below 2 minutes | `✅ [smoke] PASS: 6 protocol cases and 1 parameter guard` |

The quick workflow writes raw output, host information, CSV, and Markdown to
`artifact-results/`:

```text
artifact-results/
├── environment.txt
├── quick.txt
├── summary.csv
└── summary.md
```

The build and smoke test need at least 16 GiB RAM. Claim 2 peaks at 62.8 GiB,
while Claim 3's unique-block normal mode peaks at 198.5 GiB at $n=2^{12}$.
Use a dedicated 256 GiB host for the complete evaluation. By default, the build
script chooses
conservative parallelism from the available CPUs and memory. Override it only
when appropriate:

```bash
JOBS=32 ./scripts/build.sh
```

System packages are installed through `apt`; this step needs root or `sudo`.
If they are already installed, use `FPSI_SKIP_SYSTEM_PACKAGES=1`.

### Optional Docker path

Docker is an alternative isolated build path, not a requirement:

```bash
docker build -f code/Dockerfile -t fpsi-ae .
docker run --rm fpsi-ae ./scripts/run_reproduction.sh --quick
```

## ✅ What the artifact checks

The quick workflow generates deterministic synthetic point sets, plants four
fuzzy matches, runs representative protocols, and checks the recovered result
against the planted ground truth. A mismatch terminates the script.

| Assumption | Direction | Normal | Prefix |
|---|---|---|---|
| uniqueCell | receiver | L0, L1, L2 | L0, L1, L2 |
| uniqueCell | sender | L0, L1, L2 | L0 |
| uniqueBlock | receiver | L0, L1, L2 | L0, L1, L2 |

`L0` denotes $L_\infty$. Prefix executions require `delta` to be a power of
two. Synthetic test inputs are deterministic, while cryptographic primitives
use fresh randomness.

CTest exposes the same automated checks:

```bash
ctest --test-dir code/build --output-on-failure
```

## 🧪 Full reproduction

Run the complete parameter matrices with:

```bash
./scripts/run_reproduction.sh --full
```

This evaluates 180 protocol runs across the paper's two parameter tables. The
unique-cell table has 45 parameter tuples and runs receiver normal/prefix for
L0 (90 runs); the unique-block table has 15 parameter tuples and runs receiver
normal/prefix for L0, L1, and L2 (90 runs). Unique-cell uses
`n=2^8, 2^12, 2^16`, while unique-block uses `n=2^12`. Both use `d=2, 4, 6`
and `delta=32, 64, 128, 256, 512`. The run can take several hours and should
use an idle, large-memory machine.

The workflow is configurable without editing any script:

| Variable | Default | Purpose |
|---|---:|---|
| `REPETITIONS` | 1 | independent executions of every configuration |
| `TRIALS` | 1 | internal trials averaged by one execution |
| `VERIFY` | 1 | enable planted-match correctness checks |
| `FPSI_RESULT_DIR` | `artifact-results` | result directory |

### Reduced $n=2^{12}$ reproduction

To keep every mode, metric, dimension, threshold, and correctness check while
limiting both tables to $n=2^{12}$, run:

```bash
./scripts/run_reproduction.sh --light
```

This performs 30 unique-cell and 90 unique-block performance runs, in addition
to the smoke suite. It reduces the unique-cell runtime, but not the overall
memory peak: unique-block normal reaches 198.5 GiB. Use a 256 GiB host
for the combined workflow. To run only the genuinely lightweight unique-cell
claim, use `bash claims/claim2/run.sh --light` (8.45 GiB measured peak; 16 GiB
recommended). The unique-block prefix subset also stays below 10 GiB, but the
normal subset does not. See [the claims guide](./claims/README.md) for details.

For example:

```bash
REPETITIONS=10 TRIALS=1 VERIFY=1 \
  FPSI_RESULT_DIR=artifact-results/full-10x \
  ./scripts/run_reproduction.sh --full
```

The generated summary groups identical configurations and reports the mean and
population standard deviation of runtime and communication. Communication
should remain stable for a fixed revision and parameter set. Runtime depends on
the processor, compiler, memory bandwidth, system load, virtualization, and
network conditions; compare trends and relative costs on the same machine.

Measure peak memory for one configuration with:

```bash
./scripts/measure_case.sh large-case \
  -assumption 0 -p 0 -nn 16 -d 6 -delta 512 \
  -inter 4 -try 1 -v 1
```

## Troubleshooting

| Symptom | Resolution |
|---|---|
| `Illegal instruction` | Run `scripts/preflight.sh`; the host is usually ARM64 or is missing a required x86 instruction. |
| Compiler process is killed | Lower parallelism, for example `JOBS=4 ./scripts/build.sh`, and check available memory. |
| `GCC 13+ is required` | Use Ubuntu 24.04/GCC 13 or the Docker path. |
| Incomplete dependency directory | Remove only the dependency directory named by `scripts/build.sh`, then rerun it. |
| Runtime differs from the paper | Record `environment.txt`, repeat the case, and compare trends and communication rather than exact wall-clock values. |

If a build was interrupted, do not pre-create `code/thirdparty/` contents manually.
The build script is resumable and reports the exact incomplete directory when
manual cleanup is necessary.

## Repository guide

```text
code/                 self-contained implementation root
├── .clangd           editor and language-server configuration
├── CMakeLists.txt    build and CTest configuration
├── Dockerfile        optional reference environment
├── Dockerfile.dockerignore
│                    container build-context exclusions
├── README.md         implementation guide
├── fpsi/             source code grouped by module
├── build/            generated executable and CMake files
└── thirdparty/       generated pinned dependencies
scripts/              build, test, benchmark, analysis, and release tools
claims/               paper claims, experiment commands, and pass criteria
README.md              reviewer entry point
LICENSE                MIT license
CITATION.cff           machine-readable citation metadata
```

Reviewers only need this file. Researchers who want to reuse or modify the
implementation can continue with [code/README.md](./code/README.md).

| Task | Script |
|---|---|
| Build | `scripts/build.sh` |
| Correctness smoke test | `scripts/run_smoke.sh` |
| Quick/full reproduction | `scripts/run_reproduction.sh` |
| Unique-cell matrix | `scripts/bench_unique_cell.sh` |
| Unique-block matrix | `scripts/bench_unique_block.sh` |
| Result summarization | `scripts/summarize_results.py` |
| Single-case resource measurement | `scripts/measure_case.sh` |
| Source release archive | `scripts/package_release.sh` |
| Claim-by-claim evaluation | `claims/README.md` |
| Optional network emulation | `scripts/throttle.sh` |

<details>
<summary><strong>Command-line reference and examples</strong></summary>

Run `./code/build/fpsi -h` for built-in help.

| Flag | Meaning | Values / notes |
|---|---|---|
| `-p` | Distance metric | `0`: $L_\infty$, `1`: $L_1$, `2`: $L_2$ |
| `-assumption` | One-sided assumption | `0`: unique cell, `1`: unique block |
| `-prefix` | Prefix optimization | flag; `delta` must be a power of two |
| `-sender` | Protocol direction | flag; select sender-sided unique-cell |
| `-n`, `-nn` | Set size | exact size or its base-2 logarithm |
| `-d` | Dimension | integer, default `2` |
| `-delta` | Distance threshold | integer, default `2` |
| `-inter` | Planted match count | integer, default `4` |
| `-try` | Internal trial count | integer, default `1` |
| `-v` | Correctness/debug output | `0`: off, `1`: on |

Examples:

```bash
# Receiver-sided unique-cell, normal, L-infinity
./code/build/fpsi -assumption 0 -p 0 -nn 8 -d 4 -delta 32 -v 1

# Receiver-sided unique-cell, prefix, L1
./code/build/fpsi -assumption 0 -prefix -p 1 -nn 8 -d 4 -delta 32 -v 1

# Sender-sided unique-cell, normal, L2
./code/build/fpsi -assumption 0 -sender -p 2 -nn 8 -d 4 -delta 32 -v 1

# Receiver-sided unique-block, prefix, L2
./code/build/fpsi -assumption 1 -prefix -p 2 -nn 8 -d 4 -delta 32 -v 1
```

</details>

<details>
<summary><strong>Pinned source dependencies</strong></summary>

| Dependency | Commit | Purpose |
|---|---|---|
| [secure-join](https://github.com/Visa-Research/secure-join) | `df62f360df0c2dfb8288f8f7b99ccf3472318e87` | shared-output OPRF |
| [volePSI](https://github.com/ladnir/volepsi) | `59e06bca81a3287257522cd261bad71e37780642` | OKVS and PSI primitives |
| [libOTe](https://github.com/osu-crypto/libOTe) | `d21bc4d7aae941e276b92615252fd1760c902890` | OT and circuit primitives |
| [BLAKE3](https://github.com/BLAKE3-team/BLAKE3) | `c7f0d216e6fc834b742456b39546c9835baa1277` | hashing |

`scripts/build.sh` pins both secure-join and volePSI to the same libOTe
revision. Third-party code remains subject to its own license.

</details>

<details>
<summary><strong>Baseline implementations</strong></summary>

| Work | Code | Paper |
|---|---|---|
| van Baarsen and Pu, EUROCRYPT 2024 | [code](https://github.com/sihangpu/fuzzy_PSI) | [paper](https://eprint.iacr.org/2024/330) |
| Gao et al., ASIACRYPT 2024 | [code](https://github.com/ql70ql70/Fuzzy-Private-Set-Intersection-from-Fuzzy-Mapping) | [paper](https://eprint.iacr.org/2024/1462) |
| Dang et al., CCS 2025 | [code](https://github.com/zhouxv/ourFuzzyPSI-C) | [paper](https://eprint.iacr.org/2025/1796) |
| Bui et al., ASIACRYPT 2025 | [code](https://github.com/phuocchubeo123/SaPSI) | [paper](https://eprint.iacr.org/2025/907.pdf) |

</details>

## Limitations and safety

- This is a research prototype, not production software or a security audit.
- Inputs are generated in memory; application-data ingestion is out of scope.
- Both parties run as threads in one process over local sockets.
- Network emulation is never enabled automatically. `scripts/throttle.sh`
  changes a host qdisc, requires `sudo`, and must be cleaned up with
  `./scripts/throttle.sh del [interface]`.
- Create public source archives with `./scripts/package_release.sh <version>`;
  its allowlist excludes builds, dependencies, results, downloaded projects,
  and private review correspondence.

## Acknowledgements, citation, and license

Parts of the prefix optimization are adapted from
[Dang et al.](https://github.com/zhouxv/ourFuzzyPSI-C). We thank Peter Rindal
for the open-source [secure-join](https://github.com/ladnir/secure-join) and
[volePSI](https://github.com/ladnir/volepsi) libraries.

```bibtex
@inproceedings{yang2026efficient,
  title={Efficient Fuzzy PSI under One-Sided Assumptions},
  author={Yang, Xinpeng and Hao, Meng and Jia, Yanxue and Weng, Chenkai and Wen, Yonggang and Zhang, Tianwei},
  booktitle={Proceedings of the 2026 ACM SIGSAC Conference on Computer and Communications Security},
  year={2026}
}
```

Machine-readable citation metadata is in [CITATION.cff](./CITATION.cff). FPSI
is released under the [MIT License](./LICENSE).
