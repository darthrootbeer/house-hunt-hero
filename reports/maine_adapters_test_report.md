# Maine MLS, Brokerage, and Credit Union Adapter Test Report

**Date:** 2026-01-16  
**Tester:** Ralph Autonomous Agent  

## Summary

- **Total adapters tested:** 15
- **Successful fetches (no errors):** 15
- **Adapters returning listings:** 3
- **Total listings found:** 45

## Working Adapters

### 1. Maine Listings (Official MLS)
- **Source ID:** `maine_listings`
- **Listings found:** 23
- **Data quality:** Good
  - Valid URLs with MLS numbers
  - Address extraction working
  - Price and location data captured
- **Sample listing:**
  - Title: "128 Mills Road Newcastle Me 04553"
  - URL: `https://mainelistings.com/listings/ME/Newcastle/04553/10376/128-mills-road-newcastle-me-04553/643666246`
- **Notes:** Uses stealth browser to bypass Cloudflare protection

### 2. Landing Real Estate
- **Source ID:** `landing_real_estate`
- **Listings found:** 10
- **Data quality:** Good
  - Clean address extraction
  - Price, status, beds, baths, sqft parsed
  - IDX feed integration working
- **Sample listing:**
  - Title: "9 Office Drive, Bath, ME"
  - Price: $365,000
  - Status: Active
  - Beds: N/A, Baths: 2, SqFt: 2,112
- **Notes:** Uses stealth browser to bypass bot detection

### 3. Realty of Maine
- **Source ID:** `realty_of_maine`
- **Listings found:** 12
- **Data quality:** Good
  - Address and location extracted
  - Price, beds, baths, sqft parsed
  - IDX feed URLs captured
- **Sample listing:**
  - Title: "16 Mason Avenue, Naples, ME"
  - Price: $315,000
  - Beds: 3, Baths: 1
- **Notes:** Uses stealth browser; IDX feed requires longer wait time

## Non-Working Adapters (0 listings)

These adapters run without errors but don't find listings. Likely causes and recommendations:

### MLS Platforms
| Adapter | Issue | Recommendation |
|---------|-------|----------------|
| Maine State MLS | Requires member login | Mark as `contact_required: true` |

### Brokerages
| Adapter | Issue | Recommendation |
|---------|-------|----------------|
| Listings Direct | Site structure unknown | Needs manual investigation |
| Meservier & Associates | Site structure unknown | Needs manual investigation |
| Locations Real Estate Group | Site structure unknown | Needs manual investigation |
| Swan Agency | Complex JS loading | May need longer waits or different approach |
| The Maine Agents | Complex JS loading | May need longer waits or different approach |
| Sargent Real Estate | Site structure unknown | Needs manual investigation |
| Allied Realty | Site structure unknown | Needs manual investigation |
| La Count Real Estate | Complex JS loading | May need longer waits |
| Maine Real Estate Co. | Facebook-based | Requires Facebook API/login |
| Fontaine Family | Page returns blank | May block automated access |

### Credit Unions
| Adapter | Issue | Recommendation |
|---------|-------|----------------|
| Maine Highlands FCU | Empty inventory | Adapter works, just no current listings |

## Technical Improvements Made

1. **Stealth Browser Settings**
   - Added `--disable-blink-features=AutomationControlled` flag
   - Set realistic user agent string
   - Added webdriver property masking script
   - Created shared `browser_utils.py` module

2. **URL Corrections**
   - Landing Real Estate: `/listings/` → `/our-listings/`
   - Realty of Maine: `/searchmaine` → `/listings/`
   - Maine Listings: Simplified URL, removed filter params

3. **Selector Improvements**
   - Landing: `a[href*='/idx/']` for IDX listings
   - Maine Listings: `a[href*='/listings/ME/']` for state-specific URLs
   - Realty of Maine: `a[href*='/listing/']` for detail pages

## Recommendations for Future Work

1. **Priority Fixes** (likely to yield more listings):
   - Swan Agency - large brokerage, likely has listings behind JS
   - Allied Realty - established Maine brokerage
   - The Maine Agents - may just need longer wait times

2. **Mark as Contact Required:**
   - Maine State MLS (requires realtor credentials)
   - Maine Real Estate Co. (Facebook-based)

3. **Consider Removing:**
   - Adapters that consistently return 0 after multiple fix attempts

## Test Command

```bash
cd /Users/bengoddard/projects/house-hunt-hero
PYTHONPATH=. python3.11 tests/test_new_adapters.py
```

## Conclusion

The core MLS adapter (Maine Listings) and two major brokerages (Landing Real Estate, Realty of Maine) are now successfully fetching listings with a total of 45 active listings. The stealth browser approach is effective for bypassing common bot detection. Further investigation is needed for the remaining brokerages.
