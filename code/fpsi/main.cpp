#include <coproto/Socket/AsioSocket.h>
#include <iostream>
#include <string_view>
#include "fpsi/tools/common.h"
#include "cryptoTools/Common/CLP.h"
#include "fpsi/protocol/protocol.h"

bool LOG = false;

namespace {

void printHelp(const char *program)
{
    std::cout
        << "usage: " << program << " [options]\n\n"
        << "options:\n"
        << "  -p <0|1|2>         metric: 0 = linf (default), 1 = l1, 2 = l2\n"
        << "  -assumption <0|1>  assumption: 0 = unique cell (default), 1 = unique block\n"
        << "  -prefix            enable prefix optimization; delta must be a power of two\n"
        << "  -sender            use the sender-sided protocol\n"
        << "  -n <integer>       input set size\n"
        << "  -nn <integer>      log2 input set size (default: 10)\n"
        << "  -d <integer>       dimension (default: 2)\n"
        << "  -delta <integer>   distance threshold (default: 2)\n"
        << "  -inter <integer>   planted intersection size\n"
        << "  -try <integer>     number of benchmark runs (default: 1)\n"
        << "  -v <0|1>           verbose output (default: 0)\n"
        << "  -h, --help         show this help and exit\n";
}

bool helpRequested(int argc, char **argv)
{
    for (int i = 1; i < argc; ++i) {
        const std::string_view arg(argv[i]);
        if (arg == "-h" || arg == "--help" || arg == "-help") {
            return true;
        }
    }
    return false;
}

void runOneSidedSender(const FpsiConfig &config, int assumption, bool prefix)
{
    if (assumption != 0) {
        return;
    }

    if (prefix) {
        if (config.metric == 0) {
            fuzzyPsiUniqueCellSenderPxL0(config);
        }
        return;
    }

    if (config.metric == 0) {
        fuzzyPsiUniqueCellSenderL0(config);
    } else {
        fuzzyPsiUniqueCellSenderLp(config);
    }
}

void runOneSidedReceiver(
    const FpsiConfig &config,
    int assumption,
    bool prefix)
{
    if (assumption == 0) {
        if (config.metric == 0) {
            prefix ? fuzzyPsiUniqueCellPxL0(config) : fuzzyPsiUniqueCellL0(config);
        } else {
            if (prefix) {
                fuzzyPsiUniqueCellPxLp(config);
            } else {
                fuzzyPsiUniqueCellLp(config);
            }
        }
        return;
    }

    if (assumption == 1) {
        if (config.metric == 0) {
            prefix ? fuzzyPsiUniqueBlockPxL0(config) : fuzzyPsiUniqueBlockL0(config);
        } else {
            prefix ? fuzzyPsiUniqueBlockPxAugLp(config) : fuzzyPsiUniqueBlockLp(config);
        }
    }
}

} // namespace

int main(int argc, char **argv)
{
    if (helpRequested(argc, argv)) {
        printHelp(argv[0]);
        return 0;
    }

    oc::CLP cmd(argc, argv);
    const auto config = FpsiConfig::fromCommandLine(cmd);

    // Protocol parameters:
    //   p          : 0 = L_infinity, non-zero = L_p
    //   sender     : use the sender-sided protocol
    //   assumption : 0 = unique cell (2delta), 1 = unique block (4delta)
    //   prefix     : enable prefix optimization
    const int assumption = cmd.getOr("assumption", 0);
    const bool prefix = cmd.isSet("prefix");
    const bool sender = cmd.isSet("sender");
    LOG = config.verbose;

    if (prefix && !isPowerOfTwo(config.delta)) {
        std::cerr << "error: '-delta' must be a power of two when '-prefix' is enabled\n";
        return 2;
    }

    if (sender) {
        runOneSidedSender(config, assumption, prefix);
    } else {
        runOneSidedReceiver(config, assumption, prefix);
    }

    return 0;
}
