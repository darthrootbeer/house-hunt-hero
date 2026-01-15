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
- Registered and tested

::steps
1. Research each platform: check for API, search functionality
2. Check GitHub for commercial real estate scrapers
3. Test scraping tools
4. Create adapters for each platform
5. Create source configs with: search_urls, listing_selectors, property_type_filters (multi-family focus)
6. Implement fetch() methods
7. Register in registry
8. Test with multi-family and residential filters

::avoid
- Commercial-only properties (unless multi-family)
- Paid API access
- Over-complicating filters

::notes
Focus on multi-family residential properties. Filter out pure commercial. Store property type filters in config.
