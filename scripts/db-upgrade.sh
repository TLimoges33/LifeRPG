#!/usr/bin/env bash
set -euo pipefail
# Run Alembic upgrade to head using repo-local modern/alembic.ini
# Usage: DATABASE_URL=... ./scripts/db-upgrade.sh

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR"
ALEMBIC_INI="$ROOT_DIR/modern/alembic.ini"

# Default to dev sqlite if not provided
: "${DATABASE_URL:=sqlite:///./modern_dev.db}"

exec alembic -c "$ALEMBIC_INI" upgrade head
