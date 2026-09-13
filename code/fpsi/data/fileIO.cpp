#include "fpsi/data/fileIO.h"
#include <algorithm>
#include <charconv>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unistd.h>

namespace {

PointSet readPoints(const std::filesystem::path &path)
{
    std::ifstream input(path);
    if (!input) {
        throw std::runtime_error("cannot open input file: " + path.string());
    }

    PointSet points;
    std::set<std::vector<oc::u64>> distinct;
    std::string line;
    std::size_t lineNumber = 0;
    while (std::getline(input, line)) {
        ++lineNumber;
        std::istringstream row(line);
        std::vector<oc::u64> point;
        std::string token;
        while (row >> token) {
            oc::u64 coordinate = 0;
            const auto [end, error] = std::from_chars(
                token.data(), token.data() + token.size(), coordinate);
            if (error != std::errc {} || end != token.data() + token.size()) {
                throw std::invalid_argument(path.string() + ":" + std::to_string(lineNumber)
                    + ": expected an unsigned 64-bit decimal coordinate");
            }
            point.push_back(coordinate);
        }
        if (point.empty()) {
            continue;
        }
        if (!points.empty() && point.size() != points.dim()) {
            throw std::invalid_argument(path.string() + ":" + std::to_string(lineNumber)
                + ": inconsistent point dimension");
        }
        if (!distinct.insert(point).second) {
            throw std::invalid_argument(path.string() + ":" + std::to_string(lineNumber)
                + ": duplicate point");
        }
        points.push_back(point);
    }
    if (input.bad()) {
        throw std::runtime_error("failed to read input file: " + path.string());
    }
    return points;
}

bool withinThreshold(
    std::span<const oc::u64> senderPoint,
    std::span<const oc::u64> receiverPoint,
    const FpsiConfig &config)
{
    const auto delta = static_cast<oc::u64>(config.delta);
    oc::u64 remaining = config.metric == 2 ? delta * delta : delta;
    for (std::size_t axis = 0; axis < senderPoint.size(); ++axis) {
        const auto difference = senderPoint[axis] >= receiverPoint[axis]
            ? senderPoint[axis] - receiverPoint[axis]
            : receiverPoint[axis] - senderPoint[axis];
        if (difference > delta) {
            return false;
        }
        if (config.metric != 0) {
            const auto contribution = config.metric == 2 ? difference * difference : difference;
            if (contribution > remaining) {
                return false;
            }
            remaining -= contribution;
        }
    }
    return true;
}

void validateAssumption(const FpsiTestCase &input, int delta, int assumption, bool sender)
{
    const auto &constrained = sender ? input.sendSet : input.recvSet;
    std::set<std::vector<oc::u64>> occupied;
    for (oc::u64 index = 0; index < constrained.size(); ++index) {
        if (assumption == 0) {
            if (!occupied.insert(cell(constrained[index], 2 * static_cast<oc::u64>(delta))).second) {
                throw std::invalid_argument(std::string(sender ? "sender" : "receiver")
                    + " input violates unique-cell: multiple points in one 2*delta cell");
            }
        } else {
            const auto neighbors = neigh(constrained[index], delta);
            for (oc::u64 neighbor = 0; neighbor < neighbors.size(); ++neighbor) {
                const auto cellId = neighbors[neighbor];
                if (!occupied.emplace(cellId.begin(), cellId.end()).second) {
                    throw std::invalid_argument(
                        "receiver input violates the unique-block encoding requirement: "
                        "delta-neighborhoods occupy overlapping 2*delta cells");
                }
            }
        }
    }
}

} // namespace

