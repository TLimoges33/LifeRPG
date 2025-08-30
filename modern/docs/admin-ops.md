# Admin operations guide

This page summarizes admin/ops capabilities and where to find them.

API endpoints (all under /api/v1):
- GET /admin/orchestration — current in-flight counts, queue depths, effective provider caps, and RQ queue length.
- GET/POST /admin/provider_caps — view/update per-provider concurrency caps (persisted); reflected in metrics and enqueue logic.
- GET /admin/hooks/schema — JSON schema and examples for hooks configuration to aid validation.
- POST /admin/hooks/validate — validate a hooks object server-side before saving.
- GET /admin/email/health — show email transport config and attempt an SMTP handshake when enabled.
- POST /admin/email/test — send a test email to verify delivery.

Frontend UI:
- Integrations page includes:
  - Provider caps editor (view/edit) and orchestration summary with manual refresh, auto-refresh, sorting, and cap utilization badges.
  - Hooks editor with example prefill and server-side validation, showing inline errors.
  - Admin settings controls for integration close mode and default sync interval.

Metrics to watch (Prometheus):
- sync_inflight, sync_queue_depth, sync_provider_cap, rq_queue_length
- sync_enqueue_skips_total{reason}
- sync_job_duration_seconds (histogram by provider,result)

Alerts (Prometheus examples in ops/prometheus-alerts.yaml):
- Provider at cap for sustained periods
- Queue depth increasing
- RQ queue backlog sustained
- Slow syncs (p95 duration) exceeding threshold
