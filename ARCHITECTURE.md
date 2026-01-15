## System Architecture

### Overview (How data moves)
1. **Ingestion** pulls new listings from many public sources.
2. **Normalization** converts raw data into one clean, consistent format.
3. **De-duplication** checks Zillow/Redfin and marks status.
4. **AI classification** scores relevance and filters noise.
5. **Alerting** notifies the user immediately.

This is designed to be fast, modular, and easy to extend.

---

## 1. Source Ingestion Layer
**Goal:** Collect listings quickly from many public sources.

**Approach (plain language):** Each source has a small adapter. The adapter fetches raw listings, then hands them to the normalization layer.

**Priority sources (initial list):**
- FSBO platforms (public listings only)
- Craigslist (housing + owner)
- Facebook Marketplace (public listings only)
- Realtor.com / Realtor.ca (public pages)
- Regional and niche listing sites
- Auction / estate / probate listing sites
- RSS feeds (when offered)

**Implementation notes:**
- Use existing open-source scrapers when stable.
- Prefer low-friction tooling: `requests`, `BeautifulSoup`, RSS readers.
- Use `Playwright` only when needed for JavaScript-heavy pages.
- Each adapter returns a list of raw listings with source metadata.
- Easy add/remove: one adapter file per source, a registry file to enable/disable.

---

## 2. Normalization Layer
**Goal:** Convert raw listings into a single canonical schema.

**Canonical listing fields:**
- `address_raw`
- `address_structured` (street, city, state, zip)
- `geo` (lat, lon if available)
- `price` (number or `null`)
- `source` and `source_timestamp`
- `listing_url`
- `description_raw`
- `image_urls` (URLs only)
- `seller_type` (fsbo, agent, unknown)
- `keywords_detected` (pre-MLS, estate, off-market, etc.)

**Rules:**
- Preserve raw text for later analysis.
- Keep timestamps in ISO 8601.
- Normalize money to integers (USD cents or whole dollars).

---

## 3. Zillow / Redfin De-Duplication Layer
**Goal:** Identify listings not yet visible on Zillow/Redfin.

**How it works (plain language):** We compare listings by address and fuzzy text, then look up Zillow/Redfin to see if they already have the same place. We save what we’ve already seen to avoid repeats.

**Core behaviors:**
- Use address + fuzzy matching for near-duplicates.
- Cache known Zillow/Redfin listings for fast checks.
- Set a status flag:
  - `off_market` (not found)
  - `pre_zillow` (found later)
  - `already_public` (already on Zillow/Redfin)

---

## 4. AI Classification & Filtering Layer
**Goal:** Score relevance and reduce noise without slowing ingestion.

**Use cases:**
- Relevance scoring against the house profile.
- Keyword inference (estate sale, probate, off-market hints).
- Filter rentals, scams, or miscategorized posts.

**Rules:**
- Prompt-driven and configurable.
- Model-agnostic (OpenAI / Anthropic / local).
- Never block ingestion if the AI fails; fall back to rule-based filters.

---

## 5. Alerting & Notification Layer
**Goal:** Notify immediately when a high-confidence early listing appears.

**Trigger conditions:**
- Matches house profile.
- Status is `off_market` or `pre_zillow`.
- Confidence score exceeds threshold.

**Channels:**
- Email
- Pushover

**Alert payload:**
- Source
- Why it triggered
- Confidence score
- Direct link
- Timestamp of first discovery

---

## Storage & State
**Goal:** Avoid duplicate alerts and track discovery timing.

**Lightweight options:**
- SQLite (default)
- JSON files
- S3-like object store (optional)

**Stored data:**
- Seen listing IDs (per source)
- Normalized listing records
- Zillow/Redfin snapshots for dedup
- Last alert timestamps

---

## Scheduling & Automation
**Goal:** Run every 5–15 minutes with minimal overhead.

**Primary:**
- GitHub Actions on a schedule.

**Backup (local/dev):**
- Cron for local runs.

---

## Modularity & Extensibility
- One adapter per source.
- One schema definition for all listings.
- Pluggable AI models and notification methods.
- Clear interfaces between layers to reduce coupling.
