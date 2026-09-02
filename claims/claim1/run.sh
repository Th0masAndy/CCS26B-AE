#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
RESULT_DIR=${FPSI_RESULT_DIR:-"$ROOT_DIR/artifact-results/claim1"}

if [[ ! -x "$ROOT_DIR/code/build/fpsi" ]]; then
    echo "error: FPSI is not built; run ./scripts/build.sh first" >&2
    exit 2
fi

FPSI_RESULT_DIR="$RESULT_DIR" "$ROOT_DIR/scripts/run_reproduction.sh" --quick
