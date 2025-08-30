from abc import ABC, abstractmethod
from typing import Any, Dict


class AdapterError(Exception):
    pass


class TransientError(AdapterError):
    """Errors that may succeed on retry (e.g., 429/5xx)."""


class Adapter(ABC):
    name: str

    @abstractmethod
    def sync(self, *, db, integration_id: int) -> Dict[str, Any]:
        """Perform a sync for an integration and return a summary dict.

        Expected return shape: {"ok": bool, "count": int, "details": {...}}
        """
        ...


class GoogleCalendarAdapter(Adapter):
    name = 'google_calendar'

    def sync(self, *, db, integration_id: int) -> Dict[str, Any]:
        # Placeholder: our Google flow is handled by a dedicated endpoint.
        return {"ok": True, "count": 0, "details": {"note": "use /sync_to_habits endpoint"}}


class TodoistAdapter(Adapter):
    name = 'todoist'

    def sync(self, *, db, integration_id: int) -> Dict[str, Any]:
        # Lazy imports to avoid circulars
        from . import models
        from .crypto import decrypt_text
        import requests

        token_row = (
            db.query(models.OAuthToken)
            .filter_by(integration_id=integration_id)
            .order_by(models.OAuthToken.id.desc())
            .first()
        )
        if not token_row:
            raise AdapterError('no token for todoist integration')
        token = decrypt_text(token_row.access_token) if token_row.access_token else None
        if not token:
            raise AdapterError('unable to decrypt todoist token')

        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
        }
        try:
            resp = requests.get('https://api.todoist.com/rest/v2/tasks', headers=headers, timeout=10)
        except Exception as e:
            raise TransientError(str(e))
        if resp.status_code in (429, 500, 502, 503, 504):
            raise TransientError(f'todoist HTTP {resp.status_code}')
        if resp.status_code != 200:
            raise AdapterError(f'todoist HTTP {resp.status_code}')

        # Load integration config for cursors/flags
        integ = db.query(models.Integration).filter_by(id=integration_id).first()
        conf = {}
        if integ and integ.config:
            try:
                import json as _json
                conf = _json.loads(integ.config)
            except Exception:
                conf = {}
        full_fetch = bool(conf.get('todoist_full_fetch', True))

        items = resp.json() or []
        created = 0
        updated = 0
        seen_ext_ids = set()

        from .config import settings

        def _apply_close_policy(db, habit, should_close: bool, archived: bool):
            if not habit:
                return False
            if settings.INTEGRATION_CLOSE_MODE == 'delete' and should_close:
                db.delete(habit)
                return True
            new_status = 'archived' if archived else ('completed' if should_close else habit.status)
            if habit.status != new_status:
                habit.status = new_status
                return True
            return False

        for it in items:
            ext_id = str(it.get('id'))
            title = it.get('content') or 'Todoist Task'
            is_completed = bool(it.get('is_completed'))
            is_archived = bool(it.get('is_deleted')) or bool(it.get('is_archived')) if isinstance(it.get('is_archived'), bool) else False
            due = it.get('due', {}) or {}
            due_dt = due.get('datetime') or due.get('date')
            labels = it.get('labels') or []
            if not ext_id:
                continue
            seen_ext_ids.add(ext_id)
            mapping = (
                db.query(models.IntegrationItemMap)
                .filter_by(integration_id=integration_id, external_id=ext_id, entity_type='habit')
                .first()
            )
            if mapping:
                habit = db.query(models.Habit).filter_by(id=mapping.entity_id).first()
                if habit:
                    changed = False
                    if habit.title != title:
                        habit.title = title
                        changed = True
                    changed |= _apply_close_policy(db, habit, is_completed, is_archived)
                    if due_dt:
                        try:
                            from datetime import datetime
                            habit.due_date = datetime.fromisoformat(due_dt.replace('Z', '+00:00'))
                            changed = True
                        except Exception:
                            pass
                    if labels:
                        import json as _json
                        habit.labels = _json.dumps(labels)
                        changed = True
                    if changed:
                        updated += 1
            else:
                integ2 = integ or db.query(models.Integration).filter_by(id=integration_id).first()
                if not integ2:
                    raise AdapterError('integration missing during upsert')
                import json as _json
                habit = models.Habit(
                    user_id=integ2.user_id,
                    project_id=None,
                    title=title,
                    notes='from todoist',
                    cadence='once',
                    status='archived' if is_archived else ('completed' if is_completed else 'active'),
                    labels=_json.dumps(labels) if labels else None,
                )
                db.add(habit)
                db.flush()
                try:
                    from sqlalchemy.dialects.postgresql import insert as pg_insert
                    stmt = pg_insert(models.IntegrationItemMap.__table__).values(
                        integration_id=integration_id,
                        external_id=ext_id,
                        entity_type='habit',
                        entity_id=habit.id,
                    ).on_conflict_do_update(
                        index_elements=['integration_id', 'external_id', 'entity_type'],
                        set_={'entity_id': habit.id}
                    )
                    db.execute(stmt)
                except Exception:
                    db.add(models.IntegrationItemMap(integration_id=integration_id, external_id=ext_id, entity_type='habit', entity_id=habit.id))
                created += 1

        db.flush()

        if full_fetch:
            mappings = db.query(models.IntegrationItemMap).filter_by(integration_id=integration_id, entity_type='habit').all()
            for m in mappings:
                if m.external_id not in seen_ext_ids:
                    habit = db.query(models.Habit).filter_by(id=m.entity_id).first()
                    if habit:
                        try:
                            if settings.INTEGRATION_CLOSE_MODE == 'delete':
                                db.delete(habit)
                            else:
                                habit.status = 'archived'
                        except Exception:
                            habit.status = 'archived'
            db.flush()

        if integ:
            try:
                import json as _json
                from datetime import datetime, timezone
                conf['last_sync_at'] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                integ.config = _json.dumps(conf)
                db.flush()
            except Exception:
                pass

        return {"ok": True, "count": len(items), "created": created, "updated": updated}


