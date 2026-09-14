#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
RESULT_DIR=${FPSI_RESULT_DIR:-"$ROOT_DIR/artifact-results/claim1"}

if [[ ! -x "$ROOT_DIR/code/build/fpsi" ]]; then
    echo "error: FPSI is not built; run ./scripts/build/run.sh first" >&2
    exit 2
fi

FPSI_RESULT_DIR="$RESULT_DIR" "$ROOT_DIR/scripts/reproduction/run.sh" --quick

python3 "$ROOT_DIR/scripts/data/check_boundary_inputs.py" \
    --binary "$ROOT_DIR/code/build/fpsi" \
    --output-dir "$RESULT_DIR/boundary" \
    --trials "${TRIALS:-1}" | tee "$RESULT_DIR/boundary.txt"

echo "✅ Claim 1 complete"
