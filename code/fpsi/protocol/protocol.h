#pragma once

#include "fpsi/tool/config.h"

// Local benchmarks: generate inputs, run both parties, and report trial means.
// L0 = L-infinity; Lp = L1/L2; Px = prefix optimization.
// Time starts at "local preprocess done": key/value construction is excluded,
// while per-trial query construction and OKVS encoding/decoding are included.
// Communication uses MiB (labeled MB).

// Unique-cell assumption, receiver-sided protocols.
void fuzzyPsiUniqueCellL0(const FpsiConfig &config);
void fuzzyPsiUniqueCellLp(const FpsiConfig &config);
void fuzzyPsiUniqueCellPxL0(const FpsiConfig &config);
void fuzzyPsiUniqueCellPxLp(const FpsiConfig &config);

// Unique-cell assumption, sender-sided protocols. Prefix optimization is
// currently implemented only for L-infinity.
void fuzzyPsiUniqueCellSenderL0(const FpsiConfig &config);
void fuzzyPsiUniqueCellSenderLp(const FpsiConfig &config);
void fuzzyPsiUniqueCellSenderPxL0(const FpsiConfig &config);

// Unique-block assumption, receiver-sided protocols. The augmented prefix Lp
// implementation is the entry point selected by the command-line dispatcher.
void fuzzyPsiUniqueBlockL0(const FpsiConfig &config);
void fuzzyPsiUniqueBlockLp(const FpsiConfig &config);
void fuzzyPsiUniqueBlockPxL0(const FpsiConfig &config);
void fuzzyPsiUniqueBlockPxLp(const FpsiConfig &config);
void fuzzyPsiUniqueBlockPxAugLp(const FpsiConfig &config);