class GitHubAdapter(Adapter):
    name = 'github'

    def sync(self, *, db, integration_id: int) -> Dict[str, Any]:
        from . import models
        from .crypto import decrypt_text
        import requests

        token_row = (
            db.query(models.OAuthToken)
            .filter_by(integration_id=integration_id)
            .order_by(models.OAuthToken.id.desc())
            .first()
        )
        if not token_row:
            raise AdapterError('no token for github integration')
        token = decrypt_text(token_row.access_token) if token_row.access_token else None
        if not token:
            raise AdapterError('unable to decrypt github token')

        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github+json',
        }
        url = 'https://api.github.com/issues'
        try:
            resp = requests.get(url, headers=headers, timeout=10)
        except Exception as e:
            raise TransientError(str(e))
        if resp.status_code in (429, 500, 502, 503, 504):
            raise TransientError(f'github HTTP {resp.status_code}')
        if resp.status_code != 200:
            raise AdapterError(f'github HTTP {resp.status_code}')

        integ = db.query(models.Integration).filter_by(id=integration_id).first()
        conf = {}
        if integ and integ.config:
            try:
                import json as _json
                conf = _json.loads(integ.config)
            except Exception:
                conf = {}
        since = conf.get('github_since')

        items = []
        page = 1
        while True:
            params = {'per_page': 100, 'page': page}
            if since:
                params['since'] = since
            r = requests.get(url, headers=headers, params=params, timeout=10)
            if r.status_code in (429, 500, 502, 503, 504):
                raise TransientError(f'github HTTP {r.status_code}')
            if r.status_code != 200:
                raise AdapterError(f'github HTTP {r.status_code}')
            batch = r.json() or []
            items.extend(batch)
            link = r.headers.get('Link') or r.headers.get('link')
            if link and 'rel="next"' in link:
                page += 1
                continue
            if len(batch) == 100:
                page += 1
                continue
            break

        created = 0
        updated = 0
        seen_ext_ids = set()

        from .config import settings

        def _apply_close_policy(db, habit, should_close: bool):
            if not habit:
                return False
            if settings.INTEGRATION_CLOSE_MODE == 'delete' and should_close:
                db.delete(habit)
                return True
            new_status = 'completed' if should_close else 'active'
            if habit.status != new_status:
                habit.status = new_status
                return True
            return False

        for issue in items:
            ext_id = str(issue.get('id'))
            title = issue.get('title') or 'GitHub Issue'
            state = (issue.get('state') or '').lower()
            labels = [l.get('name') for l in (issue.get('labels') or []) if isinstance(l, dict)]
            milestone = issue.get('milestone', {}) or {}
            due_on = milestone.get('due_on')
            if not ext_id:
                continue
            seen_ext_ids.add(ext_id)
            mapping = (
                db.query(models.IntegrationItemMap)
                .filter_by(integration_id=integration_id, external_id=ext_id, entity_type='habit')
                .first()
            )
            if mapping:
                habit = db.query(models.Habit).filter_by(id=mapping.entity_id).first()
                if habit:
                    changed = False
                    if habit.title != title:
                        habit.title = title
                        changed = True
                    changed |= _apply_close_policy(db, habit, state == 'closed')
                    if due_on:
                        from datetime import datetime
                        try:
                            habit.due_date = datetime.fromisoformat(due_on.replace('Z', '+00:00'))
                            changed = True
                        except Exception:
                            pass
                    if labels:
                        import json as _json
                        habit.labels = _json.dumps(labels)
                        changed = True
                    if changed:
                        updated += 1
            else:
                integ2 = integ or db.query(models.Integration).filter_by(id=integration_id).first()
                if not integ2:
                    raise AdapterError('integration missing during upsert')
                import json as _json
                habit = models.Habit(
                    user_id=integ2.user_id,
                    project_id=None,
                    title=title,
                    notes='from github',
                    cadence='once',
                    status='completed' if state == 'closed' else 'active',
                    labels=_json.dumps(labels) if labels else None,
                )
                db.add(habit)
                db.flush()
                try:
                    from sqlalchemy.dialects.postgresql import insert as pg_insert
                    stmt = pg_insert(models.IntegrationItemMap.__table__).values(
                        integration_id=integration_id,
                        external_id=ext_id,
                        entity_type='habit',
                        entity_id=habit.id,
                    ).on_conflict_do_update(
                        index_elements=['integration_id', 'external_id', 'entity_type'],
                        set_={'entity_id': habit.id}
                    )
                    db.execute(stmt)
                except Exception:
                    db.add(models.IntegrationItemMap(integration_id=integration_id, external_id=ext_id, entity_type='habit', entity_id=habit.id))
                created += 1

        db.flush()

        if not since:
            mappings = db.query(models.IntegrationItemMap).filter_by(integration_id=integration_id, entity_type='habit').all()
            for m in mappings:
                if m.external_id not in seen_ext_ids:
                    habit = db.query(models.Habit).filter_by(id=m.entity_id).first()
                    if habit:
                        if settings.INTEGRATION_CLOSE_MODE == 'delete':
                            db.delete(habit)
                        else:
                            habit.status = 'archived'
            db.flush()

        if integ:
            try:
                import json as _json
                from datetime import datetime, timezone
                conf['github_since'] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                integ.config = _json.dumps(conf)
                db.flush()
            except Exception:
                pass

        return {"ok": True, "count": len(items), "created": created, "updated": updated}


