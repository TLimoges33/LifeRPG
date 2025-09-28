FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -u 1001 appuser

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

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

ENV PYTHONPATH=/app

EXPOSE 8000

# Start script runs migrations then launches API
COPY modern/backend/start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
