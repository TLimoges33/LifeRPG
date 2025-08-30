FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (optional): add git/curl if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY modern/backend/requirements_full.txt /app/modern/backend/requirements_full.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /app/modern/backend/requirements_full.txt

# Copy application code (backend + alembic)
COPY modern /app/modern

ENV PYTHONPATH=/app

EXPOSE 8000

# Start script runs migrations then launches API
COPY modern/backend/start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
