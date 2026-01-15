# Source Configuration Directory

This directory contains individual configuration files for each property listing source.

## Structure

Each source should have its own YAML configuration file following the template in `.template.yaml`.

## Naming Convention

Use lowercase with underscores: `source_name.yaml`
- Examples: `ownerama.yaml`, `zillow.yaml`, `maine_community_bank.yaml`

## Configuration Process

For each source, follow this process:

1. **Research** - Check for API, RSS feeds, public search URLs
2. **GitHub Search** - Look for existing scrapers/libraries
3. **Tool Testing** - Test Playwright, requests+BeautifulSoup, Selenium, etc.
4. **Create Config** - Copy `.template.yaml` and fill in source-specific details
5. **Implement Adapter** - Create adapter in `src/ingestion/adapters/`
6. **Test** - Verify listing retrieval works
7. **Document** - Add notes about gotchas, rate limits, etc.

## Configuration Fields

### Required
- `source_id` - Must match adapter's `source_id` attribute
- `label` - Human-readable name
- `enabled` - Boolean to enable/disable source
- `method` - One of: "api", "playwright", "requests", "rss", "selenium", "contact_required"
- `base_url` - Base URL for the source

### Method-Specific
- **API**: `api.endpoint`, `api.auth_type`, `api.auth_config`
- **Scraping**: `scraping.listing_container_selector`, `scraping.listing_url_selector`, etc.
- **RSS**: `rss.feed_url`, `rss.item_selector`

### Optional
- `filters` - Location, property types, price ranges
- `rate_limit_seconds` - Minimum delay between requests
- `contact_required` - Info if source requires direct contact
- `github_solutions` - Reference to found solutions
- `tools_tested` - Record of what worked/didn't work
- `notes` - Gotchas and important information

## Loading Configs

Source configs are loaded by the ingestion system and used to:
- Configure adapter behavior
- Set rate limits
- Provide selectors for scraping
- Store API credentials (via environment variables)

## Best Practices

1. **Store credentials in environment variables**, not in config files
2. **Document anti-bot measures** and how they're handled
3. **Record rate limits** accurately to avoid getting blocked
4. **Note GitHub solutions** that were evaluated or used
5. **Test tools** and document what works best
6. **Include gotchas** in notes section
