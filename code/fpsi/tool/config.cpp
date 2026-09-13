#include "fpsi/tool/config.h"
#include <bit>

FpsiConfig FpsiConfig::fromCommandLine(const oc::CLP &cmd)
{
    const oc::u64 inputSize = cmd.isSet("i") ? 0 : cmd.getOr("n", 1ull << cmd.getOr("nn", 10));
    const oc::u64 defaultIntersectionSize = inputSize == 0 ? 0 : std::bit_width(inputSize) - 1;

    return {
        .n = inputSize,
        .dimension = cmd.isSet("i") ? 0 : cmd.getOr("d", std::size_t { 2 }),
        .delta = cmd.getOr("delta", 2),
        .metric = cmd.getOr("p", 0),
        .intersectionSize = cmd.isSet("i") ? 0 : cmd.getOr("inter", defaultIntersectionSize),
        .trials = cmd.getOr("try", 1),
        .verbose = cmd.getOr("v", 0) != 0,
    };
}
