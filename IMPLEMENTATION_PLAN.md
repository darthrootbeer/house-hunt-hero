## Implementation Plan

### Repo Structure (proposed)
- `src/`
  - `ingestion/` source adapters + registry
  - `normalization/` canonical schema + mappers
  - `dedupe/` Zillow/Redfin checks + fuzzy matching
  - `classify/` rule + AI scoring
  - `alerting/` email + Pushover
  - `storage/` SQLite + cache helpers
  - `scheduler/` orchestration entrypoint
  - `utils/` shared helpers
- `configs/` user-editable YAML configs
- `examples/` example payloads
- `state/` local state (ignored in git)
- `scripts/` one-off utilities
- `.github/workflows/` GitHub Actions schedule

### Key Modules
- `ingestion.adapters.*` one file per source
- `ingestion.registry` enable/disable sources
- `normalization.schema` canonical listing model
- `dedupe.zillow_redfin` lookup + cache
- `classify.scoring` rule + AI scoring pipeline
- `alerting.dispatch` email + Pushover dispatch
- `scheduler.run` main orchestration loop
- `storage.state` SQLite read/write

### External Dependencies (explicit list)
- `requests` HTTP fetch
- `beautifulsoup4` HTML parsing
- `feedparser` RSS ingestion
- `playwright` headless browser for JS-heavy pages (optional)
- `rapidfuzz` fuzzy matching
- `pydantic` data models + validation
- `pyyaml` YAML config parsing
- `litellm` model swapping for AI scoring (optional)

### Example Config Files (included)
- `configs/sources.example.yaml`
- `configs/alerts.example.yaml`
- `configs/runtime.example.yaml`
- `house_profile.example.yaml`

### Example Alert Payload (included)
- `examples/alert_payload.example.json`
