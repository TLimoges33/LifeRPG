from typing import Generator
import models


def get_db() -> Generator:
    """FastAPI dependency: yield a SQLAlchemy Session and ensure it's closed."""
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()
