#pragma once

#include <array>
#include <coproto/Socket/AsioSocket.h>
#include <cstdint>
#include <vector>
#include "fpsi/primitive/OKVS.h"
#include "fpsi/primitive/SoOPRF.h"

extern bool LOG;

// Programmed keys must be distinct; queryKeys determines output-share order.
struct SoOpprfInput {
    std::vector<oc::block> keys;
    std::vector<oc::block> values;
    std::vector<oc::block> queryKeys;
};

class SoOPPRFSender : public SoOPRFSender {
public:
    SoOPPRFSender(uint64_t num_, uint64_t num_kv_, uint64_t numThreads_, bool useOle_, coproto::Socket *socket_);
    ~SoOPPRFSender();

    void OPPRF(std::vector<oc::block> &keys, std::vector<oc::block> &values, std::vector<oc::block> &y0);

    void OPPRF(const std::vector<oc::block> &encoding, std::vector<oc::block> &y0);

    task<> run_oprf(std::vector<oc::block> &y0);

private:
    OKVS *okvs;
};

class SoOPPRFRecver : public SoOPRFRecver {
public:
    SoOPPRFRecver(uint64_t num_, uint64_t num_kv_, uint64_t numThreads_, bool useOle_, coproto::Socket *socket_);
    ~SoOPPRFRecver();

    void OPPRF(std::vector<oc::block> &keys, std::vector<oc::block> &y1);

private:
    OKVS *okvs;
};

// Matched queries reconstruct values via sendShares ^ recvShares; misses are unflagged.
// Size outputs to queryKeys.size(); sendShares/recvShares stay on sockets[0]/[1].
// roleInverse swaps the programming/query roles, not those buffer associations.
void runSoOpprf(
    std::vector<oc::block> &keys,
    std::vector<oc::block> &values,
    std::vector<oc::block> &queryKeys,
    std::vector<oc::block> &recvShares,
    std::vector<oc::block> &sendShares,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse = false);

// encoding must use PRF-masked values, the same SoOPRF key, and numKeyValues.
void runSoOpprf(
    const std::vector<oc::block> &encoding,
    oc::u64 numKeyValues,
    std::vector<oc::block> &queryKeys,
    std::vector<oc::block> &recvShares,
    std::vector<oc::block> &sendShares,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse = false);
