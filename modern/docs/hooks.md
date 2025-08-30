# Hooks configuration

You can configure pre- and post-sync hooks per integration via `Integration.config.hooks`.

Config shape (stored as JSON in `integrations.config`):

```
{
  "hooks": {
    "pre_sync": [
      { "type": "slack", "text": "Sync starting for {provider}" },
      { "type": "webhook", "url": "https://example.com/hook", "template": "{provider} sync started" }
    ],
    "post_sync": [
      { "type": "slack", "on": "success" },
      { "type": "slack", "on": "fail" },
      { "type": "email", "to": "ops@example.com", "subject": "Sync {event}", "body": "{provider} finished with count={count}" },
      { "type": "webhook", "url": "https://example.com/notify", "headers": {"X-Token": "abc"}, "template": "{provider} done: {count}" }
    ]
  }
}
```

Notes:
- `pre_sync` runs before adapter execution.
- `post_sync` supports `on`: `success`, `fail`, or `always` (default).
- Slack hook reuses the Slack notifier. Add a Slack integration with an incoming webhook for messages to deliver.
- Webhook hook posts JSON to the given `url`. If `template` is provided, `{context}` values are formatted into a `text` field.
- Email hook uses the notifier email transport. See `docs/email.md`.

Context variables available to templates:
- `provider`: provider name (e.g., `todoist`)
- `count`: items processed (when available)

Caveats:
- Hooks execute best-effort. Failures are logged and do not block the sync.
- Keep templates simple; invalid placeholders are ignored and the raw context is sent.
