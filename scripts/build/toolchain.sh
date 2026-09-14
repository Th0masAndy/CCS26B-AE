#!/usr/bin/env bash

FPSI_CC=${CC:-gcc}
FPSI_CXX=${CXX:-g++}

compiler_version()
{
    local compiler=$1 version macros
    if ! version=$("$compiler" -dumpfullversion -dumpversion 2>/dev/null); then
        echo "Cannot run $compiler; install a matching GCC/G++ pair (version 11 or newer)." >&2
        return 1
    fi
    if [[ ! $version =~ ^[0-9]+(\.[0-9]+)*$ ]] || (( ${version%%.*} < 11 )); then
        echo "GCC 11 or newer is required: $compiler reports $version." >&2
        return 1
    fi
    if ! macros=$("$compiler" -dM -E -x c - </dev/null 2>/dev/null) \
        || [[ $macros != *"#define __GNUC__ "* || $macros == *"#define __clang__ "* ]]; then
        echo "A GNU compiler is required: $compiler is not GCC." >&2
        return 1
    fi
    echo "$version"
}

select_toolchain()
{
    local cc_version cxx_version
    cc_version=$(compiler_version "$FPSI_CC") || return 1
    cxx_version=$(compiler_version "$FPSI_CXX") || return 1
    if [[ ${cc_version%%.*} != ${cxx_version%%.*} ]]; then
        echo "CC and CXX must use the same GCC major version: $cc_version vs $cxx_version." >&2
        return 1
    fi
    CC=$(readlink -f -- "$(command -v "$FPSI_CC")")
    CXX=$(readlink -f -- "$(command -v "$FPSI_CXX")")
    export CC CXX
}

toolchain_mismatch()
{
    echo "Compiler mismatch in $1: $2" >&2
    echo "Move code/build and code/thirdparty aside, then rerun scripts/build/run.sh to rebuild with the selected compiler." >&2
    return 1
}

check_toolchain_caches()
{
    local directory cache language cached expected compiler_info compiler_id version expected_version cc_version cxx_version
    cc_version=$(compiler_version "$CC") || return 1
    cxx_version=$(compiler_version "$CXX") || return 1
    for directory in "$@"; do
        [[ -d $directory ]] || continue
        while IFS= read -r -d '' cache; do
            for language in C CXX; do
                cached=$(awk -F= -v key="CMAKE_${language}_COMPILER" \
                    '$1 ~ "^" key ":" { print substr($0, index($0, "=") + 1); exit }' "$cache")
                [[ -n $cached ]] || continue
                expected=$CC
                expected_version=$cc_version
                if [[ $language == CXX ]]; then
                    expected=$CXX
                    expected_version=$cxx_version
                fi
                if [[ $cached != */* ]]; then
                    cached=$(command -v "$cached" || true)
                fi
                if [[ $(readlink -f -- "$cached" 2>/dev/null) != "$expected" ]]; then
                    toolchain_mismatch "$cache" "CMAKE_${language}_COMPILER=$cached; expected $expected"
                    return 1
                fi
                for compiler_info in "${cache%/*}"/CMakeFiles/*/"CMake${language}Compiler.cmake"; do
                    [[ -f $compiler_info ]] || continue
                    compiler_id=$(awk -F'"' -v key="set(CMAKE_${language}_COMPILER_ID " \
                        '$1 == key { print $2; exit }' "$compiler_info")
                    version=$(awk -F'"' -v key="set(CMAKE_${language}_COMPILER_VERSION " \
                        '$1 == key { print $2; exit }' "$compiler_info")
                    if [[ $compiler_id != GNU || ${version%%.*} != "${expected_version%%.*}" ]]; then
                        toolchain_mismatch "$compiler_info" "recorded $compiler_id $version; expected GNU ${expected_version%%.*}"
                        return 1
                    fi
                done
            done
        done < <(find "$directory" -type f -name CMakeCache.txt -print0)
    done
}
