# Database migrations (Alembic)

This project includes SQLAlchemy models and tests. For dev, the app creates tables automatically. For production, use Alembic migrations.

Example commands:

```bash
# generate (after editing models)
alembic -c backend/alembic.ini revision --autogenerate -m "your message"
# upgrade
alembic -c backend/alembic.ini upgrade head
```

Observability notes:
- Logs: The backend emits structured JSON logs to stdout (type=request/job). To view in Grafana logs panel, ship logs to Loki and label them with job="liferpg". Update the dashboard datasource UID if needed and the query accordingly.
- Metrics: New counter integration_sync_by_integration_total exposes per-integration results. Ensure your Prometheus datasource is set as PROM_DS in the dashboard.
- Rate limiting: Set REDIS_URL to enable distributed per-IP limiter.

Promtail example:
- See `ops/promtail-config.yml` for a basic config. Point `clients[0].url` to your Loki. Mount your app logs path to `/var/log/liferpg` or use the Docker containers json logs path as included.
```
# The Wizard's Grimoire - Modern Implementation

This folder contains the modern implementation of The Wizard's Grimoire, transforming daily habits into magical practices.

What is included:
- `backend/` - FastAPI-based spellcasting API with mystical energy tracking
- `frontend/` - React application themed as a magical grimoire
- `ROADMAP.md` - prioritized milestones for magical enhancement
- Dockerfile and docker-compose for local development

Next steps:
- Replace backend with FastAPI and add DB/ORM/migrations
- Implement OAuth2 and integrations adapters
- Expand frontend with components and theming

