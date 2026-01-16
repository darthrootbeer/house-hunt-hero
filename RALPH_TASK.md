---
task: Implement Maine MLS services, brokerages, and credit unions for early-market property listings
test_command: "python scripts/run.py"
---

# Task: Implement Maine MLS Services, Brokerages, and Credit Unions

Implement adapters for Maine MLS services, Maine brokerages, and credit unions to find property listings before they appear on Zillow/Redfin. These sources may have early-market listings that give buyers a competitive advantage.

## Requirements

### 1. Maine MLS Services (2 platforms)
- **Maine Listings** (mainelistings.com) - Official MLS
- **Maine State MLS** (mainestatemls.com)

### 2. Maine Brokerages (12 brokerages)
- Listings Direct
- Meservier & Associates
- Locations Real Estate Group
- Swan Agency
- The Maine Agents
- Sargent Real Estate
- Allied Realty
- Landing Real Estate
- La Count Real Estate
- Realty of Maine
- Maine Real Estate Co.
- Fontaine Family

### 3. Credit Unions (3 sources)
- Maine Highlands Federal Credit Union (mhfcu.com - has properties page)
- Maine State Credit Union (loans, not listings - document if no listings)
- Maine Credit Unions directory (check for property listings)

## Success Criteria

1. [x] Both MLS platforms have adapters implemented
2. [x] All 12 brokerages have adapters implemented (or grouped adapter if similar structure)
3. [x] Credit unions with property listings have adapters implemented
4. [x] All adapters have source configs created in `configs/sources/` with appropriate configuration
5. [x] All adapters registered in `src/ingestion/registry.py`
6. [ ] Each adapter tested with actual Maine property searches and verified to retrieve listings successfully
7. [ ] Test results documented (listings found, data quality, selector/API accuracy)
8. [ ] End-to-end test: `python scripts/run.py` successfully fetches listings from all implemented sources

## Implementation Approach

### For MLS Services:
1. Research MLS API access (RETS, IDX, or public portals)
2. Check GitHub for MLS/RETS scrapers
3. Test public search portals if available
4. Research RETS protocol if needed
5. Create adapters for each MLS
6. Create source configs with: api_endpoints, rets_config (if applicable), search_params, auth_method

### For Brokerages:
1. Research each brokerage website for listing search functionality
2. Check GitHub for real estate brokerage scrapers
3. Group brokerages by similar website structure if applicable
4. Create adapters (individual or grouped)
5. Create source configs with: search_urls, listing_selectors, id_system

### For Credit Unions:
1. Research each credit union website for property listing pages
2. Check Maine Highlands FCU properties page structure
3. Create adapters for credit unions with public listings
4. Create source configs with: properties_url, listing_selectors, form_submission (if required)

### Testing Protocol:
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

## Example Output

```
Running ingestion cycle...
✓ Maine MLS services: 8 listings found
✓ Maine brokerages: 24 listings found
✓ Credit unions: 3 listings found
Total: 35 new listings processed
```

---

## Ralph Instructions

1. Work on the next incomplete criterion (marked [ ])
2. Check off completed criteria (change [ ] to [x])
3. Run tests after changes: `python scripts/run.py`
4. Commit your changes frequently
5. When ALL criteria are [x], output: `<ralph>COMPLETE</ralph>`
6. If stuck on the same issue 3+ times, output: `<ralph>GUTTER</ralph>`
