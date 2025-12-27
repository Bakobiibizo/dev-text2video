#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[launch] running scripts/setup.sh for dev-text2video..."
cd "$ROOT_DIR"
bash scripts/setup.sh "$@"
