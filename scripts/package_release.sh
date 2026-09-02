#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
VERSION=${1:-}
OUTPUT_DIR=${2:-"$ROOT_DIR/release"}

if [[ -z $VERSION || ! $VERSION =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "usage: $0 <version> [output-directory]" >&2
    echo "version may contain only letters, digits, dot, underscore, and hyphen" >&2
    exit 2
fi

mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR=$(cd -- "$OUTPUT_DIR" && pwd)
ARCHIVE="$OUTPUT_DIR/fpsi-$VERSION.tar.gz"
CHECKSUM="$ARCHIVE.sha256"

if [[ -e $ARCHIVE || -e $CHECKSUM ]]; then
    echo "error: release output already exists: $ARCHIVE" >&2
    exit 1
fi

release_files=(
    .gitignore
    CITATION.cff
    LICENSE
    README.md
    code
    claims
    scripts
)

tar \
    --exclude='*/__pycache__' \
    --exclude='*.pyc' \
    --exclude='code/build' \
    --exclude='code/thirdparty' \
    --transform="s,^,fpsi-$VERSION/," \
    -C "$ROOT_DIR" \
    -czf "$ARCHIVE" \
    "${release_files[@]}"

(cd -- "$OUTPUT_DIR" && sha256sum "$(basename -- "$ARCHIVE")" > "$(basename -- "$CHECKSUM")")

echo "📦 Release archive: $ARCHIVE"
echo "🔐 SHA-256 checksum: $CHECKSUM"
