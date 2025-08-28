# LifeRPG Modernization Roadmap

This roadmap prioritizes work to modernize LifeRPG into a cross-platform, integrations-capable, security-focused habit-tracking "level-up" system.

Prioritization legend:
- Priority: P1 (high), P2 (medium), P3 (low)
- Effort: S (1-3 days), M (1-2 weeks), L (2-6 weeks)

Milestone 1 — Core rewrite & cross-platform skeleton (P1, S → M)
- Goal: Create a maintainable API backend, web frontend, and PWA shell.
- Tasks:
  - Scaffold backend API (initial: lightweight stdlib server; target: FastAPI) — Effort: S
  - Scaffold React frontend + Vite + PWA manifest — Effort: S
  - Add Dockerfiles and docker-compose for local dev — Effort: S
  - Add CI skeleton (lint/test/build) — Effort: S
- Success criteria: repo contains runnable dev skeleton and CI passes basic checks.

Milestone 2 — Data model & persistence (P1, M)
- Goal: Design DB schema and migration strategy.
- Tasks:
  - Draft ER: Users, Profiles, Projects, Habits, Logs, Achievements, Integrations, ChangeLog — Effort: S
  - Implement migrations + ORM (e.g., SQLAlchemy/Alembic or Diesel/Golang) — Effort: M
  - Add encrypted backups and export/import — Effort: S
- Success criteria: migrations run and basic entities can be persisted.

Milestone 3 — Auth, security, and infra (P1, M)
- Goal: Secure auth and deployment-ready infra.
- Tasks:
  - Implement OAuth2/OIDC login with PKCE and refresh tokens — Effort: M
  - Secure storage for tokens (Keystore/Keychain) — Effort: M
  - Add 2FA (TOTP) and account hardening — Effort: M
  - Add security middleware (CSP, HSTS, secure cookies) — Effort: S
- Success criteria: secure login flows and CI security checks enabled.

Milestone 4 — Integrations platform (P1, M → L)
- Goal: Add Google Calendar, Todoist, GitHub, Slack integrations.
- Tasks:
  - Build pluggable adapter interface + webhook receiver — Effort: S
  - Implement Google Calendar adapter (OAuth + sync) — Effort: M
  - Implement Todoist adapter and sample sync — Effort: M
  - Add rate-limited worker queue for background sync (Redis/RQ/RabbitMQ) — Effort: M
- Success criteria: successful demo sync for at least Google Calendar.

Milestone 5 — Mobile & offline (P2, M)
- Goal: Provide Android support and offline-first experience.
- Tasks:
  - Implement PWA caching + background sync — Effort: S
  - Optionally scaffold React Native / Flutter app with local DB sync — Effort: M
  - Implement conflict resolution strategy and sync indicators — Effort: M
- Success criteria: PWA installable on Android with offline tasks and sync.

Milestone 6 — Gamification & analytics (P2, M)
- Goal: Rebuild gamification engine and analytics dashboard.
- Tasks:
  - Implement XP/levels, achievements, streaks model — Effort: S
  - Add analytics endpoints and frontend charts (heatmap, time series) — Effort: M
  - Add opt-in anonymized telemetry — Effort: S
- Success criteria: visible progress UI and charts in frontend.

Milestone 7 — Extensibility and portfolio polish (P3, M → L)
- Goal: Plugins, documentation, security portfolio artifacts.
- Tasks:
  - Add plugin system (sandbox with WASM or Lua) — Effort: L
  - Add thorough docs, CONTRIBUTING, CODE_OF_CONDUCT, architecture guides — Effort: M
  - Add security writeups, SBOM, CI SAST scans, and demo accounts — Effort: M
- Success criteria: repo is ready for public demo with documentation and security artifacts.

Roadmap timeline (example pace: solo maintainer ~10 hrs/week):
- Month 0 (weeks 0–2): Milestone 1
- Month 1 (weeks 3–6): Milestone 2 + start Milestone 3
- Month 2 (weeks 7–10): Finish Milestone 3
- Month 3–4: Milestone 4
- Month 5: Milestone 5
- Month 6: Milestone 6
- Months 7+: Milestone 7 and polish

Risks & mitigations:
- Third-party API rate limits — use queued workers and backoff.
- OAuth complexity on mobile — use PKCE and server-side token exchange patterns.
- Privacy/regulatory requirements — provide E2EE option and clear privacy policy.

Deliverables created in this commit:
- Minimal scaffold for backend and frontend
- `ROADMAP.md` (this file)

