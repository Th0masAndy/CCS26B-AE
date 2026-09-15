#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
if (( $# > 1 )) || [[ ${1:---full} != --full ]]; then
    echo "usage: $0 [--full]" >&2
    echo "For partial reproduction or the mini benchmark, use ./scripts/reproduction/run.sh." >&2
    exit 2
fi

RESULT_DIR=${FPSI_RESULT_DIR:-"$ROOT_DIR/artifact-results/claim3"}
RAW_LOG="$RESULT_DIR/unique-block.txt"
TRIALS=${TRIALS:-1}
export FPSI_NS="12" FPSI_DIMS="2 4 6" TRIALS VERIFY=1

if [[ ! $TRIALS =~ ^[1-9][0-9]*$ ]] || (( ${#TRIALS} > 10 )) || (( TRIALS > 2147483647 )); then
    echo "error: TRIALS must be an integer between 1 and 2147483647" >&2
    exit 2
fi

if [[ ! -x "$ROOT_DIR/code/build/fpsi" ]]; then
    echo "error: FPSI is not built; run ./scripts/build/run.sh first" >&2
    exit 2
fi

mkdir -p "$RESULT_DIR"
"$ROOT_DIR/scripts/reproduction/benchmark.sh" unique-block | tee "$RAW_LOG"

expected_checks=$((90 * TRIALS))
result_rows=$(grep -Ec '^\[(normal|prefix)\]' "$RAW_LOG" || true)
correct_rows=$(grep -Fxc "Total 16/16 matches found!" "$RAW_LOG" || true)
if ((result_rows != 90 || correct_rows != expected_checks)); then
    echo "error: expected 90 result rows and $expected_checks correctness markers; got $result_rows and $correct_rows" >&2
    exit 1
fi

"$ROOT_DIR/scripts/reproduction/summarize_results.py" "$RAW_LOG" --trials "$TRIALS" \
    --markdown "$RESULT_DIR/summary.md"

python3 "$ROOT_DIR/scripts/reproduction/compare_paper_results.py" \
    --reference "$ROOT_DIR/claims/claim3/paper-results.csv" \
    --results "$RAW_LOG" --trials "$TRIALS" \
    --output-dir "$RESULT_DIR"

echo "📊 Summary: $RESULT_DIR/summary.md"
echo "✅ Claim 3 complete: $result_rows configuration(s)"
