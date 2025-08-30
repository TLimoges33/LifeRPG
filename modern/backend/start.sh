#!/usr/bin/env bash
set -euo pipefail

# Default to sqlite if not provided
: "${DATABASE_URL:=sqlite:///./modern_dev.db}"
export PYTHONPATH="/app"

# Run migrations
alembic -c modern/alembic.ini upgrade head

# Start API
exec python -m uvicorn modern.backend.app:app --host 0.0.0.0 --port 8000
