---
id: AD7DD7
status: done
deps: []
files: [src/ingestion/adapters/, configs/sources/, src/ingestion/registry.py]
---
::context
18+ Maine banks may list REO properties. Most don't publicly list - need to check websites or contact REO departments. Banks: Maine Community Bank, Bangor Savings, Maine Savings, Camden National, TD Bank, Androscoggin Savings, Bar Harbor Bank & Trust, Bar Harbor S&L, Bath Savings, Franklin Savings, Katahdin Trust, Kennebec Savings, Kennebunk Savings, Machias Savings, Northeast Bank, Norway Savings, Partners Bank, Saco & Biddeford Savings, Skowhegan Savings, First National Bank. Plus 2 aggregators: BankOwnedProperties.org, DistressedPro.com.

::done-when
- Bank website scrapers implemented for banks with public listings
- Aggregator sites (BankOwnedProperties.org, DistressedPro.com) have adapters
- Source configs created for each bank/aggregator
- Registered in registry.py
- Each adapter tested with actual search data and verified to retrieve listings successfully
- Test results documented (listings found, data quality, selector accuracy)

::steps
1. Research each bank website for REO/property listing pages
2. Check GitHub for bank REO scrapers
3. Test scraping tools per bank site
4. Prioritize banks with public listing pages (Maine Community Bank known to have section)
5. Create adapters for banks with public listings
6. Create adapters for aggregator sites
7. Create source configs with: reo_page_url, listing_selectors, contact_method (if no public listings)
8. Implement fetch() methods
9. Register in registry
10. Test each adapter immediately after implementation:
    a. Run adapter.fetch() with actual searches
    b. Verify listings are retrieved (check count > 0 if listings exist)
    c. Inspect RawListing objects: verify source_id, listing_url, title, raw_payload populated
    d. Verify listing_urls are absolute and valid
    e. Check that selectors correctly extract property details, price, location
    f. Test aggregator sites with Maine location filters
    g. Verify Maine-specific listings are retrieved correctly
    h. Document which banks have public listings vs require contact
    i. Document any selector issues or data quality problems
    j. Refine selectors/config if listings are not retrieved correctly
11. Run end-to-end test: verify all adapters work in full pipeline

::avoid
- Requiring direct contact/phone calls
- Login-required sections
- Over-complicating for banks without public listings

::notes
Many banks don't publicly list REO. Document which banks require direct contact. Aggregator sites may be more reliable. Store "contact_required: true" in config for banks without public listings.
