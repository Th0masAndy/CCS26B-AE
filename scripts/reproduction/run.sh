#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
MODE=${1:---quick}
TRIALS=${TRIALS:-1}
export TRIALS

usage()
{
    echo "usage: $0 [--quick|--partial|--mini|--full|--light]" >&2
    echo "  --light retains the legacy all-n=2^12 matrix, including high-memory cases." >&2
}

if (( $# > 1 )); then
    usage
    exit 2
fi
case "$MODE" in
    --quick|--partial|--mini|--full|--light) ;;
    *) usage; exit 2 ;;
esac

if [[ ! $TRIALS =~ ^[1-9][0-9]*$ ]] || (( ${#TRIALS} > 10 )) || (( TRIALS > 2147483647 )); then
    echo "error: TRIALS must be an integer between 1 and 2147483647" >&2
    exit 2
fi

default_result_dir="$ROOT_DIR/artifact-results"
if [[ $MODE == --partial || $MODE == --mini ]]; then
    default_result_dir="$default_result_dir/${MODE#--}"
fi
RESULT_DIR=${FPSI_RESULT_DIR:-"$default_result_dir"}
mkdir -p "$RESULT_DIR"
if [[ $MODE == --mini ]]; then
    echo "🔬 FPSI mini benchmark (not a paper-parameter reproduction)"
else
    echo "🔬 FPSI ${MODE#--} reproduction"
fi
echo "   Results: $RESULT_DIR"
echo
"$ROOT_DIR/scripts/reproduction/collect_environment.sh" > "$RESULT_DIR/environment.txt"

summarize()
{
    "$ROOT_DIR/scripts/reproduction/summarize_results.py" "$@" --trials "$TRIALS" \
        --markdown "$RESULT_DIR/summary.md"
    echo "📊 Summary: $RESULT_DIR/summary.md"
}

check_results()
{
    local log=$1 expected=$2 result_rows correct_rows
    result_rows=$(grep -Ec '^\[(normal|prefix)\]' "$log" || true)
    correct_rows=$(grep -Fxc "Total 16/16 matches found!" "$log" || true)
    if (( result_rows != expected || correct_rows != expected * TRIALS )); then
        echo "error: expected $expected result rows and $((expected * TRIALS)) correctness markers in $log; got $result_rows and $correct_rows" >&2
        return 1
    fi
}

case "$MODE" in
    --quick)
        "$ROOT_DIR/scripts/reproduction/smoke.sh" | tee "$RESULT_DIR/quick.txt"
        summarize "$RESULT_DIR/quick.txt"
        echo "📄 Raw log: $RESULT_DIR/quick.txt"
        echo "✅ Quick reproduction complete"
        ;;
    --full)
        rm -f "$RESULT_DIR/smoke.txt"
        FPSI_NS="8 12 16" FPSI_DIMS="2 4 6" "$ROOT_DIR/scripts/reproduction/benchmark.sh" unique-cell | tee "$RESULT_DIR/unique-cell.txt"
        FPSI_NS="12" FPSI_DIMS="2 4 6" "$ROOT_DIR/scripts/reproduction/benchmark.sh" unique-block | tee "$RESULT_DIR/unique-block.txt"
        summarize "$RESULT_DIR/unique-cell.txt" "$RESULT_DIR/unique-block.txt"
        echo "✅ Full reproduction complete: $RESULT_DIR"
        ;;
    --light)
        rm -f "$RESULT_DIR/smoke.txt"
        FPSI_NS="12" FPSI_DIMS="2 4 6" "$ROOT_DIR/scripts/reproduction/benchmark.sh" unique-cell | tee "$RESULT_DIR/unique-cell.txt"
        FPSI_NS="12" FPSI_DIMS="2 4 6" "$ROOT_DIR/scripts/reproduction/benchmark.sh" unique-block | tee "$RESULT_DIR/unique-block.txt"
        summarize "$RESULT_DIR/unique-cell.txt" "$RESULT_DIR/unique-block.txt"
        echo "✅ Light reproduction complete: $RESULT_DIR"
        ;;
    --partial|--mini)
        nn=12
        [[ $MODE == --mini ]] && nn=10
        rm -f "$RESULT_DIR/smoke.txt"
        FPSI_NS="$nn" FPSI_DIMS="2 4" VERIFY=1 "$ROOT_DIR/scripts/reproduction/benchmark.sh" unique-cell | tee "$RESULT_DIR/unique-cell.txt"
        check_results "$RESULT_DIR/unique-cell.txt" 20
        FPSI_NS="$nn" FPSI_DIMS="2 4" VERIFY=1 "$ROOT_DIR/scripts/reproduction/benchmark.sh" unique-block | tee "$RESULT_DIR/unique-block.txt"
        check_results "$RESULT_DIR/unique-block.txt" 60
        summarize "$RESULT_DIR/unique-cell.txt" "$RESULT_DIR/unique-block.txt"
        if [[ $MODE == --mini ]]; then
            echo "✅ Mini benchmark complete: $RESULT_DIR"
        else
            echo "✅ Partial reproduction complete: $RESULT_DIR"
        fi
        ;;
esac
