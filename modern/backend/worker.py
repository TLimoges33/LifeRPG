import os
import time
from typing import Optional
try:
    from rq import Queue
    from rq import Retry
    from redis import Redis
except Exception:
    Queue = None
    Retry = None
    Redis = None
from metrics import (
    record_job_processed, record_integration_sync_by_id, 
    log_job_event, record_enqueue_skipped, SYNC_JOB_DURATION_SECONDS
)
from notifier import emit_sync_event
from hooks import hooks_for_integration
from adapters import ADAPTERS, AdapterError, TransientError


def get_queue():
    if not Queue or not Redis:
        return None
    url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    try:
        conn = Redis.from_url(url)
        # probe connectivity; if fails, fall back to inline (None)
        try:
            conn.ping()
        except Exception:
            return None
        return Queue('default', connection=conn)
    except Exception:
        # No Redis available
        return None


def example_job(payload: dict):
    try:
        time.sleep(0.1)
        record_job_processed('success')
        return {'ok': True, 'echo': payload}
    except Exception:
        record_job_processed('error')
        raise


def _sleep_backoff(attempt: int, base: float = 0.5, cap: float = 10.0):
    # Exponential backoff with jitter
    delay = min(cap, base * (2 ** (attempt - 1)))
    # tiny jitter
    time.sleep(delay + (0.1 * (attempt % 3)))


def run_adapter_sync(provider: str, integration_id: int) -> dict:
    """Execute an adapter sync with retries/backoff for transient failures.

    If running under RQ and Retry is available, rely on RQ for retry scheduling
    (we still guard a couple quick local retries for connection hiccups).
    """
    adapter = ADAPTERS.get(provider)
    if not adapter:
        record_job_processed('error')
        raise ValueError('unknown provider')
    # Provider inflight accounting
    inflight_key = f"sync_provider_inflight:{provider}"
    r = None
    try:
        if Redis:
            url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = Redis.from_url(url)
            r.incr(inflight_key)
            r.expire(inflight_key, 300)
    except Exception:
        r = None
    # Lazy import to obtain a session
    from .models import SessionLocal
    db = SessionLocal()
    try:
        # Quick local retry loop (max 3 attempts) for immediate hiccups
        attempts = 0
        while True:
            attempts += 1
            try:
                log_job_event('start', provider=provider, integration_id=integration_id, attempt=attempts)
                try:
                    hooks_for_integration(db, integration_id).run_pre(db=db, integration_id=integration_id, context={'provider': provider})
                except Exception:
                    pass
                import time as _t
                _t0 = _t.perf_counter()
                result = adapter.sync(db=db, integration_id=integration_id)
                _dur = _t.perf_counter() - _t0
                record_job_processed('success')
                record_integration_sync_by_id(integration_id, 'success')
                try:
                    SYNC_JOB_DURATION_SECONDS.labels(provider=provider, result='success').observe(_dur)
                except Exception:
                    pass
                log_job_event('success', provider=provider, integration_id=integration_id, attempts=attempts)
                try:
                    emit_sync_event(db, integration_id, 'sync_success', { 'provider': provider, 'summary': result })
                except Exception:
                    pass
                try:
                    hooks_for_integration(db, integration_id).run_post(db=db, integration_id=integration_id, status='success', context={'provider': provider, 'count': result.get('count')})
                except Exception:
                    pass
                return {**result, 'attempts': attempts}
            except TransientError:
                if attempts >= 3:
                    record_job_processed('error')
                    record_integration_sync_by_id(integration_id, 'transient_fail')
                    try:
                        SYNC_JOB_DURATION_SECONDS.labels(provider=provider, result='transient_fail').observe((_t.perf_counter() - _t0) if '_t0' in locals() else 0.0)
                    except Exception:
                        pass
                    log_job_event('fail', provider=provider, integration_id=integration_id, reason='transient', attempts=attempts)
                    try:
                        emit_sync_event(db, integration_id, 'sync_fail', { 'provider': provider, 'reason': 'transient' })
                    except Exception:
                        pass
                    try:
                        hooks_for_integration(db, integration_id).run_post(db=db, integration_id=integration_id, status='fail', context={'provider': provider})
                    except Exception:
                        pass
                    raise
                _sleep_backoff(attempts)
                continue
            except AdapterError:
                record_job_processed('error')
                record_integration_sync_by_id(integration_id, 'error')
                try:
                    SYNC_JOB_DURATION_SECONDS.labels(provider=provider, result='error').observe((_t.perf_counter() - _t0) if '_t0' in locals() else 0.0)
                except Exception:
                    pass
                log_job_event('fail', provider=provider, integration_id=integration_id, reason='adapter_error', attempts=attempts)
                try:
                    emit_sync_event(db, integration_id, 'sync_fail', { 'provider': provider, 'reason': 'adapter_error' })
                except Exception:
                    pass
                try:
                    hooks_for_integration(db, integration_id).run_post(db=db, integration_id=integration_id, status='fail', context={'provider': provider})
                except Exception:
                    pass
                raise
    finally:
        try:
            db.close()
        except Exception:
            pass
        # Decrement inflight
        try:
            if r:
                r.decr(inflight_key)
        except Exception:
            pass


