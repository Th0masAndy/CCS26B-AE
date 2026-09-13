# Efficient Fuzzy PSI under One-Sided Assumptions

FPSI is a research prototype for fuzzy private set intersection under
one-sided assumptions. It implements the unique-cell and unique-block protocol
families for $L_\infty$, $L_1$, and $L_2$ distances.


## 🖥️ Platform requirements

- **Reference platform:** Ubuntu 24.04 on x86_64 with GCC 13.
- **Required CPU instructions:** AES, PCLMUL, SSE2, and SSE4.1.
- **Unsupported platforms:** ARM64 and Apple Silicon, including AMD64 emulation.

## 🚀 Quick start

1. **Check the environment**

   Run the read-only preflight check. It verifies the operating system,
   architecture, CPU instructions, compiler, memory, disk space, and basic tools.

   ```bash
   ./scripts/preflight.sh
   ```


2. **Build FPSI**

   The build script installs the required Ubuntu packages, fetches pinned
   dependencies into `code/thirdparty/`, and creates `code/build/fpsi`. This step
   requires root or `sudo`; set `FPSI_SKIP_SYSTEM_PACKAGES=1` when the packages are
   already installed.

   ```bash
   ./scripts/build.sh
   ```

3. **Run the quick validation**

   Run a quick correctness check and save the results to `artifact-results/`.

   ```bash
   ./scripts/run_reproduction.sh --quick
   ```


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

The build and smoke test need at least 16 GiB RAM. The full unique-cell evaluation
peaks at 62.8 GiB, while unique-block normal mode peaks at 198.5 GiB at $n=2^{12}$.
Use a dedicated 256 GiB host for the complete evaluation.

### Optional Docker path

Docker is an alternative isolated build path, not a requirement:

```bash
docker build -f code/Dockerfile -t fpsi-ae .
docker run --rm fpsi-ae ./scripts/run_reproduction.sh --quick
```

## File input

Use `-i <directory>` to read `sender_data.txt` and `recver_data.txt` from that
directory and write matching sender points to `output.txt` in the same directory:

```bash
./code/build/fpsi -assumption 0 -p 2 -delta 32 -i ./my-data
```

Each nonblank line is one point: unsigned 64-bit decimal coordinates separated
by spaces or tabs, with no header. For example:

```text
0 0
128 128
```

Both files must have the same point count and dimension, with no duplicate points
within either file. The point count and dimension are inferred from the files.
Inputs must satisfy the selected protocol's one-sided assumption (unique-cell
or unique-block).

Without the `-i` option, the program uses randomly generated simulation data.

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

## Repository structure

