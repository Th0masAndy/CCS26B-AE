#pragma once

#include <cryptoTools/Crypto/PRNG.h>
#include <vector>
#include "fpsi/tools/config.h"
#include "fpsi/tools/utils.h"

struct FpsiTestCase {
    PointSet sendSet;
    PointSet recvSet;
    std::vector<oc::u64> expectedOutputIndices;
    std::vector<oc::u64> receiverMatchIndices;
};

oc::PRNG makeDataPrng();

FpsiTestCase generateFpsiTestCase(
    const FpsiConfig &config,
    oc::PRNG &prng);
