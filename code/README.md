# FPSI implementation guide

This directory is the self-contained implementation root. It contains the source
code, build definition, downloaded dependencies, and generated build output.
`CMakeLists.txt` builds the executable as `code/build/fpsi`. `Dockerfile` and
`Dockerfile.dockerignore` define the optional container build from the repository
root context.

## Directory layout

```text
fpsi/
├── main.cpp    # command-line entry point
├── tool/       # shared configuration, parameters, and utilities
├── data/       # synthetic data generation and point-file I/O
├── primitive/  # reusable 2PC, OKVS, and shared-output OPRF/OPPRF
└── protocol/   # FPSI protocol implementations
```

Each module keeps its declarations and implementations together. For example,
`fpsi/primitive/eq.h` and `fpsi/primitive/eq.cpp` live in the same directory.

Automated checks live in `../scripts/` and are registered with CTest in
`CMakeLists.txt`.

## Public entry points

- `fpsi/protocol/protocol.h` declares every supported protocol entry point.
- `fpsi/tool/config.h` defines the common `FpsiConfig` input.
- `fpsi/main.cpp` parses command-line options and dispatches by assumption,
  direction, prefix mode, and metric.
- `fpsi/protocol/uniqueCell.cpp` implements receiver- and sender-sided unique-cell
  protocols.
- `fpsi/protocol/uniqueBlock.cpp` implements receiver-sided unique-block protocols.

`L0` in function names means $L_\infty$; `Lp` covers $L_1$ and $L_2$; `Px`
marks prefix-optimized constructions.

## Reusable protocol stages

| Module | Responsibility |
|---|---|
| `primitive/SoOPPRF.cpp`, `primitive/SoOPRF.cpp` | shared-output programmable PRF interfaces |
| `primitive/OKVS.cpp` | OKVS encoding and decoding wrapper |
| `primitive/eq.cpp` | equality and interval tests |
| `primitive/mux.cpp` | conditioned selection and reveal operations |
| `primitive/b2a.cpp` | Boolean-to-arithmetic share conversion |
| `primitive/mul.cpp` | arithmetic-share multiplication |
| `primitive/cmp.cpp` | comparison and Millionaire-protocol components |

## Data, configuration, and reporting

| Module | Responsibility |
|---|---|
| `tool/config.cpp` | common command-line configuration |
| `data/genData.cpp` | synthetic point sets and planted fuzzy matches |
| `data/fileIO.cpp` | point-file parsing, input validation, optional reference checks, and recovered-point output |
| `tool/common.cpp` | communication, chunking, correctness, and result formatting |
| `fpsi/tool/param.h` | protocol constants and parameter helpers |

To add a protocol combination, declare its entry point in `fpsi/protocol/protocol.h`,
implement it in the assumption-specific source file, and add the dispatch rule
to `fpsi/main.cpp`. After any change, run
`ctest --test-dir code/build --output-on-failure` from the repository root.
