#pragma once
#include <array>
#include <coproto/Socket/AsioSocket.h>
#include <coproto/Socket/Socket.h>
#include <cryptoTools/Common/block.h>
#include <cryptoTools/Crypto/PRNG.h>
#include <cstdint>
#include <libOTe/TwoChooseOne/Silent/SilentOtExtReceiver.h>
#include <libOTe/TwoChooseOne/Silent/SilentOtExtSender.h>
#include <sys/types.h>
#include <vector>

extern bool LOG;

// Converts the low 64 bits of XOR-shared blocks to additive shares modulo 2^64.
// Paired calls borrow connected sockets and run concurrently; size blk/val to num
// and zero val before use. Adapters own internal state and must not be copied.
class B2aSender {
public:
    B2aSender(uint64_t num_, coproto::Socket *socket_);
    ~B2aSender();
    void b2a(std::vector<oc::block> &blk, std::vector<oc::u64> &val);

    uint64_t num;

private:
    coproto::Socket *socket;
    osuCrypto::SilentOtExtSender *sender;
    osuCrypto::PRNG *prng;
};

class B2aRecver {
public:
    B2aRecver(uint64_t num_, coproto::Socket *socket_);
    ~B2aRecver();
    void b2a(std::vector<oc::block> &blk, std::vector<oc::u64> &val);

    uint64_t num;

private:
    coproto::Socket *socket;
    osuCrypto::SilentOtExtReceiver *receiver;
    osuCrypto::PRNG *prng;
};

// Runs both parties locally; output shares add to low(sendShares ^ recvShares).
// Use equally sized inputs and zero-initialized outputs; outputs are accumulated.
// roleInverse swaps sockets, not input/output pairing.
void runB2a(
    std::vector<oc::block> &sendShares,
    std::vector<oc::block> &recvShares,
    std::vector<oc::u64> &sendArithShares,
    std::vector<oc::u64> &recvArithShares,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse = false);
