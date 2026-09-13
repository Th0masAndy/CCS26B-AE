#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
BINARY=${1:-${FPSI_BIN:-"$ROOT_DIR/code/build/fpsi"}}
EXPECTED="Total 4/4 matches found!"
PASSED=0
TRIALS=${TRIALS:-1}

if [[ ! $TRIALS =~ ^[1-9][0-9]*$ ]] || (( ${#TRIALS} > 10 )) || (( TRIALS > 2147483647 )); then
    echo "error: TRIALS must be an integer between 1 and 2147483647" >&2
    exit 2
fi

if [[ ! -x "$BINARY" ]]; then
    echo "❌ Executable not found: $BINARY" >&2
    echo "   Run ./scripts/build.sh first, or pass the executable as argument 1." >&2
    exit 2
fi

run_case()
{
    local label=$1
    shift

    echo
    echo "▶ $label"
    local output
    if ! output=$("$BINARY" "$@" -nn 8 -d 2 -delta 32 -inter 4 -try "$TRIALS" -v 1 2>&1); then
        printf '%s\n' "$output"
        echo "❌ Protocol exited with an error" >&2
        exit 1
    fi
    printf '%s\n' "$output"

    local correct_rows
    correct_rows=$(grep -Fxc "$EXPECTED" <<< "$output" || true)
    if ((correct_rows != TRIALS)); then
        echo "❌ Expected $TRIALS correctness markers; got $correct_rows" >&2
        exit 1
    fi
    PASSED=$((PASSED + 1))
}

echo "🧪 FPSI smoke test"

run_case "uniqueCell receiver, normal, L0" -assumption 0 -p 0
run_case "uniqueCell receiver, prefix, L1" -assumption 0 -prefix -p 1
run_case "uniqueCell sender, normal, L2" -assumption 0 -sender -p 2
run_case "uniqueCell sender, prefix, L0" -assumption 0 -sender -prefix -p 0
run_case "uniqueBlock receiver, normal, L2" -assumption 1 -p 2
run_case "uniqueBlock receiver, prefix, L1" -assumption 1 -prefix -p 1

if "$BINARY" -assumption 0 -prefix -p 0 -nn 8 -d 2 -delta 30 -inter 4 -try 1 >/dev/null 2>&1; then
    echo "❌ Non-power-of-two prefix delta was accepted" >&2
    exit 1
fi

echo
echo "✅ [smoke] PASS: $PASSED protocol cases and 1 parameter guard"
