PY?=python

.PHONY: worker
worker:
	REDIS_URL?=redis://localhost:6379/0 rq worker -u $$REDIS_URL default

.PHONY: up
up:
	docker compose up --build

.PHONY: up-d
up-d:
	docker compose up -d --build

.PHONY: down
down:
	docker compose down -v
