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
        comparison_options=()
        default_result_dir="$ROOT_DIR/artifact-results/claim2"
        ;;
    --light)
        FPSI_NS="12"
        expected_configurations=30
        comparison_options=(--size 4096)
        default_result_dir="$ROOT_DIR/artifact-results/claim2-light"
        ;;
    *)
        echo "usage: $0 [--full|--light]" >&2
        exit 2
        ;;
esac

RESULT_DIR=${FPSI_RESULT_DIR:-"$default_result_dir"}
RAW_LOG="$RESULT_DIR/unique-cell.txt"
TRIALS=${TRIALS:-1}
export FPSI_NS TRIALS VERIFY=1

if [[ ! $TRIALS =~ ^[1-9][0-9]*$ ]] || (( ${#TRIALS} > 10 )) || (( TRIALS > 2147483647 )); then
    echo "error: TRIALS must be an integer between 1 and 2147483647" >&2
    exit 2
fi

if [[ ! -x "$ROOT_DIR/code/build/fpsi" ]]; then
    echo "error: FPSI is not built; run ./scripts/build.sh first" >&2
    exit 2
fi

mkdir -p "$RESULT_DIR"
"$ROOT_DIR/scripts/collect_environment.sh" > "$RESULT_DIR/environment.txt"
"$ROOT_DIR/scripts/bench_unique_cell.sh" | tee "$RAW_LOG"

expected_checks=$((expected_configurations * TRIALS))
result_rows=$(grep -Ec '^\[(normal|prefix)\]' "$RAW_LOG" || true)
correct_rows=$(grep -Ec '^Total 4/4 matches found!$' "$RAW_LOG" || true)
if ((result_rows != expected_configurations || correct_rows != expected_checks)); then
    echo "error: expected $expected_configurations result rows and $expected_checks correctness markers; got $result_rows and $correct_rows" >&2
    exit 1
fi

"$ROOT_DIR/scripts/summarize_results.py" "$RAW_LOG" --trials "$TRIALS" \
    --csv "$RESULT_DIR/summary.csv" \
    --markdown "$RESULT_DIR/summary.md"

python3 "$ROOT_DIR/scripts/compare_paper_results.py" \
    --reference "$ROOT_DIR/claims/claim2/paper-results.csv" \
    --results "$RESULT_DIR/summary.csv" \
    --output-dir "$RESULT_DIR" "${comparison_options[@]}"

echo "📊 Summary: $RESULT_DIR/summary.md"
echo "✅ Claim 2 ${MODE#--} complete: $result_rows configuration(s)"