ADAPTERS = {
    'google_calendar': GoogleCalendarAdapter(),
    'todoist': TodoistAdapter(),
    'github': GitHubAdapter(),
}


class SlackAdapter(Adapter):
    name = 'slack'

    def sync(self, *, db, integration_id: int) -> Dict[str, Any]:
        """Optional: send a simple notification via incoming webhook as a scaffold.

        This is a no-op if the webhook is missing. Intended as a placeholder.
        """
        from . import models
        from .crypto import decrypt_text
        import requests

        tok = (
            db.query(models.OAuthToken)
            .filter_by(integration_id=integration_id)
            .order_by(models.OAuthToken.id.desc())
            .first()
        )
        if not tok or not tok.access_token:
            return {"ok": True, "count": 0, "details": {"note": "no webhook"}}
        webhook = decrypt_text(tok.access_token)
        if not webhook:
            raise AdapterError('unable to decrypt slack webhook')
        payload = {"text": "LifeRPG: Slack integration sync triggered."}
        try:
            r = requests.post(webhook, json=payload, timeout=5)
        except Exception as e:
            raise TransientError(str(e))
        if r.status_code >= 500:
            raise TransientError(f'slack HTTP {r.status_code}')
        if r.status_code >= 400:
            raise AdapterError(f'slack HTTP {r.status_code}')
        return {"ok": True, "count": 1}

ADAPTERS['slack'] = SlackAdapter()
