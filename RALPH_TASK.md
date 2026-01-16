---
task: Complete remaining property source implementations, alerting, and testing
test_command: "python scripts/run.py"
hex_id: FC7E1E
---

# Task: Complete Remaining Property Source Implementations

This task encompasses the remaining work to expand property search coverage, implement alerting, and create comprehensive testing.

## Success Criteria

### Medium Priority Sources

1. [x] [FC7E1E](TODO/FC7E1E.md) - Implement commercial real estate sites (5 platforms, focus on multi-family)
   - All 5 commercial platforms have adapters implemented
   - Source configs created with property_type_filters (multi-family focus)
   - Registered in `src/ingestion/registry.py`
   - Each adapter tested with actual Maine searches, focusing on multi-family properties
   - Test results documented (listings found, data quality, selector accuracy, multi-family filtering)

### Lower Priority Sources

2. [x] [9F80BF](TODO/9F80BF.md) - Implement national aggregators (Zillow, Realtor.com, Redfin, Trulia, Homes.com)
   - All 5 national aggregators have adapters implemented
   - Source configs created with rate_limits and anti-bot measures
   - Registered in `src/ingestion/registry.py`
   - Each adapter tested with actual Maine location searches and verified to retrieve listings successfully
   - Test results documented (listings found, data quality, selector/API accuracy, rate limit compliance)

3. [x] [FC180C](TODO/FC180C.md) - Implement land-specific sites (5 platforms: LandSearch, KW Land, etc.)
   - All 5 land platforms have adapters implemented
   - Source configs created with filters (structures, houses, not raw land)
   - Registered in `src/ingestion/registry.py`
   - Each adapter tested with actual Maine searches, filtering for properties with structures
   - Test results documented (listings found, data quality, selector accuracy, structure filtering)

### Alerting

4. [x] [B7C8D9](TODO/B7C8D9.md) - Implement email alerting - Send real alerts via SMTP
   - SMTP email sending works with config in `configs/alerts.example.yaml`
   - Handles auth and TLS correctly
   - Sends formatted alert payloads as email body
   - Tested with real SMTP server

5. [x] [E1F2A3](TODO/E1F2A3.md) - Implement Pushover alerting - Mobile push notifications
   - Pushover API integration works with config in `configs/alerts.example.yaml`
   - Sends formatted alerts to mobile devices
   - Handles API errors gracefully
   - Tested with real Pushover account

### Testing & Quality

6. [x] [E8F9A0](TODO/E8F9A0.md) - Test all 49 active platforms and generate readable report
   - Test script created that tests all 49 platforms from registry
   - Each platform search executes and collects results
   - Report generated in plain language (no technical jargon) showing:
     - Executive summary with counts
     - Results organized by category
     - Platform details (status, properties found, sample listings)
     - Issues and recommendations
   - Report saved to `reports/platform_test_report.md`

### Final Verification

7. [x] End-to-end test: `python scripts/run.py` successfully fetches listings from all implemented sources
8. [x] All adapters registered in `src/ingestion/registry.py`
9. [x] All source configs created in `configs/sources/` with appropriate configuration

## Implementation Approach

### For Commercial Real Estate (FC7E1E):
- Research each platform: check for API, search functionality
- Check GitHub for commercial real estate scrapers
- Create adapters with multi-family property filtering
- Create source configs with: search_urls, listing_selectors, property_type_filters (multi-family focus)
- Test each adapter immediately after implementation with Maine searches focusing on multi-family properties

### For National Aggregators (9F80BF):
- Research each platform: check for API access, public search URLs
- Check GitHub for existing scrapers (many exist for Zillow/Realtor.com/Redfin)
- Research rate limits and anti-bot measures
- Create adapters with rate limiting and stealth browser settings
- Create source configs with: search_urls, listing_selectors, api_endpoints (if available), rate_limits
- Test each adapter with Maine location searches, respecting rate limits

### For Land Sites (FC180C):
- Research each platform: check for API, search functionality
- Check GitHub for land listing scrapers
- Create adapters with structure filtering (exclude raw land)
- Create source configs with: search_urls, listing_selectors, filters (structures, houses, not raw land)
- Test each adapter with Maine searches, filtering for properties with structures

### For Email Alerting (B7C8D9):
- Add SMTP config to `configs/alerts.example.yaml`
- Implement `send_email()` with smtplib in `src/alerting/dispatch.py`
- Format alert payload as email body
- Handle auth and TLS correctly
- Test with real SMTP server

### For Pushover Alerting (E1F2A3):
- Add Pushover config to `configs/alerts.example.yaml`
- Implement `send_pushover()` with requests in `src/alerting/dispatch.py`
- Format alert payload for Pushover API
- Handle API errors gracefully
- Test with real Pushover account

### For Platform Testing (E8F9A0):
- Create test script that imports all adapters from registry
- For each adapter: run fetch(), collect listings, record timing
- Validate listings have required fields (title, url, source)
- Categorize results: Working/Empty/Problem/NeedsAttention
- Generate markdown report with plain language (no tech jargon)
- Follow PLATFORM_TEST_PLAN.md structure
- Save report to `reports/platform_test_report.md`

## Testing Protocol

For each adapter, immediately after implementation:
- Run `adapter.fetch()` with actual Maine property searches
- Verify listings are retrieved (check count > 0 if listings exist)
- Inspect RawListing objects: verify source_id, listing_url, title, raw_payload populated
- Verify listing_urls are absolute and valid
- Check that selectors/API correctly extract property details, price, location
- Test with different search parameters if applicable
- Document any API/auth issues, selector problems, or data quality problems
- Refine config/implementation if listings are not retrieved correctly

## Constraints

- Avoid paid MLS access fees
- Avoid requiring realtor credentials
- Avoid login-required sections
- Use simplest working method (YAGNI principle)
- For sources without public listings, document `contact_required: true` in config
- Don't over-engineer per-brokerage if structures are similar (use base adapter with config-driven selectors)
- Respect rate limits for national aggregators
- Use environment variables for credentials (SMTP, Pushover API keys)
- Focus on multi-family properties for commercial sites (exclude pure commercial)
- Filter out raw land without structures for land sites

## Ralph Instructions

1. Work on the next incomplete criterion (marked [ ])
2. Check off completed criteria (change [ ] to [x])
3. Run tests after changes: `python scripts/run.py`
4. Commit your changes frequently
5. When ALL criteria are [x], output: `<ralph>COMPLETE</ralph>`
6. If stuck on the same issue 3+ times, output: `<ralph>GUTTER</ralph>`
