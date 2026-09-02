#pragma once

#include "fpsi/tools/config.h"

// Public one-sided FPSI protocol entry points.
//
// Every function runs both parties locally over the sockets constructed by
// the implementation. Inputs, planted matches, trial count, metric, and
// reporting behavior are supplied through FpsiConfig. `L0` denotes the
// L-infinity metric; `Lp` accepts metric 1 or 2 in the current executable;
// `Px` denotes the prefix-optimized construction.

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
