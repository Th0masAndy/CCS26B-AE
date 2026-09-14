#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
PROFILE=${1:-}
TRIALS=${TRIALS:-1}
VERIFY=${VERIFY:-1}
deltas=(32 64 128 256 512)

usage()
{
    echo "usage: $0 {unique-cell|unique-block}" >&2
}

if (( $# != 1 )); then
    usage
    exit 2
fi

case "$PROFILE" in
    unique-cell)
        assumption=0
        assumption_name=uniqueCell
        default_ns="8 12 16"
        metrics=(0)
        ;;
    unique-block)
        assumption=1
        assumption_name=uniqueBlock
        default_ns="12"
        metrics=(0 1 2)
        ;;
    *)
        usage
        exit 2
        ;;
esac

read -r -a ns <<< "${FPSI_NS:-$default_ns}"
read -r -a dims <<< "${FPSI_DIMS:-2 4 6}"

if [[ ! $TRIALS =~ ^[1-9][0-9]*$ ]] || (( ${#TRIALS} > 10 )) || (( TRIALS > 2147483647 )); then
    echo "error: TRIALS must be an integer between 1 and 2147483647" >&2
    exit 2
fi

run_fpsi()
{
    "$ROOT_DIR/code/build/fpsi" "$@" -inter 16 -try "$TRIALS" -v "$VERIFY"
}

printf "[ProType]  [Assumption]   [Metric] [Dim] [Delta] [Size] [Com.(MB)] [Time(s)]\n"

for mode in normal prefix; do
    prefix_options=()
    [[ $mode == prefix ]] && prefix_options=(-prefix)
    echo "▶ $assumption_name / receiver / $mode"
    for metric in "${metrics[@]}"; do
        for nn in "${ns[@]}"; do
            for dim in "${dims[@]}"; do
                for delta in "${deltas[@]}"; do
                    run_fpsi -assumption "$assumption" "${prefix_options[@]}" \
                        -p "$metric" -nn "$nn" -d "$dim" -delta "$delta"
                done
                echo
            done
        done
    done
done
