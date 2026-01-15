## Product Requirements Document (PRD)

### 1. Problem Statement
Home listings often show up on Zillow or Redfin late. That delay means a buyer can miss early deals. This product uses automation to spot listings that are either off-market or appear earlier elsewhere. The goal is to create a real-time advantage by being first to see new opportunities.

### 2. Success Criteria
- **Beat Zillow/Redfin:** Identify listings before they appear on Zillow or Redfin; track and report this as the core KPI (a KPI is a measurable success goal).
- **Fast alerts:** Send alerts within minutes of discovery, not hours.
- **High quality:** Prefer precision over recall—false positives are acceptable but should be minimized.

### 3. User Persona
- Technically advanced buyer.
- Comfortable with GitHub, command line tools, and editing YAML/JSON.
- Wants alerts and actionable links, not dashboards.

### 4. Out of Scope
- Any UI or frontend.
- Manual data entry or manual review queues.
- Paid, credentialed, or proprietary MLS data feeds.

### 5. Ethical & Legal Constraints
- Respect robots.txt where applicable.
- No credentialed scraping or use of private accounts.
- Only public, owner-posted, or openly accessible data.

### 6. Product Goals
- Maximize early discovery and coverage across diverse sources.
- Minimize noise through lightweight filtering and clear relevance scoring.
- Keep the system modular so sources can be added or removed easily.

### 7. Non-Goals
- Perfect matching or complete market coverage.
- Polished UX or user onboarding flows.

### 8. Risks & Mitigations
- **Source instability:** Sites may change structure. Mitigation: modular adapters and quick swaps.
- **False positives:** Noisy sources (like classifieds) can be messy. Mitigation: strict filters and AI-assisted classification that can fail open.
- **Compliance:** Some sources may restrict access. Mitigation: enforce public-only rules and robots.txt checks.

### 9. Dependencies
- Open-source scrapers for target sources where available.
- Reliable notification services (Email, Pushover).
- Lightweight storage for state and deduplication.
