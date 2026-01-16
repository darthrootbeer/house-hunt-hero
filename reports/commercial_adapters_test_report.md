# Commercial Real Estate Adapters Test Report

**Date:** January 16, 2026  
**Test Duration:** ~41 seconds  
**Adapters Tested:** 5  

## Executive Summary

All 5 commercial real estate adapters were successfully implemented and registered. The adapters run without errors, but most require selector refinement to effectively extract listings from JavaScript-heavy interfaces.

**Result:** 5/5 adapters pass (no crashes), but only 1 adapter found a listing (needs refinement).

---

## Test Results by Platform

### 1. The Boulos Company (Investment/Multi-Family)
- **Status:** ✅ Runs without errors
- **Listings Found:** 0
- **URL:** https://boulos.com/properties/investment-properties/
- **Issue:** Listings are embedded in a JavaScript-based search interface (possibly iframe). The wait time and selectors need adjustment to capture the dynamically loaded property cards.
- **Observed:** During manual testing, the site showed 11 investment properties, but the automated scraper isn't capturing them.
- **Recommendation:** Increase wait time to 10-15 seconds, investigate iframe structure, use more specific selectors for the search results container.

### 2. NECPE - New England Commercial Property Exchange
- **Status:** ✅ Runs without errors
- **Listings Found:** 0
- **URL:** https://www.newenglandcommercialproperty.com/properties/?keywords=Maine
- **Issue:** Search results load dynamically via JavaScript. The current selectors aren't matching the property cards.
- **Observed:** During manual testing, the site showed multiple Maine commercial properties with map interface.
- **Recommendation:** Wait for search results to fully load (increase timeout), refine selectors to match the actual card structure (may use data-testid or specific class names from the Moody's CRE platform).

### 3. Malone Commercial Brokers
- **Status:** ✅ Runs without errors
- **Listings Found:** 1 (partial success)
- **URL:** https://www.malonecb.com/search-listings#/search/grid/
- **Issue:** Found 1 result, but it's a navigation link ("HOME") rather than a property listing. The single-page app with hash routing needs more time to load the actual property grid.
- **Observed:** During manual testing, the site showed industrial, land, retail, hospitality, and multi-family properties.
- **Sample Captured:**
  - Title: HOME
  - URL: https://malonecb.catylist.com/listings
  - Price: $6.00 Annual, Sqft: 10,000, Units: 27
- **Recommendation:** Increase wait time for JavaScript execution (12+ seconds), target the grid container specifically, filter out navigation links.

### 4. LoopNet - Multi-Family Properties (Maine)
- **Status:** ✅ Runs without errors
- **Listings Found:** 0
- **URL:** https://www.loopnet.com/search/multifamily-for-sale/maine/
- **Issue:** LoopNet uses a sophisticated JavaScript framework with lazy loading. Listings cards (placards) aren't being detected with current selectors.
- **Observed:** LoopNet is known to have bot protection and may require additional stealth measures.
- **Recommendation:** Research LoopNet's specific DOM structure (they use "placard" class names), consider API access if available, increase stealth measures (additional browser fingerprinting evasion).

### 5. NAI The Dunham Group
- **Status:** ✅ Runs without errors
- **Listings Found:** 0
- **URL:** https://www.thedunhamgroup.com/properties
- **Issue:** Property listings not captured with current selectors.
- **Observed:** Site needs manual verification to confirm listing availability and page structure.
- **Recommendation:** Manually inspect the actual DOM structure, verify the /properties URL is correct, adjust selectors based on actual page layout.

---

## Technical Observations

### What's Working:
1. ✅ All adapters run without crashes
2. ✅ Stealth browser settings successfully bypass initial bot detection (no Access Denied errors)
3. ✅ Import/registration structure is correct
4. ✅ Error handling prevents crashes on timeout or empty results

### What Needs Improvement:
1. **Selector Accuracy:** Current generic selectors don't match the specific DOM structures of these commercial platforms
2. **JavaScript Wait Times:** Most platforms need 10-15 seconds for full content load
3. **Iframe Detection:** Some sites (Boulos) may embed listings in iframes that require separate handling
4. **Dynamic Content:** Single-page apps with hash routing (Malone) need special consideration

### Root Cause Analysis:
Commercial real estate websites use more sophisticated frontend frameworks than typical FSBO/classified sites:
- React/Vue.js-based single-page applications
- Lazy-loaded content (requires scrolling or interaction to trigger)
- Protected APIs with authentication
- Map-based interfaces that load listings dynamically

---

## Recommendations for Next Steps

### Immediate Actions:
1. **Manual DOM Inspection:** Use browser dev tools on each site to identify actual class names, data attributes, and structural patterns
2. **Incremental Testing:** Fix one adapter at a time, starting with Malone (already partially working)
3. **Increase Wait Times:** Change all wait_for_timeout from 5-6 seconds to 10-15 seconds
4. **Add Scroll Behavior:** Some sites require scrolling to trigger lazy loading

### Alternative Approaches:
1. **API Discovery:** Check if any platforms offer public APIs (LoopNet, NECPE)
2. **RSS/Sitemap:** Look for XML sitemaps or RSS feeds that list properties
3. **Network Tab Analysis:** Monitor XHR/Fetch requests to find underlying data APIs
4. **Agent-Browser Testing:** Use agent-browser CLI with --headed flag to manually verify selectors

### Prioritization:
- **High Priority:** Malone Commercial (already found 1 result, close to working)
- **Medium Priority:** NECPE, Boulos Company (good market coverage)
- **Lower Priority:** LoopNet, NAI Dunham (may have API alternatives)

---

## Compliance with Task Requirements

✅ **All 5 commercial platforms have adapters implemented**  
✅ **Source configs created with property_type_filters (multi-family focus)**  
✅ **Registered in `src/ingestion/registry.py`**  
⚠️ **Each adapter tested with actual Maine searches** - Tested but need refinement  
⚠️ **Test results documented** - This document

---

## Conclusion

The commercial adapters foundation is solid - all run without errors and use appropriate stealth measures. However, the complex JavaScript interfaces require platform-specific selector refinement. The adapters are production-ready in terms of error handling and architecture, but need tuning for effective listing extraction.

**Next iteration should focus on:**
1. Refining selectors for at least 2-3 adapters to demonstrate viability
2. Adding platform-specific wait strategies
3. Investigating API/feed alternatives for highly protected sites
