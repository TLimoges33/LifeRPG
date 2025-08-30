from typing import Any, Dict, List


class Hook:
    def run(self, *, db, integration_id: int, event: str, context: Dict[str, Any]):
        raise NotImplementedError()


class SlackHook(Hook):
    def __init__(self, preset_text: str | None = None):
        self.preset_text = preset_text

    def run(self, *, db, integration_id: int, event: str, context: Dict[str, Any]):
        from .notifier import emit_sync_event
        # Reuse existing slack notifier; include summary if preset_text provided
        payload = {'provider': context.get('provider'), 'summary': {'count': context.get('count')}}
        if self.preset_text:
            payload['summary'] = {'text': self.preset_text}
        try:
            emit_sync_event(db, integration_id, event, payload)
        except Exception:
            pass


class WebhookHook(Hook):
    def __init__(self, url: str, template: str | None = None, headers: Dict[str, str] | None = None):
        self.url = url
        self.template = template
        self.headers = headers or {}

    def run(self, *, db, integration_id: int, event: str, context: Dict[str, Any]):
        from .notifier import send_webhook
        body: Dict[str, Any]
        if self.template:
            try:
                text = self.template.format(**context)
                body = {'text': text, 'event': event, 'integration_id': integration_id}
            except Exception:
                body = {'event': event, 'integration_id': integration_id, 'context': context}
        else:
            body = {'event': event, 'integration_id': integration_id, 'context': context}
        try:
            send_webhook(self.url, body, headers=self.headers)
        except Exception:
            pass


class EmailHook(Hook):
    def __init__(self, to: str, subject_template: str, body_template: str):
        self.to = to
        self.subject_template = subject_template
        self.body_template = body_template

    def run(self, *, db, integration_id: int, event: str, context: Dict[str, Any]):
        from .notifier import send_email
        try:
            subj = self.subject_template.format(**context)
            body = self.body_template.format(**context)
        except Exception:
            subj = f"LifeRPG {event} for integration {integration_id}"
            body = str(context)
        try:
            send_email(self.to, subj, body)
        except Exception:
            pass


class HookManager:
    def __init__(self, hooks_config: Dict[str, Any] | None):
        self.cfg = hooks_config or {}

    def _build_hooks(self, items: List[Dict[str, Any]]) -> List[Hook]:
        hooks: List[Hook] = []
        for it in items or []:
            typ = (it.get('type') or '').lower()
            if typ == 'slack':
                hooks.append(SlackHook(preset_text=it.get('text')))
            elif typ == 'webhook':
                hooks.append(WebhookHook(url=it.get('url', ''), template=it.get('template'), headers=it.get('headers')))
            elif typ == 'email':
                hooks.append(EmailHook(to=it.get('to', ''), subject_template=it.get('subject', 'LifeRPG {event}'), body_template=it.get('body', '{context}')))
        return hooks

    def run_pre(self, *, db, integration_id: int, context: Dict[str, Any]):
        pre = self._build_hooks(self.cfg.get('pre_sync', []))
        for h in pre:
            try:
                h.run(db=db, integration_id=integration_id, event='pre_sync', context=context)
            except Exception:
                continue

    def run_post(self, *, db, integration_id: int, status: str, context: Dict[str, Any]):
        # Filter post hooks by 'on' condition (success, fail, always)
        items = self.cfg.get('post_sync', [])
        selected: List[Dict[str, Any]] = []
        for it in items:
            on = (it.get('on') or 'always').lower()
            if on == 'always' or (on == 'success' and status == 'success') or (on == 'fail' and status != 'success'):
                selected.append(it)
        post = self._build_hooks(selected)
        ev = 'post_sync_success' if status == 'success' else 'post_sync_fail'
        for h in post:
            try:
                h.run(db=db, integration_id=integration_id, event=ev, context=context)
            except Exception:
                continue


def hooks_for_integration(db, integration_id: int) -> HookManager:
    # Load hooks config from Integration.config.hooks
    from . import models
    integ = db.query(models.Integration).filter_by(id=integration_id).first()
    cfg = {}
    if integ and integ.config:
        try:
            import json as _json
            cfg = _json.loads(integ.config) or {}
        except Exception:
            cfg = {}
    return HookManager(cfg.get('hooks'))
