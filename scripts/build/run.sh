#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
THIRDPARTY_DIR="$ROOT_DIR/code/thirdparty"
INSTALL_DIR="$THIRDPARTY_DIR/out/install"
BUILD_DIR="$ROOT_DIR/code/build"
source "$ROOT_DIR/scripts/build/toolchain.sh"

default_jobs()
{
    local cpu_jobs memory_kib memory_jobs jobs
    cpu_jobs=$(nproc)
    memory_kib=$(awk '/^MemTotal:/ { print $2 }' /proc/meminfo)
    memory_jobs=$((memory_kib / 2097152))
    ((memory_jobs < 1)) && memory_jobs=1
    jobs=$cpu_jobs
    ((jobs > memory_jobs)) && jobs=$memory_jobs
    ((jobs > 16)) && jobs=16
    echo "$jobs"
}

JOBS=${JOBS:-$(default_jobs)}

SECURE_JOIN_COMMIT=df62f360df0c2dfb8288f8f7b99ccf3472318e87
VOLEPSI_COMMIT=59e06bca81a3287257522cd261bad71e37780642
BLAKE3_COMMIT=c7f0d216e6fc834b742456b39546c9835baa1277
LIBOTE_COMMIT=d21bc4d7aae941e276b92615252fd1760c902890

"$ROOT_DIR/scripts/build/preflight.sh" --build
echo
echo "🔨 Building FPSI with $JOBS parallel job(s)"
echo "   Override with JOBS=<count>."

install_system_packages()
{
    if [[ ${FPSI_SKIP_SYSTEM_PACKAGES:-0} == 1 ]]; then
        echo "  ↪ System package installation skipped"
        return
    fi

    local packages=(
        build-essential cmake git libtool iproute2 python3 sudo nasm
        libssl-dev libgmp-dev wget libfmt-dev time
    )

    if [[ $EUID -eq 0 ]]; then
        apt-get update
        apt-get install -y "${packages[@]}"
    else
        sudo apt-get update
        sudo apt-get install -y "${packages[@]}"
    fi
}

clone_at_commit()
{
    local url=$1
    local commit=$2
    local destination=$3

    if [[ -e "$destination" && ! -d "$destination/.git" ]]; then
        echo "  ✗ Incomplete dependency directory: $destination" >&2
        echo "    Remove that directory and rerun this script." >&2
        return 1
    fi
    if [[ ! -d "$destination/.git" ]]; then
        git clone --no-checkout "$url" "$destination"
    fi
    git -C "$destination" fetch --depth 1 origin "$commit"
    git -C "$destination" checkout --detach "$commit"
}

build_secure_join()
{
    if [[ -f "$INSTALL_DIR/lib/libsecureJoin.a" ]]; then
        echo "  ✓ secure-join already installed"
        return
    fi

    local source_dir="$THIRDPARTY_DIR/secure-join"
    clone_at_commit https://github.com/Visa-Research/secure-join.git "$SECURE_JOIN_COMMIT" "$source_dir"
    sed -i "s|657f6da90bff5774a2d01c824e997572d5e8ba00|$LIBOTE_COMMIT|" "$source_dir/thirdparty/getLibOTe.cmake"

    pushd "$source_dir" >/dev/null
    python3 build.py --install="$INSTALL_DIR" --par="$JOBS" \
        "${CMAKE_TOOLCHAIN_ARGS[@]}" \
        -DSECUREJOIN_ENABLE_BOOST=ON \
        -DSODIUM_MONTGOMERY=false \
        -DENABLE_BITPOLYMUL=false
    popd >/dev/null
}

build_volepsi()
{
    if [[ -f "$INSTALL_DIR/lib/libvolePSI.a" ]]; then
        echo "  ✓ volePSI already installed"
        return
    fi

    local source_dir="$THIRDPARTY_DIR/volepsi"
    clone_at_commit https://github.com/ladnir/volepsi.git "$VOLEPSI_COMMIT" "$source_dir"
    sed -i "s|36cd7242e085eddba34feaa63733ec4c6ded66c7|$LIBOTE_COMMIT|g" "$source_dir/thirdparty/getLibOTe.cmake"

    pushd "$source_dir" >/dev/null
    python3 build.py --install="$INSTALL_DIR" --par="$JOBS" \
        "${CMAKE_TOOLCHAIN_ARGS[@]}" \
        -DVOLE_PSI_ENABLE_BOOST=true \
        -DVOLE_PSI_ENABLE_BITPOLYMUL=false \
        -DVOLE_PSI_SODIUM_MONTGOMERY=false \
        -DCMAKE_PREFIX_PATH=/usr/local/
    cp out/build/linux/volePSI/config.h "$INSTALL_DIR/include/volePSI/"
    popd >/dev/null
}

build_blake3()
{
    if [[ -f "$INSTALL_DIR/lib/libblake3.a" ]]; then
        echo "  ✓ BLAKE3 already installed"
        return
    fi

    local source_dir="$THIRDPARTY_DIR/BLAKE3"
    clone_at_commit https://github.com/BLAKE3-team/BLAKE3.git "$BLAKE3_COMMIT" "$source_dir"
    cmake -S "$source_dir/c" -B "$source_dir/c/build" \
        "${CMAKE_TOOLCHAIN_ARGS[@]}" -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR"
    cmake --build "$source_dir/c/build" --target install -j "$JOBS"
}

install_system_packages
select_toolchain
check_toolchain_caches "$BUILD_DIR" "$THIRDPARTY_DIR"
CMAKE_TOOLCHAIN_ARGS=("-DCMAKE_C_COMPILER=$CC" "-DCMAKE_CXX_COMPILER=$CXX")
echo "   C compiler: $CC"
echo "   C++ compiler: $CXX"
mkdir -p "$THIRDPARTY_DIR"
build_secure_join
build_volepsi
build_blake3

cmake -S "$ROOT_DIR/code" -B "$BUILD_DIR" \
    "${CMAKE_TOOLCHAIN_ARGS[@]}" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" -j "$JOBS"

echo
echo "✅ Build complete: $BUILD_DIR/fpsi"
