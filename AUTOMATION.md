## Automation & Deployment

### Goal
Run fully automated checks every 5–15 minutes, cache state, and avoid duplicate alerts.

### Runtime
- **GitHub Actions:** A scheduled workflow triggers the run on a fixed interval.
- **Local fallback:** Optional cron for local testing.

### Schedule
- Default cadence: every 10 minutes.
- Acceptable range: 5–15 minutes depending on source rate limits.

### State & Caching
**Why:** A job run is stateless by default, so we must persist what we have already seen to avoid duplicate alerts.

**Default storage:**
- `state/state.db` (SQLite)
- Cached between runs using GitHub Actions cache.

**Alternative storage (optional):**
- JSON files in `state/`
- S3-compatible object storage

### Dedupe & Alert Suppression
- Store a stable listing hash and first-seen timestamp.
- Suppress re-alerts within a configurable window (default: 7 days).
- Keep a lightweight log of alert outcomes.

### Failure Behavior
- If a source fails, continue with other sources.
- If AI scoring fails, fall back to rule-based filters.
- Alerts only fire when a listing meets profile + status + score rules.

### Observability
- Write logs to stdout for GitHub Actions logs.
- Summarize counts: total fetched, normalized, deduped, alerted.
