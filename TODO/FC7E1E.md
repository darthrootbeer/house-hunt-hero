---
id: FC7E1E
status: pending
deps: []
files: [src/ingestion/adapters/, configs/sources/, src/ingestion/registry.py]
---
::context
Commercial real estate sites may have multi-family properties. 5 platforms: The Boulos Company, NECPE, Malone Commercial Brokers, Five Star Realty Maine, Land.com (commercial section).

::done-when
- All 5 commercial platforms have adapters
- Source configs created
- Registered in registry.py
- Each adapter tested with actual search data and verified to retrieve listings successfully
- Test results documented (listings found, data quality, selector accuracy, multi-family filtering)

::steps
1. Research each platform: check for API, search functionality
2. Check GitHub for commercial real estate scrapers
3. Test scraping tools
4. Create adapters for each platform
5. Create source configs with: search_urls, listing_selectors, property_type_filters (multi-family focus)
6. Implement fetch() methods
7. Register in registry
8. Test each adapter immediately after implementation:
   a. Run adapter.fetch() with actual Maine searches, focusing on multi-family properties
   b. Verify listings are retrieved (check count > 0 if listings exist)
   c. Inspect RawListing objects: verify source_id, listing_url, title, raw_payload populated
   d. Verify listing_urls are absolute and valid
   e. Check that selectors correctly extract property details, price, location, property type
   f. Verify multi-family filter works correctly (excludes pure commercial)
   g. Test with different Maine locations
   h. Verify property type filtering excludes non-residential commercial
   i. Document any selector issues or data quality problems
   j. Refine selectors/config if listings are not retrieved correctly
9. Run end-to-end test: verify all adapters work in full pipeline

::avoid
- Commercial-only properties (unless multi-family)
- Paid API access
- Over-complicating filters

::notes
Focus on multi-family residential properties. Filter out pure commercial. Store property type filters in config.