```text
code/                 self-contained implementation root        
├── CMakeLists.txt    build and CTest configuration
├── Dockerfile        optional reference environment
├── README.md         implementation guide
├── fpsi/             source code grouped by module
├── build/            generated executable and CMake files
└── thirdparty/       generated pinned dependencies
scripts/              build, test, benchmark, analysis, and release tools
claims/               paper claims, experiment commands, and pass criteria
README.md             reviewer entry point
LICENSE               MIT license
CITATION.cff          machine-readable citation metadata
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

## Command-line Flags

Run `./code/build/fpsi -h` for built-in help.

| Flag | Meaning | Values / notes |
|---|---|---|
| `-p` | Distance metric | `0`: $L_\infty$, `1`: $L_1$, `2`: $L_2$ |
| `-assumption` | One-sided assumption | `0`: unique cell, `1`: unique block |
| `-prefix` | Prefix optimization | flag; `delta` must be a power of two |
| `-sender` | Protocol direction | flag; select sender-sided unique-cell |
| `-i` | Input directory | `sender_data.txt`, `recver_data.txt`; writes `output.txt` |
| `-n`, `-nn` | Set size | exact size or its base-2 logarithm; inferred with `-i` |
| `-d` | Dimension | integer, default `2` |
| `-delta` | Distance threshold | integer, default `2` |
| `-inter` | Planted match count | integer, default `floor(log2(n))` |
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

| Work | Ref |
|---|---|
| van Baarsen and Pu, EUROCRYPT 2024 | [code](https://github.com/sihangpu/fuzzy_PSI) \| [paper](https://eprint.iacr.org/2024/330) |
| Gao et al., ASIACRYPT 2024 | [code](https://github.com/ql70ql70/Fuzzy-Private-Set-Intersection-from-Fuzzy-Mapping) \| [paper](https://eprint.iacr.org/2024/1462) |
| Dang et al., CCS 2025 | [code](https://github.com/zhouxv/ourFuzzyPSI-C) \| [paper](https://eprint.iacr.org/2025/1796) |
| Bui et al., ASIACRYPT 2025 | [code](https://github.com/phuocchubeo123/SaPSI) \| [paper](https://eprint.iacr.org/2025/907.pdf) |

</details>

## Full reproduction

Run the complete parameter matrices (180 performance configurations plus smoke
checks):

```bash
./scripts/run_reproduction.sh --full
```

**Estimated runtime: 5–6 hours. Peak memory: approximately 200 GiB RSS.**
A host with **256 GiB RAM** is recommended.

### Reduced $n=2^{12}$ reproduction (optional)

Run both tables at $n=2^{12}$ (120 performance configurations plus smoke checks):

```bash
./scripts/run_reproduction.sh --light
```

**Estimated runtime: 2–3 hours. Peak memory: approximately 200 GiB RSS.**
A host with **256 GiB RAM** is still recommended: this mode reduces the
unique-cell workload, but leaves unique-block unchanged, so the overall memory
peak does not decrease.

Both time budgets are estimates based on measured per-configuration runtimes
on our AMD EPYC 9554 host, assuming `TRIALS=1` and excluding build time.
Peak memory is based on prior measurements. Slower hosts or additional trials
need more time.

## Claims

1. **[Claim 1: Protocol correctness](./claims/claim1/claim.md).** All implemented
   FPSI protocols correctly recover fuzzy intersections under
   the corresponding one-sided assumptions.
2. **[Claim 2: Unique-cell evaluation](./claims/claim2/claim.md).** The runtime
   and communication of the receiver-sided unique-cell $L_\infty$ protocols,
   in normal and prefix modes, are reproducible for the paper's parameter settings (Table 2).
3. **[Claim 3: Unique-block evaluation](./claims/claim3/claim.md).** The runtime
   and communication of the receiver-sided unique-block $L_\infty$, $L_1$, and
   $L_2$ protocols, in normal and prefix modes, are reproducible for the paper's
   parameter settings (Table 3). 

For a claim-by-claim evaluation roadmap, use [claims/README.md](./claims/README.md).

## Limitations and safety

- This is a research prototype, not production software or a security audit.
- Inputs are generated in memory by default; `-i` accepts equal-sized point files.
- Both parties run as threads in one process over local sockets.
- Network emulation is never enabled automatically. `scripts/throttle.sh`
  changes a host qdisc, requires `sudo`, and must be cleaned up with
  `./scripts/throttle.sh del [interface]`.
- Create public source archives with `./scripts/package_release.sh <version>`;
  its allowlist excludes builds, dependencies, results, downloaded projects,
  and private review correspondence.

## Acknowledgements

Parts of the prefix optimization are adapted from
[Dang et al.](https://github.com/zhouxv/ourFuzzyPSI-C). We thank Peter Rindal
for the open-source [secure-join](https://github.com/ladnir/secure-join) and
[volePSI](https://github.com/ladnir/volepsi) libraries.

## Citation

```bibtex
@inproceedings{yang2026efficient,
  title={Efficient Fuzzy PSI under One-Sided Assumptions},
  author={Yang, Xinpeng and Hao, Meng and Jia, Yanxue and Weng, Chenkai and Wen, Yonggang and Zhang, Tianwei},
  booktitle={Proceedings of the 2026 ACM SIGSAC Conference on Computer and Communications Security},
  year={2026}
}
```

Machine-readable citation metadata is in [CITATION.cff](./CITATION.cff).

## License

FPSI is released under the [MIT License](./LICENSE).
