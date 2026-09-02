#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
MODE=${1:---quick}
RESULT_DIR=${FPSI_RESULT_DIR:-"$ROOT_DIR/artifact-results"}

mkdir -p "$RESULT_DIR"
echo "🔬 FPSI ${MODE#--} reproduction"
echo "   Results: $RESULT_DIR"
echo
"$ROOT_DIR/scripts/collect_environment.sh" > "$RESULT_DIR/environment.txt"

summarize()
{
    "$ROOT_DIR/scripts/summarize_results.py" "$@" \
        --csv "$RESULT_DIR/summary.csv" \
        --markdown "$RESULT_DIR/summary.md"
    echo "📊 Summary: $RESULT_DIR/summary.md"
}

case "$MODE" in
    --quick)
        "$ROOT_DIR/scripts/run_smoke.sh" | tee "$RESULT_DIR/quick.txt"
        summarize "$RESULT_DIR/quick.txt"
        echo "📄 Raw log: $RESULT_DIR/quick.txt"
        echo "✅ Quick reproduction complete"
        ;;
    --full)
        "$ROOT_DIR/scripts/run_smoke.sh" | tee "$RESULT_DIR/smoke.txt"
        FPSI_NS="8 12 16" "$ROOT_DIR/scripts/bench_unique_cell.sh" | tee "$RESULT_DIR/unique-cell.txt"
        "$ROOT_DIR/scripts/bench_unique_block.sh" | tee "$RESULT_DIR/unique-block.txt"
        summarize "$RESULT_DIR/unique-cell.txt" "$RESULT_DIR/unique-block.txt"
        echo "✅ Full reproduction complete: $RESULT_DIR"
        ;;
    --light)
        "$ROOT_DIR/scripts/run_smoke.sh" | tee "$RESULT_DIR/smoke.txt"
        FPSI_NS="12" "$ROOT_DIR/scripts/bench_unique_cell.sh" | tee "$RESULT_DIR/unique-cell.txt"
        "$ROOT_DIR/scripts/bench_unique_block.sh" | tee "$RESULT_DIR/unique-block.txt"
        summarize "$RESULT_DIR/unique-cell.txt" "$RESULT_DIR/unique-block.txt"
        echo "✅ Light reproduction complete: $RESULT_DIR"
        ;;
    *)
        echo "usage: $0 [--quick|--light|--full]" >&2
        exit 2
        ;;
esac
