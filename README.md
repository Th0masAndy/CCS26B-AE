# Efficient Fuzzy PSI under One-Sided Assumptions

FPSI is a research prototype for fuzzy private set intersection under
one-sided assumptions. It implements the unique-cell and unique-block protocol
families for $L_\infty$, $L_1$, and $L_2$ distances.


## 🖥️ Platform requirements

- **Reference platform:** Ubuntu 24.04 on x86_64.
- **Compiler requirement:** GCC 11 or newer with C++20 support.
- **Memory requirement:** 256 GiB for full reproduction, 64 GiB for partial reproduction, and 32 GiB for the mini benchmark.
- **Required CPU instructions:** AES, PCLMUL, SSE2, and SSE4.1.
- **Unsupported platforms:** ARM64 and Apple Silicon, including AMD64 emulation.

## 🚀 Quick start

1. **Check the environment**

   Run the read-only preflight check. It verifies the operating system,
   architecture, CPU instructions, compiler, memory, disk space, and basic tools.

   ```bash
   ./scripts/build/preflight.sh
   ```


2. **Build FPSI**

   The build script installs the required Ubuntu packages, fetches pinned
   dependencies into `code/thirdparty/`, and creates `code/build/fpsi`. This step
   requires root or `sudo`; set `FPSI_SKIP_SYSTEM_PACKAGES=1` when the packages are
   already installed.

   ```bash
   ./scripts/build/run.sh
   ```

3. **Run the quick validation**

   Run a quick correctness check and save the results to `artifact-results/`.

   ```bash
   ./scripts/reproduction/run.sh --quick
   ```


Expected time on an 8-core machine:

| Step | Typical time | Success indicator |
|---|---:|---|
| Environment preflight | below 1 minute | `✅ Preflight passed` |
| Fresh build | 10–20 minutes | `✅ Build complete: .../code/build/fpsi` |
| Quick reproduction | below 2 minutes | `✅ [smoke] PASS: 6 protocol cases and 1 parameter guard` |

The quick workflow writes raw output and a Markdown summary to
`artifact-results/`:

```text
artifact-results/
├── quick.txt
└── summary.md
```

The build and smoke test need at least 16 GiB RAM. The full unique-cell evaluation
peaks at 62.8 GiB, while unique-block normal mode peaks at 198.5 GiB at $n=2^{12}$.
Use a dedicated 256 GiB host for the complete evaluation.

### 🐳 Docker build (Recommended)

Docker is the recommended way to build and run the artifact in a consistent environment:

```bash
docker build -f code/Dockerfile -t fpsi-ae .
docker run --rm fpsi-ae ./scripts/reproduction/run.sh --quick
```

## 🗂️ Input data

By default, the program uses randomly generated simulation data.

To use file-based inputs, pass `-i <directory>`. The program reads
`sender_data.txt` and `recver_data.txt` from that directory and writes matching
sender points to `output.txt` in the same directory:

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

## 🛠️ Troubleshooting

| Symptom | Resolution |
|---|---|
| `Illegal instruction` | Run `scripts/build/preflight.sh`; the host is usually ARM64 or is missing a required x86 instruction. |
| Compiler process is killed | Lower parallelism, for example `JOBS=4 ./scripts/build/run.sh`, and check available memory. |
| Compiler is missing or older than GCC 11 | Install `build-essential`, or select a matching pair with `CC` and `CXX`. |
| `Compiler mismatch` | Move `code/build` and `code/thirdparty` aside, then rebuild; do not reuse libraries built with another toolchain. |
| Incomplete dependency directory | Remove only the dependency directory named by `scripts/build/run.sh`, then rerun it. |
| Runtime differs from the paper | Repeat the case and compare trends and communication rather than exact runtimes. |

If a build was interrupted, do not pre-create `code/thirdparty/` contents manually.
The build script is resumable and reports the exact incomplete directory when
manual cleanup is necessary.

## ⚙️ Command-line Flags

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

`scripts/build/run.sh` pins both secure-join and volePSI to the same libOTe
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

## 📊 Full reproduction

After the Quick start, choose an evaluation option based on your platform's available resources:

| Option | Purpose | Cases | Recommended RAM |
|---|---|---:|---:|
| `--full` | Reproduce all paper parameters in Tables 2 and 3 | 180 | 256 GiB |
| `--partial` | Reproduce the paper subset at $n=2^{12}$, $d=2,4$ | 80 | 64 GiB |
| `--mini` | Try a small benchmark at $n=2^{10}$, $d=2,4$ | 80 | 32 GiB |

Full reproduction runs 180 benchmark cases:

- **Unique cell (90 cases):** normal and prefix mode, $L_\infty$,
  $n\in\{2^8,2^{12},2^{16}\}$, $d\in\{2,4,6\}$, and
  $\delta\in\{32,64,128,256,512\}$
- **Unique block (90 cases):** normal and prefix mode, $L_\infty$, $L_1$, and
  $L_2$, $n=2^{12}$, $d\in\{2,4,6\}$, and
  $\delta\in\{32,64,128,256,512\}$

```bash
./scripts/reproduction/run.sh --full
```

**Estimated runtime: 5–6 hours. Peak memory: approximately 200 GiB RSS.**
A host with **256 GiB RAM** is recommended.

### Partial reproduction (optional)

Reproduce a subset of Tables 2 and 3 at their original set size:
$n=2^{12}$ and $d=2,4$. Keep all five thresholds, both normal and prefix
modes, and the metrics used in each table (80 benchmark cases).

```bash
./scripts/reproduction/run.sh --partial
```

**Estimated runtime: 25–35 minutes. Peak memory: approximately 35 GiB RSS.**
A host with **64 GiB RAM** is recommended.
Results are saved to `artifact-results/partial/`.

### Mini benchmark (optional)

Run the same 80-case subset with $n=2^{10}$ instead. This is a smaller
performance benchmark, **not a reproduction of
the paper's set sizes**; its results should not be compared directly with
the paper's reported times.

```bash
./scripts/reproduction/run.sh --mini
```

**Estimated runtime: 6–10 minutes. Peak memory: approximately 21 GiB RSS.**
A host with **32 GiB RAM** is recommended.
Results are saved to `artifact-results/mini/`.

All modes save raw logs and Markdown summaries.
Time budgets are estimates for the AMD EPYC 9554 reference host with
`TRIALS=1`, excluding build time. Partial memory is based on a measured
$n=2^{12},d=4,\delta=512$ unique-block normal case (33.5 GiB); mini memory
is the maximum of the corresponding 80 cases in the earlier $n=2^{10}$
resource sweep (20.4 GiB). Slower hosts or additional trials need more time;
leave memory headroom for the OS and allocator variation.

## Claims

1. **[Claim 1: Protocol correctness](./claims/claim1/claim.md).** The implemented
   protocols correctly compute fuzzy private set intersection by outputting all
   sender elements that are close to the receiver set.
2. **[Claim 2: Unique-cell evaluation](./claims/claim2/claim.md).** The runtime
   and communication of the receiver-sided unique-cell $L_\infty$ protocols,
   in normal and prefix modes, are reproducible for the paper's parameter settings (Table 2).
3. **[Claim 3: Unique-block evaluation](./claims/claim3/claim.md).** The runtime
   and communication of the receiver-sided unique-block $L_\infty$, $L_1$, and
   $L_2$ protocols, in normal and prefix modes, are reproducible for the paper's
   parameter settings (Table 3). 

For a claim-by-claim evaluation roadmap, use [claims/README.md](./claims/README.md).

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