def enqueue_adapter_sync(provider: str, integration_id: int):
    q = get_queue()
    if not q:
        # run inline if no queue
        return None
    # Backpressure: prevent duplicate enqueues within a short window per integration
    try:
        import os
        from redis import Redis
        url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = Redis.from_url(url)
        # Provider concurrency check with per-provider overrides from Integration.config
        # Base cap: env default or settings default
        try:
            from .config import settings
            max_conc = settings.DEFAULT_PROVIDER_CAP
            # apply global per-provider override if present
            if provider in settings.PROVIDER_CAPS:
                max_conc = min(max_conc, int(settings.PROVIDER_CAPS[provider]))
        except Exception:
            max_conc = int(os.getenv('SYNC_MAX_CONCURRENCY_PER_PROVIDER', '4'))
        try:
            # if a per-provider cap is configured on any integration for this provider, use the min cap
            from .models import SessionLocal, Integration
            s = SessionLocal()
            caps = []
            try:
                for row in s.query(Integration).filter_by(provider=provider).all():
                    if row.config:
                        import json as _json
                        try:
                            cfg = _json.loads(row.config)
                            v = cfg.get('sync_max_concurrency')
                            if isinstance(v, int) and v > 0:
                                caps.append(v)
                        except Exception:
                            continue
                # include global admin settings provider caps
                admin_row = (
                    s.query(Integration)
                    .filter_by(provider='admin', external_id='settings')
                    .order_by(Integration.id.desc())
                    .first()
                )
                if admin_row and admin_row.config:
                    import json as _json
                    try:
                        acfg = _json.loads(admin_row.config) or {}
                        pc = acfg.get('provider_caps') or {}
                        if isinstance(pc, dict) and provider in pc:
                            pv = int(pc.get(provider))
                            if pv > 0:
                                caps.append(pv)
                    except Exception:
                        pass
            finally:
                s.close()
            if caps:
                max_conc = min(max_conc, min(caps))
        except Exception:
            pass
        inflight_key = f"sync_provider_inflight:{provider}"
        try:
            inflight = int(r.get(inflight_key) or 0)
        except Exception:
            inflight = 0
        if inflight >= max_conc:
            # increment queue depth metric key and skip
            r.incr(f"sync_queue_depth:{provider}")
            r.expire(f"sync_queue_depth:{provider}", 300)
            log_job_event('enqueue_skipped', provider=provider, integration_id=integration_id, reason='provider_cap', inflight=inflight, max=max_conc)
            record_enqueue_skipped('provider_cap')
            return None
        guard_key = f"sync_guard:{integration_id}"
        if r.setnx(guard_key, '1'):
            r.expire(guard_key, 30)  # 30s guard
        else:
            # already enqueued recently
            log_job_event('enqueue_skipped', integration_id=integration_id, reason='guard')
            record_enqueue_skipped('guard')
            return None
    except Exception:
        pass
    kwargs = {'provider': provider, 'integration_id': integration_id}
    # If RQ Retry is available, add a retry policy with exponential backoff
    if Retry is not None:
        return q.enqueue(run_adapter_sync, provider, integration_id, retry=Retry(max=5, interval=[5, 10, 20, 40, 60]))
    return q.enqueue(run_adapter_sync, provider, integration_id)


def schedule_periodic_syncs():
    """Naive scheduler: enqueue all integrations periodically.

    Intended to be called by an external timer (cron/k8s CronJob) or a long-running worker.
    """
    from .models import SessionLocal, Integration
    db = SessionLocal()
    try:
        rows = db.query(Integration).all()
        import json as _json, random
        now = time.time()
        for integ in rows:
            conf = {}
            if integ.config:
                try:
                    conf = _json.loads(integ.config)
                except Exception:
                    conf = {}
            # default 15 minutes
            interval = int(conf.get('sync_interval_seconds', 900))
            # jitter up to 10%
            jitter = int(interval * 0.1)
            interval_with_jitter = interval + (random.randint(-jitter, jitter) if jitter > 0 else 0)
            last_sync_at = conf.get('last_sync_at') or conf.get('github_since')
            should_run = True
            if last_sync_at:
                try:
                    # parse ISO and compare
                    from datetime import datetime, timezone
                    ts = datetime.fromisoformat(last_sync_at.replace('Z','+00:00')).timestamp()
                    should_run = (now - ts) >= max(60, interval_with_jitter)
                except Exception:
                    should_run = True
            if should_run:
                enqueue_adapter_sync(integ.provider, integ.id)
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Simple CLI entrypoint: python -m backend.worker schedule
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'schedule'
    if cmd == 'schedule':
        schedule_periodic_syncs()
