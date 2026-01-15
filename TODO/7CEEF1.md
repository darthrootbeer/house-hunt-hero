---
id: 7CEEF1
status: done
deps: []
files: [src/ingestion/adapters/, configs/sources/, src/ingestion/registry.py]
---
::context
Classifieds and local newspapers often have early listings. 6 sources: Oodle, Town-Ads.com, Sun Journal, Advertiser Democrat, Midcoast Villager, Portland Press Herald.

::done-when
- All 6 classified/newspaper sources have adapters
- Source configs created with scraping methods
- Registered in registry.py
- Each adapter tested with actual search data and verified to retrieve listings successfully
- Test results documented (listings found, data quality, selector accuracy)

::steps
1. Research each site: check classifieds section URLs, search functionality, RSS feeds
2. Check GitHub for existing scrapers
3. Test scraping tools (Playwright for JS-heavy, requests+BS4 for static)
4. Create adapters following pattern
5. Create source configs with: classifieds_url, search_params, listing_selectors, date_filters
6. Implement fetch() methods
7. Register in registry
8. Test each adapter immediately after implementation:
   a. Run adapter.fetch() with actual Maine location searches
   b. Verify listings are retrieved (check count > 0 if listings exist)
   c. Inspect RawListing objects: verify source_id, listing_url, title, raw_payload populated
   d. Verify listing_urls are absolute and valid
   e. Check that selectors correctly extract price, location, date, description
   f. Test with different location filters (Maine cities/towns)
   g. Verify date filters work correctly if implemented
   h. Document any selector issues or data quality problems
   i. Refine selectors/config if listings are not retrieved correctly
9. Run end-to-end test: verify all adapters work in full pipeline

::avoid
- Paywalled content
- Login requirements
- Complex multi-step workflows

::notes
Newspapers may have different structures. Some may require Playwright for dynamic content. Store search parameters and filters in config.
