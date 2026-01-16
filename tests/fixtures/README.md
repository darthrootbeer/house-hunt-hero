# Test Fixtures

This directory contains HTML fixtures for testing property listing adapters without requiring network access.

## Structure

- `html/` - HTML fixtures simulating property listing pages from various platforms

## HTML Fixtures

Each HTML fixture file represents a platform's listing page structure with mock property data.

### Naming Convention

`{platform_id}.html` - HTML page with 5-10 mock property listings

### Content Guidelines

- Use realistic Maine addresses (e.g., "123 Main St, Portland, ME 04101")
- Include variety of property types: houses, land with structures, commercial
- Include edge cases: missing price, missing beds/baths, special characters in titles
- Keep file size under 50KB
- Do NOT use real property data (privacy concerns)
- Structure should match the platform's actual HTML, but with mock data

### Platform Categories Covered

1. **MLS Services** - maine_listings, maine_state_mls
2. **Brokerages** - realty_of_maine, landing_real_estate
3. **FSBO Platforms** - ownerama, brokerless, fsbo_com
4. **Classifieds** - craigslist_owner, town_ads

## Usage

These fixtures are used by `tests/test_adapters_with_mock_data.py` to test adapter parsing logic:

```python
from pathlib import Path

html_content = Path('tests/fixtures/html/maine_listings.html').read_text()
# Test adapter parsing on html_content
```

## Updating Fixtures

When platform HTML structures change:

1. Capture new HTML structure using browser inspector or diagnostics
2. Update fixture file with new structure
3. Verify adapters still extract data correctly
