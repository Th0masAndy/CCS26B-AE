#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
RESULT_DIR=${FPSI_RESULT_DIR:-"$ROOT_DIR/artifact-results/claim3"}
RAW_LOG="$RESULT_DIR/unique-block.txt"
REPETITIONS=${REPETITIONS:-1}
export REPETITIONS VERIFY=1

if [[ ! -x "$ROOT_DIR/code/build/fpsi" ]]; then
    echo "error: FPSI is not built; run ./scripts/build.sh first" >&2
    exit 2
fi

mkdir -p "$RESULT_DIR"
"$ROOT_DIR/scripts/collect_environment.sh" > "$RESULT_DIR/environment.txt"
"$ROOT_DIR/scripts/bench_unique_block.sh" | tee "$RAW_LOG"

expected_runs=$((90 * REPETITIONS))
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
echo "✅ Claim 3 complete: $result_rows verified run(s)"
