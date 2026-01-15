---
task: Implement all high priority pre-Zillow listing sources (8 source categories: FSBO platforms, classifieds/newspapers, Facebook, Nextdoor, bank REO, government foreclosures, auction houses, investment platforms)
---

# Task: Implement High Priority Pre-Zillow Listing Sources

Implement all 8 high priority source categories to find listings before they appear on Zillow/Redfin. These sources are most likely to have early-market listings that give buyers a competitive advantage.

## Requirements

1. **FSBO Platforms (8 sites)**: Ownerama, Brokerless, Flat Fee Group, The Rock Foundation, FSBOHomeListings.com, DIY Flat Fee MLS, ISoldMyHouse.com, Hoang Realty FSBO Program
2. **Classifieds & Local Newspapers (6 sources)**: Oodle, Town-Ads.com, Sun Journal, Advertiser Democrat, Midcoast Villager, Portland Press Herald
3. **Facebook Marketplace & Groups**: Facebook Marketplace listings and local Maine real estate groups
4. **Nextdoor**: Neighborhood-based listings from Nextdoor platform
5. **Bank REO Properties (20+ sources)**: 18+ Maine banks (Maine Community Bank, Bangor Savings, etc.) plus 2 aggregators (BankOwnedProperties.org, DistressedPro.com)
6. **Government Tax Foreclosures**: Maine Revenue Services (Unorganized Territory), county probate courts, municipal tax assessor offices
7. **Auction Houses (3 platforms)**: EstateSale.com, GoToAuction.com, Homes.com (auction section)
8. **Investment/Wholesale Platforms (6 sites)**: QuickFlip Construction, Motivate Maine (Wholesale Network), Connected Investors, Discounted Property Solutions, HouseCashin, OfferMarket

## Success Criteria

1. [ ] All 8 FSBO platform adapters implemented and registered
2. [ ] All 6 classified/newspaper source adapters implemented and registered
3. [ ] Facebook Marketplace adapter implemented and registered
4. [ ] Facebook Groups adapter implemented and registered
5. [ ] Nextdoor adapter implemented and registered
6. [ ] Bank REO adapters implemented for banks with public listings
7. [ ] Bank aggregator adapters (BankOwnedProperties.org, DistressedPro.com) implemented
8. [ ] Maine Revenue Services adapter implemented
9. [ ] County/municipal foreclosure adapters implemented (where public)
10. [ ] All 3 auction house adapters implemented and registered
11. [ ] All 6 investment/wholesale platform adapters implemented and registered
12. [ ] All adapters have source configs in configs/sources/ with scraping methods
13. [ ] All adapters registered in src/ingestion/registry.py
14. [ ] All adapters tested and retrieving listings successfully
15. [ ] End-to-end test: run.py successfully fetches listings from all implemented sources

## Implementation Approach

For each source category:
1. Research each platform: check for API, RSS feeds, public search URLs
2. Search GitHub for existing scrapers/libraries
3. Test appropriate tools (Playwright for JS-heavy, requests+BeautifulSoup for static, RSS for feeds)
4. Create adapter class following IngestionAdapter pattern from src/ingestion/base.py
5. Create source config YAML in configs/sources/ with: url, selectors, method (playwright/html/rss/api), rate_limits
6. Implement fetch() method returning List[RawListing]
7. Register in src/ingestion/registry.py
8. Test end-to-end listing retrieval

## Constraints

- Avoid paid API access or credentials
- Avoid login-required sources (unless public endpoints available)
- Avoid violating platform ToS
- Use simplest working method (YAGNI principle)
- For banks/government without public listings, document contact_required: true in config

## Example Output

```
Running ingestion cycle...
✓ FSBO platforms: 12 listings found
✓ Classifieds/newspapers: 8 listings found
✓ Facebook Marketplace: 15 listings found
✓ Facebook Groups: 5 listings found
✓ Nextdoor: 3 listings found
✓ Bank REO: 7 listings found
✓ Government foreclosures: 4 listings found
✓ Auction houses: 9 listings found
✓ Investment platforms: 6 listings found
Total: 69 new listings processed
```

---

## Ralph Instructions

1. Work on the next incomplete criterion (marked [ ])
2. Check off completed criteria (change [ ] to [x])
3. Run tests after changes: `python scripts/run.py`
4. Commit your changes frequently
5. When ALL criteria are [x], output: `<ralph>COMPLETE</ralph>`
6. If stuck on the same issue 3+ times, output: `<ralph>GUTTER</ralph>`
