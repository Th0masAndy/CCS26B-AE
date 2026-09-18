#pragma once

#include <coproto/Socket/AsioSocket.h>
#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Common/block.h>
#include <cstdint>
#include "secure-join/Prf/AltModPrfProto.h"

using namespace secJoin;

// Paired OPRF calls return XOR shares: y0 ^ y1 = PRF_key(x), in input order.
// Agree on num/useOle, size x/y0/y1 to num, and run both roles concurrently.
// Adapters borrow connected sockets and own internal state; do not copy them.
// Benchmark setup retains a fixed PRF key and synthetic key-OT material.
class SoOPRFSender {
public:
    SoOPRFSender(uint64_t num_, uint64_t numThreads_, bool useOle_, coproto::Socket *socket_);
    ~SoOPRFSender();

    // Compatibility no-op; initialization is handled by the adapter.
    void setup();
    void OPRF(std::vector<oc::block> &y0);

    AltModPrf::KeyType getKey()
    {
        return sender->getKey();
    }

    uint64_t num;
    uint64_t numThreads;
    bool useOle;
    coproto::Socket *socket;
    PRNG *prng;

private:
    AltModWPrfSender *sender;
    macoro::thread_pool *pool;
    CorGenerator *ole;
};

class SoOPRFRecver {
public:
    SoOPRFRecver(uint64_t num_, uint64_t numThreads_, bool useOle_, coproto::Socket *socket_);
    ~SoOPRFRecver();

    void setup();
    void OPRF(std::vector<oc::block> &x, std::vector<oc::block> &y1);

    uint64_t num;
    uint64_t numThreads;
    bool useOle;
    coproto::Socket *socket;
    PRNG *prng;

private:
    AltModWPrfReceiver *recver;
    macoro::thread_pool *pool;
    CorGenerator *ole;
};
