# LifeRPG Ops Runbook

This runbook summarizes common operational signals and actions.

## Key metrics and dashboards
- HTTP: request rate (`http_requests_total`), p95 latency (`http_request_duration_seconds`), in-progress gauge.
- Jobs: `jobs_processed_total{status}`.
- Integrations: `integration_sync_total{provider,result}`, `integration_sync_by_integration_total{integration_id,result}`.
- Backpressure: `sync_enqueue_skips_total{reason}`, `sync_queue_depth{provider}`, `sync_inflight{provider}`.
- Logs: structured JSON logs for requests and jobs; ship via Promtail to Loki.

Grafana dashboard: `ops/grafana-dashboard.json` (import into Grafana and configure `PROM_DS` and `LOKI_DS`).

## Common symptoms

1) High enqueue skips
- Symptom: `sync_enqueue_skips_total` rate > 0.2 for >10m.
- Likely causes: provider concurrency cap, duplicate enqueues (guard), or downstream slowness.
- Actions:
  - Check `sync_inflight{provider}` vs cap (env `SYNC_MAX_CONCURRENCY_PER_PROVIDER`).
  - Temporarily raise the cap if safe, or reduce scheduler cadence (`sync_interval_seconds`).
  - Inspect job logs in Loki for adapter errors or rate limits.

2) Queue depth rising
- Symptom: `increase(sync_queue_depth[15m]) > 50`.
- Actions:
  - Scale workers or increase per-provider cap cautiously.
  - Pause non-critical providers by increasing intervals.
  - Check external API health/rate limits.

3) Elevated request latency
- Symptom: p95 > 500ms sustained.
- Actions:
  - Inspect recent deployments, DB CPU/IO, and external dependencies.
  - Enable sampling/profiling; consider caching.

## Configuration
- Concurrency cap per provider: `SYNC_MAX_CONCURRENCY_PER_PROVIDER` (default 4).
- Default scheduler interval: `DEFAULT_SYNC_INTERVAL_SECONDS` (default 900s). Per-integration override: `integration.config.sync_interval_seconds`.
- Close mode: `INTEGRATION_CLOSE_MODE` (`archive` default; `delete` opt-in).

## On-call checklist
- Confirm alerts and correlate with Grafana panels.
- Review recent logs for `event=enqueued|start|success|fail` in Loki.
- Take one mitigating action at a time; document in the incident log.

## Playbooks
- Raise provider cap:
  - Set `SYNC_MAX_CONCURRENCY_PER_PROVIDER` and restart worker.
- Slow the scheduler:
  - PATCH integration config `{"sync_interval_seconds": <value>}` for noisy integrations.
- Toggle close policy:
  - POST `/api/v1/admin/settings` `{ "integration_close_mode": "archive|delete" }`.
