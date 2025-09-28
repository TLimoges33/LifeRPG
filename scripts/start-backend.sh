#!/bin/bash
echo "🚀 Starting LifeRPG Backend..."
cd modern/backend
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn app:app --reload --host 0.0.0.0 --port 8000