FpsiFileInput loadFpsiInput(
    const std::filesystem::path &directory,
    FpsiConfig &config,
    int assumption,
    bool sender)
{
    if (config.metric < 0 || config.metric > 2 || assumption < 0 || assumption > 1) {
        throw std::invalid_argument("file input requires -p 0, 1, or 2 and -assumption 0 or 1");
    }
    if (sender && assumption != 0) {
        throw std::invalid_argument("sender-sided unique-block is not implemented");
    }
    if (config.delta <= 0 || config.delta > std::numeric_limits<int>::max() / 4) {
        throw std::invalid_argument("file input requires 0 < delta <= INT_MAX/4");
    }
    if (config.trials <= 0) {
        throw std::invalid_argument("file input requires a positive -try value");
    }

    FpsiFileInput result;
    result.testCase.sendSet = readPoints(directory / "sender_data.txt");
    result.testCase.recvSet = readPoints(directory / "recver_data.txt");
    auto &input = result.testCase;
    if (input.sendSet.size() != input.recvSet.size()) {
        throw std::invalid_argument("sender_data.txt and recver_data.txt must contain the same number of points");
    }
    if (input.sendSet.dim() != input.recvSet.dim()) {
        throw std::invalid_argument("sender_data.txt and recver_data.txt must have the same dimension");
    }
    config.n = input.sendSet.size();
    config.dimension = input.sendSet.dim();
    config.intersectionSize = 0;
    if (config.dimension >= 64) {
        throw std::invalid_argument("file input dimension must be below 64");
    }
    if (config.n != 0) {
        const auto neighborCount = oc::u64 { 1 } << config.dimension;
        const auto capacity = static_cast<oc::u64>(std::numeric_limits<std::uint32_t>::max());
        if (config.n > capacity / neighborCount / config.dimension
                / (2 * static_cast<oc::u64>(config.delta) + 1)) {
            throw std::invalid_argument("file input exceeds the protocol's 32-bit encoding capacity");
        }
    }

    result.coordinateOffsets.resize(config.dimension, 0);
    const auto delta = static_cast<oc::u64>(config.delta);
    for (std::size_t axis = 0; axis < config.dimension; ++axis) {
        oc::u64 minimum = std::numeric_limits<oc::u64>::max();
        oc::u64 maximum = 0;
        for (const auto *points : { &input.sendSet, &input.recvSet }) {
            for (oc::u64 index = 0; index < points->size(); ++index) {
                minimum = std::min(minimum, (*points)[index][axis]);
                maximum = std::max(maximum, (*points)[index][axis]);
            }
        }
        // A 4*delta translation preserves distances and both cell/block grids.
        const auto offset = minimum < delta ? 4 * delta : 0;
        if (maximum > std::numeric_limits<oc::u64>::max() - delta - offset) {
            throw std::invalid_argument("coordinate range is too wide for safe threshold arithmetic");
        }
        result.coordinateOffsets[axis] = offset;
        if (offset != 0) {
            for (auto *points : { &input.sendSet, &input.recvSet }) {
                for (oc::u64 index = 0; index < points->size(); ++index) {
                    (*points)[index][axis] += offset;
                }
            }
        }
    }
    validateAssumption(input, config.delta, assumption, sender);

    // File-mode verification uses an independent plaintext oracle, not planted matches.
    if (config.verbose) {
        for (oc::u64 senderIndex = 0; senderIndex < config.n; ++senderIndex) {
            for (oc::u64 receiverIndex = 0; receiverIndex < config.n; ++receiverIndex) {
                if (withinThreshold(input.sendSet[senderIndex], input.recvSet[receiverIndex], config)) {
                    input.expectedOutputIndices.push_back(senderIndex);
                    break;
                }
            }
        }
    }
    return result;
}

void captureFpsiOutput(
    const FpsiConfig &config,
    const std::vector<std::vector<oc::block>> &elements)
{
    PointSet points(0, config.dimension);
    points.reserve(elements.size());
    for (const auto &element : elements) {
        if (element.size() != (config.dimension + 1) / 2) {
            throw std::runtime_error("recovered point dimension mismatch");
        }
        std::vector<oc::u64> point(config.dimension);
        for (std::size_t axis = 0; axis < config.dimension; ++axis) {
            // transferElements packs the first coordinate in the high word.
            point[axis] = axis % 2 == 0 ? high(element[axis / 2]) : low(element[axis / 2]);
        }
        points.push_back(point);
    }
    *config.output = std::move(points);
}

void writeFpsiOutput(
    const std::filesystem::path &directory,
    const PointSet &points,
    const std::vector<oc::u64> &coordinateOffsets)
{
    if (points.dim() != coordinateOffsets.size()) {
        throw std::runtime_error("output dimension mismatch");
    }
    std::vector<std::vector<oc::u64>> rows;
    rows.reserve(points.size());
    for (oc::u64 index = 0; index < points.size(); ++index) {
        std::vector<oc::u64> row(points[index].begin(), points[index].end());
        for (std::size_t axis = 0; axis < row.size(); ++axis) {
            if (row[axis] < coordinateOffsets[axis]) {
                throw std::runtime_error("invalid recovered coordinate");
            }
            row[axis] -= coordinateOffsets[axis];
        }
        rows.push_back(std::move(row));
    }
    std::sort(rows.begin(), rows.end());
    rows.erase(std::unique(rows.begin(), rows.end()), rows.end());

    // Replace output only after a complete write; do not follow an existing symlink.
    auto temporary = (directory / ".output.txt.XXXXXX").string();
    const int descriptor = mkstemp(temporary.data());
    if (descriptor < 0) {
        throw std::runtime_error("cannot create output file in: " + directory.string());
    }
    std::FILE *output = fdopen(descriptor, "w");
    if (output == nullptr) {
        close(descriptor);
        std::filesystem::remove(temporary);
        throw std::runtime_error("cannot open temporary output file");
    }
    try {
        for (const auto &row : rows) {
            for (std::size_t axis = 0; axis < row.size(); ++axis) {
                if (std::fprintf(output, "%s%llu", axis == 0 ? "" : " ",
                        static_cast<unsigned long long>(row[axis])) < 0) {
                    throw std::runtime_error("failed to write output points");
                }
            }
            if (std::fputc('\n', output) == EOF) {
                throw std::runtime_error("failed to write output points");
            }
        }
        const int closed = std::fclose(output);
        output = nullptr;
        if (closed != 0) {
            throw std::runtime_error("failed to flush output points");
        }
        std::filesystem::rename(temporary, directory / "output.txt");
    } catch (...) {
        if (output != nullptr) {
            std::fclose(output);
        }
        std::error_code ignored;
        std::filesystem::remove(temporary, ignored);
        throw;
    }
}
