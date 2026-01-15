---
id: 7CEEF1
status: pending
deps: []
files: [src/ingestion/adapters/, configs/sources/, src/ingestion/registry.py]
---
::context
Classifieds and local newspapers often have early listings. 6 sources: Oodle, Town-Ads.com, Sun Journal, Advertiser Democrat, Midcoast Villager, Portland Press Herald.

::done-when
- All 6 classified/newspaper sources have adapters
- Source configs created with scraping methods
- Registered and tested

::steps
1. Research each site: check classifieds section URLs, search functionality, RSS feeds
2. Check GitHub for existing scrapers
3. Test scraping tools (Playwright for JS-heavy, requests+BS4 for static)
4. Create adapters following pattern
5. Create source configs with: classifieds_url, search_params, listing_selectors, date_filters
6. Implement fetch() methods
7. Register in registry
8. Test retrieval

::avoid
- Paywalled content
- Login requirements
- Complex multi-step workflows

::notes
Newspapers may have different structures. Some may require Playwright for dynamic content. Store search parameters and filters in config.
