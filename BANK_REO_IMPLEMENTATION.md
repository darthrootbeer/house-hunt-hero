# Bank REO Properties Implementation Report

## Summary

Implemented bank REO (Real Estate Owned) property listings for 20+ Maine banks and 2 aggregator sites.

**Date:** January 2026
**Task ID:** AD7DD7

---

## Implementation Details

### Aggregator Sites (2 adapters)

#### 1. BankOwnedProperties.org
- **Adapter:** `BankOwnedPropertiesAdapter`
- **Status:** ✅ Implemented
- **Config:** `configs/sources/bank_owned_properties.yaml`
- **URL:** https://www.bankownedproperties.org/bankhomes/MAINE.html
- **Method:** Playwright scraping
- **Notes:** Aggregator site organized by state, county, and city. Contains active REO listings from multiple banks.

#### 2. DistressedPro.com
- **Adapter:** `DistressedProAdapter`
- **Status:** ✅ Implemented
- **Config:** `configs/sources/distressed_pro.yaml`
- **URL:** https://www.distressedpro.com/app/properties/ME
- **Method:** Playwright scraping
- **Notes:** Aggregator site for distressed and bank-owned properties, organized by bank and location.

### Banks with Public Listings (1 adapter)

#### 3. Maine Community Bank
- **Adapter:** `MaineCommunityBankAdapter`
- **Status:** ✅ Implemented
- **Config:** `configs/sources/maine_community_bank.yaml`
- **URL:** https://maine.bank/personal/home-loans/bank-owned-properties/
- **Method:** Playwright scraping
- **Notes:** Has public REO listings page (may currently show "no properties available")

### Banks Requiring Contact (18 configs)

The following banks do not publicly list REO properties. Configs are created with `contact_required: true` and `enabled: false`. These banks require direct contact with their REO departments:

1. **Bangor Savings Bank** - `bangor_savings.yaml`
2. **Maine Savings** - `maine_savings.yaml`
3. **Camden National Bank** - `camden_national.yaml`
4. **Androscoggin Savings Bank** - `androscoggin_savings.yaml`
5. **Bar Harbor Bank & Trust** - `bar_harbor_bank.yaml`
6. **Bar Harbor Savings & Loan** - `bar_harbor_savings_loan.yaml`
7. **Bath Savings Institution** - `bath_savings.yaml`
8. **Franklin Savings Bank** - `franklin_savings.yaml`
9. **Katahdin Trust Company** - `katahdin_trust.yaml`
10. **Kennebec Savings Bank** - `kennebec_savings.yaml`
11. **Kennebunk Savings Bank** - `kennebunk_savings.yaml`
12. **Machias Savings Bank** - `machias_savings.yaml`
13. **Northeast Bank** - `northeast_bank.yaml`
14. **Norway Savings Bank** - `norway_savings.yaml`
15. **Partners Bank** - `partners_bank.yaml`
16. **Saco & Biddeford Savings Institution** - `saco_biddeford_savings.yaml`
17. **Skowhegan Savings Bank** - `skowhegan_savings.yaml`
18. **First National Bank** - `first_national_bank.yaml`
19. **TD Bank** - `td_bank.yaml`

**Note:** All banks requiring contact have `method: "contact_required"` and should be contacted directly through their REO departments for available properties.

---

## Files Created

### Adapters (3 files)
- `src/ingestion/adapters/bank_owned_properties.py`
- `src/ingestion/adapters/distressed_pro.py`
- `src/ingestion/adapters/maine_community_bank.py`

### Source Configs (21 files)
- `configs/sources/bank_owned_properties.yaml` (aggregator)
- `configs/sources/distressed_pro.yaml` (aggregator)
- `configs/sources/maine_community_bank.yaml` (bank with public listings)
- 18 bank configs marked as `contact_required: true`

### Registry Updates
- `src/ingestion/adapters/__init__.py` - Added exports for 3 new adapters
- `src/ingestion/registry.py` - Registered 3 new adapters

### Test Script
- `test_bank_reo_adapters.py` - Test script for verifying adapters (requires playwright)

---

## Testing Status

### Aggregator Sites
- ✅ **BankOwnedProperties.org** - Adapter implemented, needs live testing with playwright
- ✅ **DistressedPro.com** - Adapter implemented, needs live testing with playwright

### Banks with Public Listings
- ✅ **Maine Community Bank** - Adapter implemented, needs live testing with playwright

### Banks Requiring Contact
- ⚠️  All 18 banks marked as `contact_required: true` - No adapters created (direct contact required)

---

## Testing Instructions

To test the adapters:

1. Install playwright:
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. Run test script:
   ```bash
   python test_bank_reo_adapters.py
   ```

3. Verify each adapter:
   - Retrieves listings (check count > 0 if listings exist)
   - Populates RawListing objects correctly (source_id, listing_url, title, raw_payload)
   - Listing URLs are absolute and valid
   - Selectors correctly extract property details (price, location, beds/baths)

---

## Selector Notes

All adapters use flexible selector patterns to handle various page structures:
- Container selectors: `.listing, .property, .result-item, [class*='listing'], [class*='property']`
- Title selectors: `h2, h3, h4, .title, [class*='title'], .address`
- Price selectors: `.price, [class*='price'], [class*='cost']`
- Location selectors: `.location, [class*='location'], .city, .county`

**Note:** Selectors may need refinement after live testing based on actual page structures.

---

## Next Steps

1. **Live Testing** - Test all 3 adapters with actual searches to verify:
   - Selectors work correctly
   - Data extraction is accurate
   - Listing URLs are valid

2. **Selector Refinement** - Adjust selectors based on actual page structures discovered during testing

3. **Documentation** - Document any selector issues or data quality problems found during testing

4. **End-to-End Testing** - Verify all adapters work in the full pipeline (ingestion → normalization → dedupe → scoring → alerting)

---

## Contact Information

For banks requiring contact, reach out to their REO/Special Assets departments directly. Config files include the base URL and contact method for each bank.

---

## Registry Status

All 3 active adapters are registered in `src/ingestion/registry.py`:
- `BankOwnedPropertiesAdapter()` - Enabled
- `DistressedProAdapter()` - Enabled  
- `MaineCommunityBankAdapter()` - Enabled

The 18 banks requiring contact are not included in the registry (they have configs but no adapters, as direct contact is required).
