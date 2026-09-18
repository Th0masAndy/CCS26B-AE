#pragma once

#include <array>
#include <coproto/Socket/AsioSocket.h>

#include <cryptoTools/Common/BitVector.h>
#include <libOTe/TwoChooseOne/Silent/SilentOtExtReceiver.h>
#include <libOTe/TwoChooseOne/Silent/SilentOtExtSender.h>
#include <vector>
#include <volePSI/Defines.h>

using namespace volePSI;
using namespace osuCrypto;

extern bool LOG;

// Returns XOR-shared equality bits for the low 40 + ceil(log2(input.size())) bits.
// Both parties call concurrently with complementary idx values (0/1); out is resized.
void ssPEQT(u32 idx, std::vector<block> &input, BitVector &out, Socket &chl, u32 numThreads);

// Mux gates shared values by ssPEQT equality; block shares use XOR, u64 shares add modulo 2^64.
// Paired adapters borrow connected sockets, run concurrently, and must not be copied.
// Size per-item inputs/results to num; grouped EqSel/EqConstant use the contracts below.
class MuxSender {
public:
    MuxSender(uint64_t num_, coproto::Socket *socket_);
    ~MuxSender();
    BitVector Mux(std::vector<block> &u0, std::vector<block> &v0, std::vector<block> &res0);
    BitVector EqRand(std::vector<block> &u0, std::vector<block> &v0, std::vector<block> &res0);

    BitVector Mux(std::vector<block> &u0, std::vector<u64> &v0, std::vector<u64> &res0);

    void EqSel(std::vector<block> &u0, std::vector<block> &v0, std::vector<block> &res0, u64 len);

    void EqConstant(
        std::vector<block> &u0,
        std::vector<block> &v0,
        std::vector<block> &res0,
        u64 len,
        block constant);

    void EqSel(std::vector<block> &u0, std::vector<u64> &v0, std::vector<u64> &res0, u64 len);

    void EqSel(std::vector<block> &u0, std::vector<block> &res0, u64 len);

    BitVector CmpRand(std::vector<u64> &u0, std::vector<block> &v0, std::vector<block> &res0, u64 threshold);

    uint64_t num;

private:
    coproto::Socket *socket;
    osuCrypto::SilentOtExtSender *sender;
    osuCrypto::SilentOtExtReceiver *recver;
    osuCrypto::PRNG *prng;
};

class MuxRecver {
public:
    MuxRecver(uint64_t num_, coproto::Socket *socket_);
    ~MuxRecver();
    BitVector Mux(std::vector<block> &u1, std::vector<block> &v1, std::vector<block> &res1);
    BitVector EqRand(std::vector<block> &u1, std::vector<block> &v1, std::vector<block> &res1);
    BitVector Mux(std::vector<block> &u1, std::vector<u64> &v1, std::vector<u64> &res1);

    void EqSel(std::vector<block> &u1, std::vector<block> &v1, std::vector<block> &res1, u64 len);

    void EqConstant(
        std::vector<block> &u1,
        std::vector<block> &v1,
        std::vector<block> &res1,
        u64 len,
        block constant);
    void EqSel(std::vector<block> &u1, std::vector<u64> &v1, std::vector<u64> &res1, u64 len);

    void EqSel(std::vector<block> &u0, std::vector<block> &res0, u64 len);

    BitVector CmpRand(std::vector<u64> &u1, std::vector<block> &v1, std::vector<block> &res1);

    uint64_t num;

private:
    coproto::Socket *socket;
    osuCrypto::SilentOtExtSender *sender;
    osuCrypto::SilentOtExtReceiver *recver;
    osuCrypto::PRNG *prng;
};

// Helpers run both parties locally; roleInverse swaps sockets, not buffer pairing.
// Reveals sendValues ^ recvValues on selector equality, random blocks otherwise.
// All four input vectors must have the same size; equality uses ssPEQT's truncated labels.
std::vector<block> runEqRandReveal(
    std::vector<block> &sendSelectors,
    std::vector<block> &recvSelectors,
    std::vector<block> &sendValues,
    std::vector<block> &recvValues,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse = false);

// Reveals sendValues ^ recvValues when (sendInputs + recvInputs) mod 2^64 < threshold,
// random blocks otherwise. All four input vectors must have the same size.
std::vector<block> runCmpRandReveal(
    std::vector<u64> &sendInputs,
    std::vector<u64> &recvInputs,
    std::vector<block> &sendValues,
    std::vector<block> &recvValues,
    u64 threshold,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse = false);

// Grouped helpers require len > 0, equal input sizes divisible by len, and at most
// one matching selector per group. Pre-size outputs to input.size()/len and zero them.
// EqSel returns shares of the selected value, or a random value when no selector matches.
void runEqSel(
    std::vector<block> &sendSelectors,
    std::vector<block> &recvSelectors,
    std::vector<block> &sendValues,
    std::vector<block> &recvValues,
    std::vector<block> &sendResults,
    std::vector<block> &recvResults,
    u64 len,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse = false);

// Same grouping as EqSel, but reconstructs constant when no selector matches.
void runEqConstant(
    std::vector<block> &sendSelectors,
    std::vector<block> &recvSelectors,
    std::vector<block> &sendValues,
    std::vector<block> &recvValues,
    std::vector<block> &sendResults,
    std::vector<block> &recvResults,
    u64 len,
    block constant,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse = false);

// Selector-only overload: shares reconstruct to zero on a match, random otherwise.
void runEqSel(
    std::vector<block> &sendSelectors,
    std::vector<block> &recvSelectors,
    std::vector<block> &sendResults,
    std::vector<block> &recvResults,
    u64 len,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse = false);

void runEqSel(
    std::vector<block> &sendSelectors,
    std::vector<block> &recvSelectors,
    std::vector<u64> &sendValues,
    std::vector<u64> &recvValues,
    std::vector<u64> &sendResults,
    std::vector<u64> &recvResults,
    u64 len,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse = false);
