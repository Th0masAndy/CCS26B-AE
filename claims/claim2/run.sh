#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
MODE=${1:---full}

if (( $# > 1 )); then
    echo "usage: $0 [--full|--light]" >&2
    exit 2
fi

case "$MODE" in
    --full)
        FPSI_NS="8 12 16"
        expected_configurations=90
        default_result_dir="$ROOT_DIR/artifact-results/claim2"
        ;;
    --light)
        FPSI_NS="12"
        expected_configurations=30
        default_result_dir="$ROOT_DIR/artifact-results/claim2-light"
        ;;
    *)
        echo "usage: $0 [--full|--light]" >&2
        exit 2
        ;;
esac

RESULT_DIR=${FPSI_RESULT_DIR:-"$default_result_dir"}
RAW_LOG="$RESULT_DIR/unique-cell.txt"
REPETITIONS=${REPETITIONS:-1}
export FPSI_NS REPETITIONS VERIFY=1

if [[ ! -x "$ROOT_DIR/code/build/fpsi" ]]; then
    echo "error: FPSI is not built; run ./scripts/build.sh first" >&2
    exit 2
fi

mkdir -p "$RESULT_DIR"
"$ROOT_DIR/scripts/collect_environment.sh" > "$RESULT_DIR/environment.txt"
"$ROOT_DIR/scripts/bench_unique_cell.sh" | tee "$RAW_LOG"

expected_runs=$((expected_configurations * REPETITIONS))
result_rows=$(grep -Ec '^\[(normal|prefix)\]' "$RAW_LOG")
correct_rows=$(grep -Ec '^Total 4/4 matches found!$' "$RAW_LOG")
if ((result_rows != expected_runs || correct_rows != expected_runs)); then
    echo "error: expected $expected_runs results and correctness markers; got $result_rows and $correct_rows" >&2
    exit 1
fi

"$ROOT_DIR/scripts/summarize_results.py" "$RAW_LOG" \
    --csv "$RESULT_DIR/summary.csv" \
    --markdown "$RESULT_DIR/summary.md"

echo "📊 Summary: $RESULT_DIR/summary.md"
echo "✅ Claim 2 ${MODE#--} complete: $result_rows verified run(s)"
