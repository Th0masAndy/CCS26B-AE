#pragma once

#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Network/IOService.h>
#include <cstring>
#include <map>
#include <vector>
#include "volePSI/Paxos.h"
using namespace oc;
using namespace osuCrypto;
using namespace std;

// Encodes numItems distinct block key/value pairs; decode preserves query order.
// Use identical constructor parameters for encoding/decoding; outputs are resized.
// Unknown keys produce unspecified values, not a non-membership flag.
class OKVS {
public:
    OKVS(u64 numItems, u64 weight_ = 3, u64 ssp = 40, u64 binSize_ = 1 << 14);

    vector<block> encode(const vector<block> &keys, const vector<block> &values);

    void encode(const vector<block> &keys, const vector<block> &values, vector<block> &encoding);

    // numThreads == 0 selects a bounded automatic worker count.
    vector<block> decode(const vector<block> &encoding, const vector<block> &keys, u64 numThreads = 0);

    void decode(const vector<block> &encoding, const vector<block> &keys, vector<block> &values, u64 numThreads = 0);

    // Encoded size in blocks, not bytes.
    u64 size();

private:
    volePSI::Baxos paxos;
    volePSI::PaxosParam param;
};
