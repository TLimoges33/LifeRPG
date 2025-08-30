#!/usr/bin/env bash
set -euo pipefail
# Stamp current DB as at migration head
# Usage: DATABASE_URL=... ./scripts/db-stamp-head.sh

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR"
ALEMBIC_INI="$ROOT_DIR/modern/alembic.ini"

: "${DATABASE_URL:=sqlite:///./modern_dev.db}"

exec alembic -c "$ALEMBIC_INI" stamp head
