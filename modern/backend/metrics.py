from time import perf_counter
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import os
try:
    from redis import Redis
except Exception:
    Redis = None
import json
import logging


REQUESTS_TOTAL = Counter('http_requests_total', 'Total HTTP requests', ['method', 'path', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency seconds', ['method', 'path', 'status'], buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5, 10))
IN_PROGRESS = Gauge('http_requests_in_progress', 'In-progress HTTP requests', ['method', 'path'])

# App-specific metrics
JOBS_PROCESSED_TOTAL = Counter(
    'jobs_processed_total', 'Background jobs processed', ['status']
)
INTEGRATION_SYNC_TOTAL = Counter('integration_sync_total', 'Integration sync events', ['provider', 'result'])
INTEGRATION_SYNC_BY_INTEG = Counter('integration_sync_by_integration_total', 'Integration sync events by integration id', ['integration_id', 'result'])
WEBHOOK_EVENTS_TOTAL = Counter(
    'webhook_events_total', 'Webhook events received', ['provider', 'verified']
)
SYNC_JOB_DURATION_SECONDS = Histogram(
    'sync_job_duration_seconds', 'Duration of integration sync jobs', ['provider', 'result'],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60)
)

# Backpressure / enqueue metrics
SYNC_ENQUEUE_SKIPS_TOTAL = Counter(
    'sync_enqueue_skips_total', 'Sync enqueue attempts skipped due to backpressure or guards', ['reason']
)

# Provider-level orchestration gauges (read from Redis on scrape)
SYNC_QUEUE_DEPTH = Gauge('sync_queue_depth', 'Number of enqueued sync jobs by provider', ['provider'])
SYNC_INFLIGHT = Gauge('sync_inflight', 'Number of in-flight sync jobs by provider', ['provider'])
SYNC_PROVIDER_CAP = Gauge('sync_provider_cap', 'Configured max concurrency per provider', ['provider'])
RQ_QUEUE_LENGTH = Gauge('rq_queue_length', 'Number of jobs in RQ queue', ['queue'])


def _path_template(request: Request) -> str:
    # Attempt to use the route path template to reduce cardinality
    route = request.scope.get('route')
    if route is not None and getattr(route, 'path', None):
        return route.path
    return request.url.path


logger = logging.getLogger("liferpg")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))  # raw message will be JSON
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = _path_template(request)
        # Skip metrics endpoint to avoid self-observation noise
        if path == '/metrics':
            return await call_next(request)
        IN_PROGRESS.labels(method=method, path=path).inc()
        start = perf_counter()
        try:
            response: Response = await call_next(request)
            status = str(response.status_code)
            dur = perf_counter() - start
            REQUESTS_TOTAL.labels(method=method, path=path, status=status).inc()
            REQUEST_LATENCY.labels(method=method, path=path, status=status).observe(dur)
            try:
                logger.info(json.dumps({
                    'type': 'request',
                    'method': method,
                    'path': path,
                    'status': int(status),
                    'duration_ms': round(dur * 1000, 3)
                }))
            except Exception:
                pass
            return response
        finally:
            IN_PROGRESS.labels(method=method, path=path).dec()


def metrics_endpoint() -> Response:
    # Refresh orchestration gauges from Redis (best-effort)
    try:
        _update_sync_gauges_from_redis()
    except Exception:
        pass
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


def setup_metrics(app):
    app.add_middleware(PrometheusMiddleware)
    # Plain GET /metrics endpoint
    app.add_api_route('/metrics', metrics_endpoint, methods=['GET'])


# Helper recorders (optional sugar)
def record_job_processed(status: str = 'success'):
    JOBS_PROCESSED_TOTAL.labels(status=status).inc()


def record_integration_sync(provider: str, result: str):
    INTEGRATION_SYNC_TOTAL.labels(provider=provider, result=result).inc()
    # integration_id variant is recorded elsewhere via record_integration_sync_by_id


def record_webhook(provider: str, verified: bool):
    WEBHOOK_EVENTS_TOTAL.labels(provider=provider, verified=str(bool(verified)).lower()).inc()


def record_integration_sync_by_id(integration_id: int, result: str):
    INTEGRATION_SYNC_BY_INTEG.labels(integration_id=str(integration_id), result=result).inc()


def log_job_event(event: str, **kwargs):
    try:
        logger.info(json.dumps({'type': 'job', 'event': event, **kwargs}))
    except Exception:
        pass


