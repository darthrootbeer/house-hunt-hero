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

#### Enhanced Test Diagnostics & Tools

7. [x] [B81B06](TODO/B81B06.md) - Add diagnostic capture to test_all_platforms.py
   - Test script captures screenshots for zero-property platforms
   - Saves HTML snapshots to reports/diagnostics/{adapter_id}/page.html
   - Logs network requests and console errors
   - Records timing metrics (page load, selector wait times)
   - Adds --diagnose flag to enable detailed diagnostics

8. [x] [45DD1A](TODO/45DD1A.md) - Create test_selector_validation.py to test CSS selectors on live pages
   - Test file navigates to platform URLs
   - Tests each selector in adapters against live pages
   - Reports: count of elements found, sample element HTML
   - Flags selectors that find zero elements
   - Compares working vs non-working adapter selector strategies

9. [x] [39D5EA](TODO/39D5EA.md) - Create HTML test fixtures in tests/fixtures/html/
   - HTML fixtures created for all platform types
   - Each fixture contains 5-10 mock property listings
   - Properties use realistic Maine addresses
   - Includes edge cases: missing fields, special characters, long titles

10. [x] [13A1CD](TODO/13A1CD.md) - Create test_adapters_with_mock_data.py for unit testing with HTML fixtures
    - Test file loads HTML fixtures for each adapter
    - Creates mock Playwright page object with fixture HTML
    - Runs adapter's fetch() method with mock page
    - Verifies: properties extracted, correct count, valid URLs/titles
    - Fast execution (no network requests)

11. [ ] [F0C541](TODO/F0C541.md) - Create scripts/inspect_platform.py interactive tool for page inspection
    - Script accepts platform adapter name as argument
    - Navigates to platform URL using Playwright
    - Displays page screenshot and accessibility tree snapshot
    - Tests CSS selectors interactively (shows matched elements)
    - Exports findings for adapter update

12. [ ] [6EDE07](TODO/6EDE07.md) - Create scripts/run_diagnostics.py for batch diagnostic report generation
    - Script accepts platform list or "all-empty" flag
    - Runs enhanced diagnostics on specified platforms
    - Generates diagnostic reports in reports/diagnostics/{adapter_id}/
    - Creates summary report of findings
    - Flags common issues: anti-bot protection, selector mismatch, AJAX loading

#### Platform Fixes (Zero Property Platforms)

13. [ ] [1FC3FD](TODO/1FC3FD.md) - Fix FSBO platforms (7 platforms: ownerama, brokerless, flat_fee_group, etc.)
    - All 7 FSBO platforms finding properties (or documented why not possible)
    - Correct selectors identified via page inspection
    - Adapter code updated with specific selectors
    - Each platform tested independently and verified working
    - Fixes documented with before/after selector comparison

14. [ ] [164AEC](TODO/164AEC.md) - Fix Maine Brokerage platforms (9 platforms: listings_direct, swan_agency, etc.)
    - At least 6 of 9 Maine Brokerage platforms finding properties
    - Correct selectors identified via page inspection
    - Adapter code updated with specific selectors (similar to realty_of_maine pattern)
    - Each working platform tested and verified
    - Fixes documented with selector patterns

15. [ ] [7BD1E6](TODO/7BD1E6.md) - Fix maine_state_mls platform
    - maine_state_mls platform finding properties (or documented why not possible)
    - Correct selectors identified via page inspection
    - Adapter code updated with specific selectors
    - Tested and verified working
    - Fix documented with selector comparison to maine_listings

16. [ ] [706A0E](TODO/706A0E.md) - Fix social platforms (facebook_marketplace, facebook_groups, nextdoor)
    - All 3 social platforms finding properties (or documented authentication/technical blockers)
    - Correct selectors identified via page inspection
    - Authentication handled if required (state save/load)
    - Adapter code updated with specific selectors
    - Each platform tested and verified working

17. [ ] [A551DB](TODO/A551DB.md) - Fix classifieds platforms (oodle, town_ads, sun_journal, etc.)
    - At least 4 of 6 classifieds platforms finding properties
    - Correct selectors identified via page inspection
    - Adapter code updated with specific selectors
    - Each working platform tested and verified
    - Platforms with no listings documented as legitimately empty

#### Documentation & Tracking

18. [ ] [62C966](TODO/62C966.md) - Create reports/platform_status.md to track fixing progress
    - Status tracker file created at reports/platform_status.md
    - All 58 platforms listed with status: ✅ Working | 🔧 In Progress | ⚠️ Needs Fix | ❌ Broken | 📋 Not Started
    - Each platform entry includes: last tested date, issues found, selectors (current vs correct), fix notes
    - Updated after each platform fix

19. [ ] [74CFE6](TODO/74CFE6.md) - Create docs/PLATFORM_FIX_TEMPLATE.md for fix documentation
    - Template file created at docs/PLATFORM_FIX_TEMPLATE.md
    - Template includes: platform name, issue description, diagnostic findings, correct selectors, code changes, test results before/after, notes
    - Template used when fixing each platform
    - Documentation stored in docs/fixes/ or reports/fixes/

### Final Verification

20. [x] End-to-end test: `python scripts/run.py` successfully fetches listings from all implemented sources
21. [x] All adapters registered in `src/ingestion/registry.py`
22. [x] All source configs created in `configs/sources/` with appropriate configuration

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

### For Enhanced Test Diagnostics (B81B06, 45DD1A, 39D5EA, 13A1CD, F0C541, 6EDE07):
- Add diagnostic capture to test script: screenshots, HTML snapshots, network logs, console errors
- Create selector validation test to check if CSS selectors match elements on live pages
- Create HTML test fixtures for platform structure samples (5-10 mock properties each)
- Create unit tests using HTML fixtures to test adapter parsing logic without network access
- Create interactive inspection tool for investigating platform pages and finding selectors
- Create batch diagnostic runner for generating diagnostic reports on multiple platforms

### For Platform Fixes (1FC3FD, 164AEC, 7BD1E6, 706A0E, A551DB):
- Run diagnostics on each platform returning zero properties
- Use inspect_platform.py or browser tools to identify correct selectors
- Update adapter code with site-specific selectors (not generic patterns)
- Add wait conditions for dynamic content if needed
- Handle anti-bot protection if detected
- Test each adapter independently after fix
- Verify properties found and data quality (titles, URLs, payload)
- Document fixes with before/after selector comparison

### For Documentation & Tracking (62C966, 74CFE6):
- Create platform status tracker to track fixing progress (status, last tested, issues, selectors)
- Create fix documentation template for recording platform fixes consistently

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
