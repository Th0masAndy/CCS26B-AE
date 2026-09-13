#pragma once

#include <filesystem>
#include "fpsi/data/genData.h"

struct FpsiFileInput {
    FpsiTestCase testCase;
    std::vector<oc::u64> coordinateOffsets;
};

FpsiFileInput loadFpsiInput(
    const std::filesystem::path &directory,
    FpsiConfig &config,
    int assumption,
    bool sender);

void captureFpsiOutput(
    const FpsiConfig &config,
    const std::vector<std::vector<oc::block>> &elements);

void writeFpsiOutput(
    const std::filesystem::path &directory,
    const PointSet &points,
    const std::vector<oc::u64> &coordinateOffsets);
