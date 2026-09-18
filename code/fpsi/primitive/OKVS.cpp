#include "fpsi/primitive/OKVS.h"
#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Common/Timer.h>
#include <algorithm>
#include <stdexcept>
#include <thread>
#include <vector>

namespace {

constexpr u64 kMinItemsPerThread = 1ULL << 16;
constexpr u64 kMaxOkvsThreads = 16;
constexpr u64 kOkvsEncodeThreads = 1;

u64 resolveThreadCount(u64 requested, u64 itemCount)
{
    if (requested != 0) {
        return requested;
    }

    const u64 hardwareThreads = std::max(1u, std::thread::hardware_concurrency());
    const u64 workThreads = std::max<u64>(1, (itemCount + kMinItemsPerThread - 1) / kMinItemsPerThread);
    return std::min({ hardwareThreads, workThreads, kMaxOkvsThreads });
}

} // namespace

OKVS::OKVS(u64 numItems, u64 weight_, u64 ssp, u64 binSize_)
{
    // Public layout seed; private solve randomness is generated separately.
    paxos.init(numItems, binSize_, weight_, ssp, volePSI::PaxosParam::GF128, oc::ZeroBlock);
    param = paxos.mPaxosParam;
}

vector<block> OKVS::encode(const vector<block> &keys, const vector<block> &values)
{
    vector<block> encoding;
    encode(keys, values, encoding);
    return encoding;
}

void OKVS::encode(const vector<block> &keys, const vector<block> &values, vector<block> &encoding)
{
    if (keys.size() != values.size()) {
        throw std::invalid_argument("OKVS keys and values must have the same size");
    }

    encoding.resize(paxos.size());
    PRNG prng(sysRandomSeed());
    // Baxos shares this PRNG across solve workers, but PRNG is not thread-safe.
    paxos.solve<block>(keys, values, encoding, &prng, kOkvsEncodeThreads);
}

vector<block> OKVS::decode(const vector<block> &encoding, const vector<block> &keys, u64 numThreads)
{
    vector<block> values;
    decode(encoding, keys, values, numThreads);
    return values;
}

void OKVS::decode(const vector<block> &encoding, const vector<block> &keys, vector<block> &values, u64 numThreads)
{
    if (encoding.size() != paxos.size()) {
        throw std::invalid_argument("OKVS encoding has an unexpected size");
    }

    values.resize(keys.size());
    paxos.decode<block>(keys, values, encoding, resolveThreadCount(numThreads, keys.size()));
}

u64 OKVS::size()
{
    return paxos.size();
}
