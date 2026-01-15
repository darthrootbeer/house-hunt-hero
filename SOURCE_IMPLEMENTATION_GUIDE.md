# Source Implementation Guide

This guide explains how to implement new property listing sources for House Hunt Hero.

## Overview

Each source requires:
1. **Research** - Understanding how to access the source
2. **Configuration** - YAML file in `configs/sources/`
3. **Adapter** - Python class in `src/ingestion/adapters/`
4. **Registration** - Add to `src/ingestion/registry.py`

## Implementation Process

### Step 1: Research the Source

For each source, follow this research process:

1. **Check for API**
   - Look for official API documentation
   - Check for public endpoints
   - Look for API keys/authentication requirements

2. **Check GitHub**
   - Search for existing scrapers: `github.com search: "site-name scraper"`
   - Look for libraries that might help
   - Review how others have solved similar problems

3. **Test Tools**
   - **Playwright** - Best for JavaScript-heavy sites, anti-bot measures
   - **requests + BeautifulSoup** - Fastest for static HTML
   - **Selenium** - Alternative to Playwright (heavier)
   - **RSS/Feedparser** - If site has RSS feeds
   - **API libraries** - If official API exists

4. **Document Findings**
   - Record what works and what doesn't
   - Note rate limits and anti-bot measures
   - Document any gotchas

### Step 2: Create Source Configuration

Create a YAML file in `configs/sources/` following the template:

```yaml
source_id: "ownerama"
label: "Ownerama - FSBO Listings"
enabled: true
method: "playwright"  # or "api", "requests", "rss", "selenium"
base_url: "https://ownerama.com"
search_url: "https://ownerama.com/search?state=ME"
# ... (see configs/sources/.template.yaml for full structure)
```

Key fields:
- **method**: How to retrieve data (playwright, requests, api, rss, etc.)
- **scraping.selectors**: CSS selectors for finding listings
- **rate_limit_seconds**: Minimum delay between requests
- **github_solutions**: Links to solutions you found
- **tools_tested**: What you tried and results

### Step 3: Implement Adapter

Create a new file in `src/ingestion/adapters/` (e.g., `ownerama.py`):

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright
from ..base import IngestionAdapter, RawListing
from ...utils.source_config import load_source_config


class OwneramaAdapter(IngestionAdapter):
    source_id = "ownerama"
    
    def fetch(self) -> List[RawListing]:
        config = load_source_config(self.source_id)
        if not config or not config.get("enabled"):
            return []
        
        listings = []
        # Implementation using config for selectors, URLs, etc.
        # ...
        return listings
```

The adapter should:
- Load its config using `load_source_config()`
- Use config values for URLs, selectors, rate limits
- Follow the `IngestionAdapter` pattern
- Return `List[RawListing]`
- Handle errors gracefully (return empty list on failure)

### Step 4: Register Adapter

Add to `src/ingestion/registry.py`:

```python
from .adapters import OwneramaAdapter

def get_adapters() -> List[IngestionAdapter]:
    return [
        # ... existing adapters
        OwneramaAdapter(),
    ]
```

### Step 5: Test

Test the adapter:
1. Enable it in the config (`enabled: true`)
2. Run `python scripts/run.py`
3. Verify listings are retrieved
4. Check for errors or rate limiting

## Tool Selection Guide

### Use Playwright When:
- Site uses JavaScript to load content
- Anti-bot measures are present
- Site blocks simple HTTP requests
- Dynamic content loading

**Example**: Craigslist, Facebook Marketplace, modern real estate sites

### Use requests + BeautifulSoup When:
- Site serves static HTML
- No JavaScript required
- Simple structure
- Fast scraping needed

**Example**: Simple classifieds, RSS feeds, basic listing pages

### Use API When:
- Official API available
- No scraping needed
- Rate limits are reasonable
- Authentication is straightforward

**Example**: Some MLS systems, modern platforms with APIs

### Use RSS When:
- Site provides RSS/Atom feeds
- Feed contains listing data
- No scraping needed

**Example**: Some auction sites, news-based listings

## Best Practices

1. **Respect Rate Limits**
   - Set appropriate `rate_limit_seconds` in config
   - Add delays between requests
   - Don't overwhelm servers

2. **Handle Errors Gracefully**
   - Return empty list on failure
   - Log errors for debugging
   - Don't crash the entire system

3. **Use Configuration**
   - Don't hardcode URLs or selectors
   - Store everything in config files
   - Make it easy to update without code changes

4. **Document Everything**
   - Add notes in config about gotchas
   - Record what tools were tested
   - Link to GitHub solutions found

5. **Test Thoroughly**
   - Test with real searches
   - Verify listings are retrieved correctly
   - Check for edge cases

## Configuration Structure

See `configs/sources/.template.yaml` for the full configuration structure.

Key sections:
- **Basic info**: source_id, label, enabled, method
- **API config**: If using API
- **Scraping config**: Selectors, pagination, anti-bot measures
- **RSS config**: If using RSS feeds
- **Filters**: Location, property types, price ranges
- **Rate limiting**: Delays between requests
- **Documentation**: GitHub solutions, tools tested, notes

## Current Status

All sources from `Maine_Property_Sources_2026.md` have been added to the TODO list:

### High Priority (TODO items 6929E3 - 31949E)
- FSBO platforms (8 sites)
- Classifieds & newspapers (6 sources)
- Facebook Marketplace & Groups
- Nextdoor
- Bank REO properties (20+ banks)
- Government tax foreclosures
- Auction houses (3 sites)
- Investment/wholesale platforms (6 sites)

### Medium Priority (TODO items 5BEC96 - FC7E1E)
- Maine MLS services (2 sites)
- Maine brokerages (12 sites)
- Credit unions (3 sites)
- Commercial real estate (5 sites)

### Lower Priority (TODO items 9F80BF - FC180C)
- National aggregators (5 sites)
- Land-specific sites (5 sites)

## Next Steps

1. Start with high-priority sources (FSBO platforms)
2. Follow the research → config → adapter → test process
3. Document findings in config files
4. Register and enable sources as they're implemented
