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
├── tools/      # shared configuration, parameters, and utilities
├── data/       # synthetic benchmark data generation
├── mpc/        # reusable MPC components
│   └── opprf/  # OKVS and shared-output OPRF/OPPRF
├── protocol/   # FPSI entry points and composed filter stages
└── testing/    # legacy test helpers
```

Each module keeps its declarations and implementations together. For example,
`fpsi/mpc/eq.h` and `fpsi/mpc/eq.cpp` live in the same directory.

## Public entry points

- `fpsi/protocol/protocol.h` declares every supported protocol entry point.
- `fpsi/tools/config.h` defines the common `FpsiConfig` input.
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
| `protocol/filter.cpp` | composition of soOPPRF, equality, interval, conversion, multiplication, and selection stages |
| `mpc/opprf/SoOPPRF.cpp`, `mpc/opprf/SoOPRF.cpp` | shared-output programmable PRF interfaces |
| `mpc/opprf/OKVS.cpp` | OKVS encoding and decoding wrapper |
| `mpc/eq.cpp` | equality and interval tests |
| `mpc/mux.cpp` | conditioned selection and reveal operations |
| `mpc/b2a.cpp` | Boolean-to-arithmetic share conversion |
| `mpc/mul.cpp` | arithmetic-share multiplication |
| `mpc/cmp.cpp` | comparison and Millionaire-protocol components |

## Data, configuration, and reporting

| Module | Responsibility |
|---|---|
| `tools/config.cpp` | common command-line configuration |
| `data/genData.cpp` | synthetic point sets and planted fuzzy matches |
| `tools/common.cpp` | communication, chunking, correctness, and result formatting |
| `fpsi/tools/param.h` | protocol constants and parameter helpers |

To add a protocol combination, declare its entry point in `fpsi/protocol/protocol.h`,
implement it in the assumption-specific source file, and add the dispatch rule
to `fpsi/main.cpp`. After any change, run
`ctest --test-dir code/build --output-on-failure` from the repository root.
