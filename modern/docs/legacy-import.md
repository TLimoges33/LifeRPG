# Legacy import (AHK) plan

The classic LifeRPG AHK app can export data (habits, projects, logs). This document outlines a basic import approach for the modern backend.

Scope (phase 1):
- Accept a JSON export shaped as:
  ```json
  { "habits": [{"title":"...","notes":"...","cadence":"once","status":"active"}],
    "projects": [{"title":"...","description":"..."}],
    "logs": [{"habit_title":"...","action":"completed","timestamp":"2025-08-28T12:00:00Z"}] }
  ```
- Map to current schema: create Projects, Habits, and Logs for the authenticated user.
- Provide an admin endpoint to upload and import.

Future:
- Write a converter for AHK-specific export formats (CSV/INI) into the JSON shape above.
- Support incremental merge with duplicate detection by title + timestamps.
