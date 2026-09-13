#include "fpsi/primitive/SoOPPRF.h"
#include <algorithm>
#include <stdexcept>
#include <thread>
#include "fpsi/primitive/SoOPRF.h"
#include "fpsi/tool/common.h"

namespace {

struct SoOpprfRoles {
    coproto::Socket *sendSocket;
    coproto::Socket *recvSocket;
    std::vector<oc::block> *sendOutput;
    std::vector<oc::block> *recvOutput;
};

// AltModPrf expands every input block into five bit-sliced matrices whose
// combined live size is about 256 bytes per item. Evaluating at most one GiB
// of raw blocks at a time bounds that temporary working set to about 16 GiB.
constexpr oc::u64 kPrfItemsPerBatch = kBlocksPerChunk;

void maskValuesInBatches(
    AltModPrf &prf,
    std::vector<oc::block> &keys,
    const std::vector<oc::block> &values,
    std::vector<oc::block> &maskedValues)
{
    if (keys.size() != values.size() || keys.size() != maskedValues.size()) {
        throw std::invalid_argument("OPPRF key/value count mismatch");
    }

    for (oc::u64 offset = 0; offset < keys.size(); offset += kPrfItemsPerBatch) {
        const oc::u64 batchSize =
            std::min<oc::u64>(keys.size() - offset, kPrfItemsPerBatch);
        oc::span<oc::block> keyBatch(keys.data() + offset, batchSize);
        oc::span<oc::block> maskedBatch(maskedValues.data() + offset, batchSize);
        prf.eval(keyBatch, maskedBatch);

        for (oc::u64 i = 0; i < batchSize; ++i) {
            maskedBatch[i] ^= values[offset + i];
        }
    }
}

SoOpprfRoles resolveRoles(
    std::vector<oc::block> &recvShares,
    std::vector<oc::block> &sendShares,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse)
{
    if (roleInverse) {
        return { &sockets[1], &sockets[0], &recvShares, &sendShares };
    }
    return { &sockets[0], &sockets[1], &sendShares, &recvShares };
}

} // namespace

SoOPPRFSender::SoOPPRFSender(uint64_t num_, uint64_t num_kv_, uint64_t numThreads_, bool useOle_, coproto::Socket *socket_)
    : SoOPRFSender(num_, numThreads_, useOle_, socket_)
{
    okvs = new OKVS(num_kv_);
}

SoOPPRFSender::~SoOPPRFSender()
{
    delete okvs;
}

void SoOPPRFSender::OPPRF(std::vector<oc::block> &keys, std::vector<oc::block> &values, std::vector<oc::block> &y0)
{
    auto before = socket->bytesReceived() + socket->bytesSent();

    SoOPRFSender::OPRF(y0);

    auto after = socket->bytesReceived() + socket->bytesSent();

    AltModPrf prf(SoOPRFSender::getKey());
    std::vector<block> values_masked(keys.size());
    maskValuesInBatches(prf, keys, values, values_masked);

    auto encoding = okvs->encode(keys, values_masked);

    if (LOG) {
        std::cout << "OPRF comm: " << (after - before) / 1024.0 / 1024.0 << " MB " << std::endl;

        std::cout << "OKVS size: " << encoding.size() * sizeof(block) / 1024.0 / 1024.0 << " MB " << std::endl;
    }

    sendBlocks(*socket, encoding);
}

void SoOPPRFSender::OPPRF(const std::vector<oc::block> &encoding, std::vector<oc::block> &y0)
{
    auto before = socket->bytesReceived() + socket->bytesSent();

    SoOPRFSender::OPRF(y0);

    auto after = socket->bytesReceived() + socket->bytesSent();

    if (LOG) {
        std::cout << "OPRF comm: " << (after - before) / 1024.0 / 1024.0 << " MB " << std::endl;
        std::cout << "OKVS size: " << encoding.size() * sizeof(block) / 1024.0 / 1024.0 << " MB " << std::endl;
    }

    sendBlocks(*socket, encoding);
}

SoOPPRFRecver::SoOPPRFRecver(uint64_t num_, uint64_t num_kv_, uint64_t numThreads_, bool useOle_, coproto::Socket *socket_)
    : SoOPRFRecver(num_, numThreads_, useOle_, socket_)
{
    okvs = new OKVS(num_kv_);
}

SoOPPRFRecver::~SoOPPRFRecver()
{
    delete okvs;
}

void SoOPPRFRecver::OPPRF(std::vector<oc::block> &keys, std::vector<oc::block> &y1)
{
    std::vector<oc::block> tmp(keys.size());

    SoOPRFRecver::OPRF(keys, tmp);

    std::vector<oc::block> encoding(okvs->size());

    recvBlocks(*socket, encoding);

    okvs->decode(encoding, keys, y1);

    for (u64 i = 0; i < keys.size(); i++) {
        y1[i] ^= tmp[i];
    }
}

void runSoOpprf(
    std::vector<oc::block> &keys,
    std::vector<oc::block> &values,
    std::vector<oc::block> &queryKeys,
    std::vector<oc::block> &recvShares,
    std::vector<oc::block> &sendShares,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse)
{
    auto roles = resolveRoles(recvShares, sendShares, sockets, roleInverse);

    std::thread sendParty([&] {
        SoOPPRFRecver recv(queryKeys.size(), keys.size(), 1, false, roles.recvSocket);
        recv.OPPRF(queryKeys, *roles.recvOutput);
    });

    std::thread recvParty([&] {
        SoOPPRFSender send(queryKeys.size(), keys.size(), 1, false, roles.sendSocket);
        send.OPPRF(keys, values, *roles.sendOutput);
    });

    sendParty.join();
    recvParty.join();
}

void runSoOpprf(
    const std::vector<oc::block> &encoding,
    oc::u64 numKeyValues,
    std::vector<oc::block> &queryKeys,
    std::vector<oc::block> &recvShares,
    std::vector<oc::block> &sendShares,
    std::array<coproto::AsioSocket, 2> &sockets,
    bool roleInverse)
{
    auto roles = resolveRoles(recvShares, sendShares, sockets, roleInverse);

    std::thread sendParty([&] {
        SoOPPRFRecver recv(queryKeys.size(), numKeyValues, 1, false, roles.recvSocket);
        recv.OPPRF(queryKeys, *roles.recvOutput);
    });

    std::thread recvParty([&] {
        SoOPPRFSender send(queryKeys.size(), numKeyValues, 1, false, roles.sendSocket);
        send.OPPRF(encoding, *roles.sendOutput);
    });

    sendParty.join();
    recvParty.join();
}
