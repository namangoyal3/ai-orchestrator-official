# TODOS

## Add test suite
**What:** pytest suite for analytics endpoints + Jest tests for dashboard loading logic and KeySetupModal.

**Why:** Zero tests currently. Any change to analytics SQL queries, the Promise.allSettled dashboard fetch, or the API key modal can break silently with no verification signal.

**Pros:** Confidence when refactoring; catches the SQLite vs PostgreSQL dialect issue class early; CI gates for future PRs.

**Cons:** ~1 day of work; needs test DB setup for backend.

**Context:** The `func.date()` fix (replacing `func.strftime`) was caught in code review, not by a test. The dashboard uses `Promise.allSettled` now but there's no test verifying that a single endpoint failure doesn't cascade. `KeySetupModal` relies on `localStorage` which needs a mock in Jest.

**Where to start:**
- `backend/tests/test_analytics.py` — test `GET /v1/analytics/timeseries` returns 200 on both SQLite and a mock PG connection
- `frontend/__tests__/dashboard.test.tsx` — test that when one of the 5 `Promise.allSettled` calls rejects, the other 4 still set state

**Depends on:** Nothing — can be added after the demo sprint.

**Priority:** P1 (after YC demo)
