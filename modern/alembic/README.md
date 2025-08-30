Alembic migration scripts for LifeRPG (modern/backend)

Use:

    export DATABASE_URL=sqlite:///./modern_dev.db
    alembic -c modern/alembic.ini upgrade head

The env.py uses modern.backend.models for metadata.
