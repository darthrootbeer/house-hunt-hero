# Platform Status Tracker

**Last Updated:** 2026-01-16

**Purpose:** Track platform fix progress and selector changes

**Legend:**
- ✅ **Working** - Finding properties successfully
- ⚠️ **Needs Fix** - Returns zero properties, needs selector update
- 🔧 **In Progress** - Currently being fixed
- ❌ **Broken** - Has errors or known blockers
- 📋 **Not Started** - Not yet investigated

---

## Summary

- **Working:** 7 platforms (12%)
- **Needs Fix:** 51 platforms (88%)
- **In Progress:** 0 platforms
- **Broken:** 0 platforms

---

## Platforms by Category

### Classifieds & Local News (3/9 working)

#### ✅ craigslist_owner
- **Last Tested:** 2026-01-16
- **Status:** Working (25 properties found)
- **Selectors:** `.cl-search-result`
- **Notes:** Using current live Craigslist structure

#### ✅ craigslist_maine
- **Last Tested:** 2026-01-16
- **Status:** Working (25 properties found)
- **Selectors:** `.cl-search-result`
- **Notes:** Using current live Craigslist structure

#### ✅ craigslist_nh
- **Last Tested:** 2026-01-16
- **Status:** Working (25 properties found)
- **Selectors:** `.cl-search-result`
- **Notes:** Using current live Craigslist structure

#### ⚠️ oodle
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)
- **Issues:** Selector not matching
- **Diagnostics:** Run `python scripts/run_diagnostics.py --platforms oodle`

#### ⚠️ town_ads
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)
- **Issues:** Selector not matching or limited inventory
- **Diagnostics:** Run `python scripts/run_diagnostics.py --platforms town_ads`

#### ⚠️ sun_journal
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)
- **Issues:** Selector not matching or limited inventory
- **Diagnostics:** Run `python scripts/run_diagnostics.py --platforms sun_journal`

#### ⚠️ advertiser_democrat
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)
- **Issues:** Selector not matching or limited inventory
- **Diagnostics:** Run `python scripts/run_diagnostics.py --platforms advertiser_democrat`

#### ⚠️ midcoast_villager
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)
- **Issues:** Selector not matching or limited inventory
- **Diagnostics:** Run `python scripts/run_diagnostics.py --platforms midcoast_villager`

#### ⚠️ portland_press_herald
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)
- **Issues:** Selector not matching or limited inventory
- **Diagnostics:** Run `python scripts/run_diagnostics.py --platforms portland_press_herald`

---

### Maine Brokerages (2/11 working)

#### ✅ realty_of_maine
- **Last Tested:** 2026-01-16
- **Status:** Working (12 properties found)
- **Selectors:** `a[href*='/listing/']`
- **Notes:** Using stealth browser to bypass anti-bot

#### ✅ landing_real_estate
- **Last Tested:** 2026-01-16
- **Status:** Working (10 properties found)
- **Selectors:** `a[href*='/listing/']`
- **Notes:** Using stealth browser to bypass anti-bot

#### ⚠️ listings_direct
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ meservier_associates
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ locations_real_estate_group
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ swan_agency
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ the_maine_agents
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ sargent_real_estate
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ allied_realty
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ la_count_real_estate
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ maine_real_estate_co
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

---

### MLS Services (1/2 working)

#### ✅ maine_listings
- **Last Tested:** 2026-01-16
- **Status:** Working (23 properties found)
- **Selectors:** `a[href*='/listings/ME/']`
- **Notes:** Using stealth browser to bypass Cloudflare

#### ⚠️ maine_state_mls
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)
- **Issues:** Similar to maine_listings but different URL structure
- **Diagnostics:** Run `python scripts/run_diagnostics.py --platforms maine_state_mls`

---

### Commercial Real Estate (1/5 working)

#### ✅ boulos_company
- **Last Tested:** 2026-01-16
- **Status:** Working (1 property found)
- **Selectors:** Multi-family focused
- **Notes:** Limited inventory

#### ⚠️ necpe
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ malone_commercial
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ loopnet
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ nai_dunham
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

---

### FSBO Platforms (0/9 working)

#### ⚠️ ownerama
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ brokerless
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ flat_fee_group
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ the_rock_foundation
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ fsbo_home_listings
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ diy_flat_fee
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ isold_my_house
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ hoang_realty_fsbo
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ fsbo_com
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

---

### Social & Community (0/3 working)

#### ⚠️ facebook_marketplace
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)
- **Issues:** May require authentication

#### ⚠️ facebook_groups
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)
- **Issues:** May require authentication

#### ⚠️ nextdoor
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)
- **Issues:** May require authentication

---

### Bank REO & Foreclosures (0/4 working)

#### ⚠️ bank_owned_properties
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ distressed_pro
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ maine_community_bank
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ fontaine_family
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

---

### Government & Tax Sales (0/3 working)

#### ⚠️ on_point_realty
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ york_county_probate
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ municipal_tax_assessor
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

---

### Auctions (0/3 working)

#### ⚠️ estatesale
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ gotoauction
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ homes_auction
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

---

### Investment & Wholesale (0/6 working)

#### ⚠️ quickflip_construction
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ motivate_maine
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ connected_investors
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ discounted_property_solutions
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ housecashin
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

#### ⚠️ offermarket
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)

---

### Credit Unions (0/3 working)

#### ⚠️ maine_highlands_fcu
- **Last Tested:** 2026-01-16
- **Status:** Needs Fix (0 properties)
- **Notes:** Has dedicated REO listings page

#### ⚠️ maine_state_credit_union
- **Last Tested:** 2026-01-16
- **Status:** Contact Required
- **Notes:** No public listings page - requires contact

#### ⚠️ maine_credit_unions_directory
- **Last Tested:** 2026-01-16
- **Status:** Contact Required
- **Notes:** Directory site - no direct listings

---

## Next Actions

### High Priority (Working but need monitoring)
1. Craigslist adapters - verify ongoing stability
2. Maine Listings - monitor for Cloudflare changes
3. Realty of Maine - monitor anti-bot detection
4. Landing Real Estate - monitor anti-bot detection

### Medium Priority (Should investigate next)
1. Maine State MLS - similar to maine_listings
2. FSBO platforms - likely have listings available
3. Maine brokerage sites - likely have listings available

### Lower Priority
1. Social platforms - may require authentication
2. Specialized sites - may have limited inventory

---

## How to Fix a Platform

1. Run diagnostics: `python scripts/run_diagnostics.py --platforms <adapter_id>`
2. Inspect interactively: `python scripts/inspect_platform.py <adapter_id>`
3. Review diagnostic report in `reports/diagnostics/<adapter_id>/`
4. Identify correct selectors from screenshot/HTML
5. Update adapter code with correct selectors
6. Test adapter: `python -c "from src.ingestion.adapters.<adapter> import <Adapter>; print(len(<Adapter>().fetch()))"`
7. Update this status file with new status and selector info
8. Commit changes with descriptive message
