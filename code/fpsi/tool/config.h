#pragma once

#include <cryptoTools/Common/CLP.h>
#include <cryptoTools/Common/Defines.h>
#include <cstddef>

struct FpsiTestCase;
class PointSet;

struct FpsiConfig {
    oc::u64 n;
    std::size_t dimension;
    int delta;
    // 0 = L-infinity (not L0 norm), 1 = L1, 2 = L2.
    int metric;
    oc::u64 intersectionSize;
    // Reuse generated inputs; report one averaged row for all trials.
    int trials;
    bool verbose;

    // Optional caller-owned file input and recovered output; null for benchmarks.
    const FpsiTestCase *input = nullptr;
    PointSet *output = nullptr;

    static FpsiConfig fromCommandLine(const oc::CLP &cmd);
};
