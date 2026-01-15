# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Development Philosophy: MVP-First, Low-Complexity

**Core Principle:** Build the smallest, simplest system that fully achieves the stated goal.

### Philosophy
- Prefer working functionality over architectural elegance
- Do not introduce abstractions, extensibility, or optimization unless required for the current goal
- Before adding complexity, explicitly justify why a simpler approach cannot meet the requirement

### Operational Constraints

1. **YAGNI Check** - If a feature, abstraction, or configuration is not required for the current goal, do not implement it. Ask: "Is this required for the current goal?" If no, skip it.

2. **KISS Baseline** - Choose the simplest design that works end-to-end. Fewer files, fewer layers, fewer concepts beats "clean" architecture. Prefer single files over multiple modules, linear code over abstractions.

3. **Tracer Bullet First** - Build a thin, end-to-end path that proves the system works (inputs → processing → outputs) before improving structure or robustness.

4. **One-Way Door Rule** - Only introduce hard-to-undo decisions (schemas, frameworks, infrastructure) after the MVP path is validated.

5. **Bungalow Test** - If the solution resembles a city (multiple services, plugins, abstractions), replace it with a bungalow (single module, linear flow, direct logic) unless scaling is explicitly required.

6. **Complexity Budget** - Each new concept must either enable the core goal or remove more complexity than it adds.

7. **Refactor Later, Not Now** - Code may be "ugly but correct" during MVP. Cleanup only after success criteria are met.

### Success Criteria
- ✅ The core goal is met at 100%
- ✅ The codebase is understandable in one sitting
- ✅ Removing any major part would break required functionality

---

## TODO System

### Structure
- `TODO.md`: Master list (human-scannable)
- `TODO/<hex-id>.md`: AI-optimized task specs
- Every `TODO.md` item must link to a detail file

### Hex ID Generation
- 6-character uppercase hex: `A1B2C3`, `FF00A9`, etc.
- Generate randomly, verify uniqueness against existing `TODO/` files
- Never reuse IDs

### Task File Format
```yaml
---
id: <HEX>
status: pending|active|done
deps: [<hex>, <hex>]
files: [paths]
---
::context
<why>

::done-when
- criterion

::steps
1. step

::avoid
- exclusion

::notes
<gotchas>
```

### Operations
- **Add TODO**: Generate hex ID → Add to `TODO.md` under Active → Create `TODO/HEX.md`
- **Start TODO**: Move to "In Progress" in `TODO.md` → Set `status: active`
- **Complete TODO**: Move to "Completed" in `TODO.md` → Set `status: done`

### When Working on a Task
1. Load `TODO/<id>.md`
2. Parse all sections
3. Verify deps are complete
4. Follow `::steps` exactly
5. Respect `::avoid` boundaries
6. Confirm all `::done-when` criteria met before marking done

---

## Protected Paths

Never delete the `.cursor` folder from this project. It may be excluded from git, but must remain on disk.

---

## Project Overview

House Hunt Hero is an early-market real estate discovery system that finds listings before they appear on Zillow/Redfin and sends immediate alerts. The system runs on a scheduled loop (every 10 minutes via GitHub Actions) to continuously monitor multiple public sources.

## Core Commands

### Running the system
```bash
# Run a single cycle locally (for testing)
python scripts/run.py

# Install dependencies
python -m pip install -r requirements.txt
```

### Automation
The system is designed to run via GitHub Actions on schedule (every 10 minutes). See `.github/workflows/house-hunt-hero.yml`.

## Architecture

The codebase follows a **5-layer pipeline architecture** where data flows sequentially through each stage:

### 1. Ingestion Layer (`src/ingestion/`)
- **Purpose**: Fetch raw listings from multiple public sources
- **Key files**:
  - `base.py`: Defines `IngestionAdapter` base class and `RawListing` dataclass
  - `registry.py`: Returns list of enabled adapters via `get_adapters()`
  - `adapters/`: One file per source (e.g., `craigslist_owner.py`)
- **Adding a new source**: Create a new adapter in `src/ingestion/adapters/` that inherits from `IngestionAdapter` and register it in `registry.py`

### 2. Normalization Layer (`src/normalization/`)
- **Purpose**: Convert all raw listings into a single canonical schema
- **Key files**:
  - `schema.py`: Defines `Listing`, `Address`, and `Geo` models (Pydantic)
  - `mapper.py`: Contains `normalize_many()` which converts `RawListing` → `Listing`
- **Schema fields**: `listing_id`, `source`, `source_timestamp`, `listing_url`, `address`, `geo`, `price`, `description_raw`, `image_urls`, `seller_type`, `keywords_detected`

### 3. Deduplication Layer (`src/dedupe/`)
- **Purpose**: Check if listings already exist on Zillow/Redfin
- **Key file**: `zillow_redfin.py` - `check_listing_status()` returns one of: `"off_market"`, `"pre_zillow"`, `"already_public"`
- **Strategy**: Address + fuzzy matching to identify duplicates

### 4. Classification Layer (`src/classify/`)
- **Purpose**: Score listings against the user's house profile using AI
- **Key file**: `scoring.py` - `score_listing()` returns a dict with `confidence` and `reasons`
- **Config**: AI provider/model specified in `configs/runtime.example.yaml` under `ai:` section

### 5. Alerting Layer (`src/alerting/`)
- **Purpose**: Send notifications via email and Pushover
- **Key file**: `dispatch.py` - `dispatch_alert()` sends to all configured channels
- **Alert conditions**: Defined in `src/scheduler/run.py:_should_alert()` - checks status requirements and minimum confidence threshold

### Orchestration (`src/scheduler/`)
- **Main entry point**: `run.py:run_once()` executes one complete cycle through all layers
- **Called by**: `scripts/run.py` (local testing) or GitHub Actions workflow

### State Management (`src/storage/`)
- **File**: `state.py` - `StateStore` class wraps SQLite operations
- **Database**: `state/state.db` (SQLite)
- **Tables**:
  - `seen_listings`: Tracks listing IDs to prevent duplicate processing
  - `alerts`: Records when alerts were sent
- **Critical methods**: `has_seen()`, `mark_seen()`, `record_alert()`

### Configuration (`configs/`)
- `sources.example.yaml`: Which sources to check, rate limits, regions
- `runtime.example.yaml`: Schedule, alerting rules, AI config, storage settings
- `alerts.example.yaml`: Notification channel configuration
- `house_profile.json`: User's buying criteria for scoring

### Utilities (`src/utils/`)
- `config.py`: Contains `load_yaml()` helper for loading YAML config files

## Data Flow

```
Raw sources → Ingestion adapters → Normalize → Dedupe check → AI scoring → Alert dispatch
                                                    ↓
                                            StateStore (SQLite)
                                         (prevent duplicate alerts)
```

## Implementation Notes

### Two implementations coexist
- **MVP (consolidated)**: `house_hunt.py` - Single-file implementation with all logic inline
- **Modular**: `src/` directory - Production architecture with proper separation of concerns
- When adding features, modify the `src/` structure, not `house_hunt.py`

### Listing ID format
Listings are uniquely identified by: `"{source}:{listing_url}"`

### Adapter pattern
Each source adapter must:
1. Inherit from `IngestionAdapter` (`src/ingestion/base.py`)
2. Set a `source_id` class attribute
3. Implement `fetch() -> List[RawListing]`
4. Be registered in `src/ingestion/registry.py:get_adapters()`

### Environment variables
Email and Pushover credentials should be stored as environment variables (not committed to the repo).

### GitHub Actions caching
The workflow caches `state/state.db` between runs to maintain deduplication state across scheduled executions.
