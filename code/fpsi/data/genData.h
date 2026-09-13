#pragma once

#include <cryptoTools/Crypto/PRNG.h>
#include <vector>
#include "fpsi/tool/config.h"
#include "fpsi/tool/utils.h"

struct FpsiTestCase {
    PointSet sendSet;
    PointSet recvSet;
    // Sender indices, paired position-wise with receiverMatchIndices.
    std::vector<oc::u64> expectedOutputIndices;
    std::vector<oc::u64> receiverMatchIndices;
};

// Fixed-seed data generation only; not a source of private protocol coins.
oc::PRNG makeDataPrng();

// Plants matches without validating one-sided assumptions or extra matches.
FpsiTestCase generateFpsiTestCase(
    const FpsiConfig &config,
    oc::PRNG &prng);
