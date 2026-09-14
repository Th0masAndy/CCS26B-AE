#!/usr/bin/env bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/toolchain.sh"

BUILD_MODE=0
[[ ${1:-} == --build ]] && BUILD_MODE=1

failures=0
warnings=0

pass()
{
    echo "  ✓ $*"
}

fail()
{
    echo "  ✗ $*" >&2
    failures=$((failures + 1))
}

warn()
{
    echo "  ⚠ $*" >&2
    warnings=$((warnings + 1))
}

echo "🔎 FPSI environment preflight"
echo

os=$(uname -s)
arch=$(uname -m)
[[ $os == Linux ]] && pass "operating system is Linux" || fail "Linux is required (found $os)"
[[ $arch == x86_64 || $arch == amd64 ]] \
    && pass "architecture is AMD64 ($arch)" \
    || fail "AMD64/x86_64 is required (found $arch)"

cpu_flags=$(awk -F: '/^flags[[:space:]]*:/ { print $2; exit }' /proc/cpuinfo 2>/dev/null || true)
for feature in aes pclmulqdq sse2 sse4_1; do
    if [[ " $cpu_flags " == *" $feature "* ]]; then
        pass "CPU feature $feature"
    else
        fail "CPU feature $feature is unavailable"
    fi
done

memory_kib=$(awk '/^MemTotal:/ { print $2 }' /proc/meminfo)
memory_gib=$((memory_kib / 1024 / 1024))
if ((memory_gib >= 16)); then
    pass "installed memory is ${memory_gib} GiB"
else
    warn "installed memory is ${memory_gib} GiB; build and smoke evaluation recommend 16 GiB"
fi

available_kib=$(df -Pk "${TMPDIR:-/tmp}" | awk 'NR == 2 { print $4 }')
available_gib=$((available_kib / 1024 / 1024))
if ((available_gib >= 10)); then
    pass "temporary filesystem has ${available_gib} GiB free"
else
    warn "temporary filesystem has only ${available_gib} GiB free"
fi

for tool in cmake git python3; do
    if command -v "$tool" >/dev/null 2>&1; then
        pass "$tool is available"
    elif ((BUILD_MODE)); then
        warn "$tool is not installed yet; scripts/build/run.sh will install system packages"
    else
        warn "$tool is unavailable"
    fi
done

for compiler in "$FPSI_CC" "$FPSI_CXX"; do
    if command -v "$compiler" >/dev/null 2>&1; then
        if version=$(compiler_version "$compiler"); then
            pass "$compiler $version meets the GCC 11+ requirement"
        else
            fail "Unsupported compiler: $compiler"
        fi
    elif ((BUILD_MODE)) && [[ ${FPSI_SKIP_SYSTEM_PACKAGES:-0} != 1 ]] \
        && [[ $compiler == gcc || $compiler == g++ ]]; then
        warn "$compiler is not installed yet; scripts/build/run.sh will install it"
    else
        fail "$compiler is unavailable; install build-essential or the selected GCC/G++ 11+ pair"
    fi
done

if ((failures)); then
    echo
    echo "❌ Preflight failed: $failures required check(s), $warnings warning(s)" >&2
    exit 1
fi

echo
echo "✅ Preflight passed with $warnings warning(s)"
