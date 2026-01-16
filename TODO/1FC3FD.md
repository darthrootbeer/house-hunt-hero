---
id: 1FC3FD
status: pending
deps: [F0C541]
files: [src/ingestion/adapters/ownerama.py, src/ingestion/adapters/brokerless.py, src/ingestion/adapters/flat_fee_group.py, src/ingestion/adapters/the_rock_foundation.py, src/ingestion/adapters/fsbo_home_listings.py, src/ingestion/adapters/diy_flat_fee.py, src/ingestion/adapters/isold_my_house.py]
---
::context
Fix FSBO platforms returning zero properties. Inspect live pages, identify correct selectors, update adapter code, test fixes. Priority: ownerama, brokerless, flat_fee_group, the_rock_foundation, fsbo_home_listings, diy_flat_fee, isold_my_house.

::done-when
- All 7 FSBO platforms finding properties (or documented why not possible)
- Correct selectors identified via page inspection
- Adapter code updated with specific selectors
- Each platform tested independently and verified working
- Fixes documented with before/after selector comparison

::steps
1. Run diagnostics on each FSBO platform
2. Use inspect_platform.py to identify correct selectors
3. For each platform: update query_selector_all calls with correct selectors
4. Add wait conditions if listings load dynamically
5. Handle anti-bot protection if detected
6. Test each adapter: python -c "from src.ingestion.adapters.{name} import {Adapter}; print(len({Adapter}().fetch()))"
7. Verify properties found, check data quality (titles, URLs)
8. Update platform status tracker

::avoid
- Don't use generic selectors (use site-specific ones)
- Don't skip wait conditions for dynamic content
- Don't assume all 7 will have properties (some sites may be empty)

::notes
- FSBO platforms are high priority (likely to have properties)
- Each platform may need different selector strategy
- Test one at a time to avoid confusion
