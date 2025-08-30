SHELL := /bin/bash

.PHONY: help db-upgrade db-stamp alembic-rev
.PHONY: help db-upgrade db-stamp alembic-rev alembic-current alembic-history drift-check pre-commit-install pre-commit-run

help:
	@echo "Targets:"
	@echo "  db-upgrade       - Run Alembic upgrade head (uses DATABASE_URL)"
	@echo "  db-stamp         - Stamp DB as at head (uses DATABASE_URL)"
	@echo "  alembic-rev MSG= - Create auto migration with message"
	@echo "  alembic-current  - Show current DB revision"
	@echo "  alembic-history  - Show migration history"
	@echo "  drift-check      - Compare DB schema vs models (non-zero exit on diff)"
	@echo "  pre-commit-install - Install git pre-commit hooks"
	@echo "  pre-commit-run     - Run pre-commit on all files"

db-upgrade:
	@DATABASE_URL?=sqlite:///./modern_dev.db
	@export PYTHONPATH=$(PWD); \
	 alembic -c modern/alembic.ini upgrade head

db-stamp:
	@DATABASE_URL?=sqlite:///./modern_dev.db
	@export PYTHONPATH=$(PWD); \
	 alembic -c modern/alembic.ini stamp head

alembic-rev:
	@if [ -z "$(MSG)" ]; then echo "Usage: make alembic-rev MSG=your message"; exit 1; fi
	@export PYTHONPATH=$(PWD); \
	 alembic -c modern/alembic.ini revision --autogenerate -m "$(MSG)"

alembic-current:
	@export PYTHONPATH=$(PWD); \
	 alembic -c modern/alembic.ini current

alembic-history:
	@export PYTHONPATH=$(PWD); \
	 alembic -c modern/alembic.ini history --verbose

drift-check:
	@export PYTHONPATH=$(PWD); \
	 python scripts/alembic_check.py

pre-commit-install:
	@python -m pip install pre-commit >/dev/null 2>&1 || true
	@pre-commit install
	@echo "pre-commit hooks installed"

pre-commit-run:
	@python -m pip install pre-commit >/dev/null 2>&1 || true
	@pre-commit run --all-files