def record_enqueue_skipped(reason: str = 'guard'):
    SYNC_ENQUEUE_SKIPS_TOTAL.labels(reason=reason).inc()


def _get_redis():
    if not Redis:
        return None
    url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    try:
        return Redis.from_url(url)
    except Exception:
        return None


def _update_sync_gauges_from_redis():
    r = _get_redis()
    if not r:
        return
    # Provider caps: compute min override across integrations vs env default
    try:
        from .models import SessionLocal, Integration
        from .config import settings
        s = SessionLocal()
        caps_by_provider = {}
        try:
            for row in s.query(Integration).all():
                prov = row.provider
                if not prov:
                    continue
                v = None
                if row.config:
                    import json as _json
                    try:
                        cfg = _json.loads(row.config)
                        vv = cfg.get('sync_max_concurrency')
                        if isinstance(vv, int) and vv > 0:
                            v = vv
                    except Exception:
                        pass
                if v is not None:
                    if prov not in caps_by_provider:
                        caps_by_provider[prov] = v
                    else:
                        caps_by_provider[prov] = min(caps_by_provider[prov], v)
        finally:
            s.close()
        default_cap = settings.DEFAULT_PROVIDER_CAP if settings else int(os.getenv('SYNC_MAX_CONCURRENCY_PER_PROVIDER', '4'))
        # Set the cap gauge for any seen providers; fall back to default for inflight keys later
        # Include process-wide overrides from settings.PROVIDER_CAPS and admin settings integration
        proc_caps = getattr(settings, 'PROVIDER_CAPS', {}) if settings else {}
        try:
            import json as _json
            admin_row = (
                s.query(Integration)
                .filter_by(provider='admin', external_id='settings')
                .order_by(Integration.id.desc())
                .first()
            )
            admin_caps = {}
            if admin_row and admin_row.config:
                acfg = _json.loads(admin_row.config) or {}
                if isinstance(acfg.get('provider_caps'), dict):
                    admin_caps = acfg.get('provider_caps')
        except Exception:
            admin_caps = {}
        for prov, cap in caps_by_provider.items():
            base = min(default_cap, cap)
            if prov in proc_caps:
                try:
                    base = min(base, int(proc_caps[prov]))
                except Exception:
                    pass
            if prov in admin_caps:
                try:
                    base = min(base, int(admin_caps[prov]))
                except Exception:
                    pass
            SYNC_PROVIDER_CAP.labels(provider=prov).set(base)
    except Exception:
        pass
    # Queue depth
    for key in r.scan_iter(match='sync_queue_depth:*'):
        try:
            provider = key.decode().split(':', 1)[1]
            val = int(r.get(key) or 0)
            SYNC_QUEUE_DEPTH.labels(provider=provider).set(val)
        except Exception:
            continue
    # Inflight
    for key in r.scan_iter(match='sync_provider_inflight:*'):
        try:
            provider = key.decode().split(':', 1)[1]
            val = int(r.get(key) or 0)
            SYNC_INFLIGHT.labels(provider=provider).set(val)
            # Also set cap for this provider from env
            try:
                # set to default/provider override if not already set
                metrics = getattr(SYNC_PROVIDER_CAP, '_metrics', {})
                label_keys = [k for k in getattr(metrics, 'keys', lambda: [])()]
                if hasattr(metrics, 'keys'):
                    exists = any(True for k in metrics.keys())  # best-effort
                else:
                    exists = False
                # Always set, using settings if available
                from .config import settings as _s
                base = _s.DEFAULT_PROVIDER_CAP if _s else int(os.getenv('SYNC_MAX_CONCURRENCY_PER_PROVIDER', '4'))
                ov = (getattr(_s, 'PROVIDER_CAPS', {}) or {}).get(provider) if _s else None
                if ov:
                    try:
                        base = min(base, int(ov))
                    except Exception:
                        pass
                SYNC_PROVIDER_CAP.labels(provider=provider).set(base)
            except Exception:
                pass
        except Exception:
            continue
    # RQ queue length (best-effort)
    try:
        from rq import Queue
        from redis import Redis as _Redis
        queues_env = os.getenv('RQ_QUEUES', 'default')
        names = [n.strip() for n in queues_env.split(',') if n.strip()] or ['default']
        conn = _Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        for name in names:
            try:
                q = Queue(name, connection=conn)
                RQ_QUEUE_LENGTH.labels(queue=name).set(len(q))
            except Exception:
                continue
    except Exception:
        pass
