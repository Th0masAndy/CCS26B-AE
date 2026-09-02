#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

echo "FPSI artifact evaluation environment"
echo "recorded_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "kernel=$(uname -srmo)"
if git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "revision=$(git -C "$ROOT_DIR" rev-parse HEAD)"
else
    echo "revision=unavailable"
fi
echo

echo "[CPU]"
if command -v lscpu >/dev/null 2>&1; then
    lscpu | grep -E '^(Architecture|Model name|CPU\(s\)|Thread|Core|Socket|Flags):' || true
else
    echo "lscpu unavailable"
fi
echo

echo "[Memory]"
if command -v free >/dev/null 2>&1; then
    free -h
else
    grep -E '^(MemTotal|MemAvailable):' /proc/meminfo || true
fi
echo

echo "[Storage]"
df -h "$ROOT_DIR"
echo

echo "[Toolchain]"
command -v g++ >/dev/null 2>&1 && g++ --version | sed -n '1p' || echo "g++ unavailable"
command -v cmake >/dev/null 2>&1 && cmake --version | sed -n '1p' || echo "cmake unavailable"
command -v python3 >/dev/null 2>&1 && python3 --version || echo "python3 unavailable"
