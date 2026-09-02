#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
LABEL=${1:-}

if [[ -z $LABEL || $# -lt 2 ]]; then
    echo "usage: $0 <label> <fpsi-options...>" >&2
    exit 2
fi
shift

if [[ ! -x "$ROOT_DIR/code/build/fpsi" ]]; then
    echo "error: $ROOT_DIR/code/build/fpsi is missing; run ./scripts/build.sh first" >&2
    exit 2
fi
if [[ ! -x /usr/bin/time ]]; then
    echo "error: /usr/bin/time is missing; install the GNU time package" >&2
    exit 2
fi
if [[ ! $LABEL =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "error: label may contain only letters, digits, dot, underscore, and hyphen" >&2
    exit 2
fi

RESULT_DIR=${FPSI_RESULT_DIR:-"$ROOT_DIR/artifact-results"}/resources
mkdir -p "$RESULT_DIR"

"$ROOT_DIR/scripts/collect_environment.sh" > "$RESULT_DIR/$LABEL-environment.txt"
/usr/bin/time -v -o "$RESULT_DIR/$LABEL-resources.txt" \
    "$ROOT_DIR/code/build/fpsi" "$@" 2>&1 | tee "$RESULT_DIR/$LABEL-output.txt"

echo "📄 Protocol output: $RESULT_DIR/$LABEL-output.txt"
echo "📊 Resource report: $RESULT_DIR/$LABEL-resources.txt"
