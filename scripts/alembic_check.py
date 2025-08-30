#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata

# Ensure models are importable (expect PYTHONPATH to be set by caller)
try:
    from modern.backend import models
except Exception as e:
    print(f"Failed to import models: {e}")
    sys.exit(2)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./modern_dev.db")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    context = MigrationContext.configure(conn)
    diffs = compare_metadata(context, models.Base.metadata)

if diffs:
    print("Schema diffs detected between DB and models:")
    for d in diffs:
        print(" -", d)
    sys.exit(1)

print("No schema diffs detected.")
