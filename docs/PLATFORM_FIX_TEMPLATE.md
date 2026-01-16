# Platform Fix Template

Use this template to document platform fixes. Copy this template to `docs/fixes/<platform_name>.md` when fixing a platform.

---

# Platform Fix: [PLATFORM_NAME]

**Date:** YYYY-MM-DD  
**Fixed By:** [Your name/identifier]  
**Platform ID:** [adapter_source_id]  
**Platform URL:** [search_url]

---

## Issue Description

Briefly describe what wasn't working:

- Platform returned 0 properties
- Selector not matching elements
- Anti-bot blocking
- Authentication required
- Other: [describe]

---

## Diagnostic Findings

### Initial Investigation

What did you discover when investigating the issue?

**Tools Used:**
- [ ] `python scripts/run_diagnostics.py --platforms [platform_name]`
- [ ] `python scripts/inspect_platform.py [platform_name]`
- [ ] Browser DevTools inspection
- [ ] Other: [describe]

**Findings:**
- Screenshot review: [observations from screenshot]
- HTML structure: [key findings about page structure]
- Console errors: [any JavaScript errors or warnings]
- Network requests: [any relevant API calls or XHR]
- Anti-bot protection: [Cloudflare, CAPTCHA, etc. - yes/no]

---

## Selector Analysis

### Old Selectors (Not Working)

```
[List selectors that were not working]
```

**Why they didn't work:**
- [Explanation of why old selectors failed]

### New Selectors (Working)

```
[List correct selectors that match elements]
```

**How they were identified:**
1. [Step-by-step process of finding correct selectors]
2. [Used inspect tool to test selectors]
3. [Verified element count and structure]

**Elements Matched:** [number] elements found

---

## Code Changes

### Adapter File

**File:** `src/ingestion/adapters/[platform_name].py`

**Changes Made:**

1. **Updated selector(s):**
   - Changed `[old_selector]` to `[new_selector]`
   - Reason: [why this change was needed]

2. **Added stealth browser settings:** (if applicable)
   - Added browser launch args: `['--disable-blink-features=AutomationControlled']`
   - Added user agent override
   - Added init script to hide webdriver
   - Reason: [bypass anti-bot protection]

3. **Updated wait conditions:** (if applicable)
   - Changed timeout from X to Y seconds
   - Added wait for specific selector
   - Reason: [page loads slowly, dynamic content, etc.]

4. **Other changes:** (if any)
   - [Describe additional changes]

### Config File (if applicable)

**File:** `configs/sources/[platform_name].yaml`

**Changes Made:**
- [List any config changes]

---

## Test Results

### Before Fix

```
Properties found: 0
Error: [any error messages]
```

### After Fix

```
Properties found: [number]
Sample listings:
  - [sample listing 1]
  - [sample listing 2]
  - [sample listing 3]
```

### Test Command Used

```bash
# Quick test
python -c "from src.ingestion.adapters.[module] import [AdapterClass]; print(len([AdapterClass]().fetch()))"

# Full test
python test_all_platforms.py
```

---

## Platform-Specific Notes

### Special Considerations

- [Any special handling needed for this platform]
- [Rate limits or anti-bot measures]
- [Authentication requirements]
- [Known limitations]

### Future Maintenance

- [What to watch for if this breaks again]
- [Likely causes of future failures]
- [Alternative approaches if current fix stops working]

### Similar Platforms

Other platforms that might use the same fix approach:
- [platform_1] - similar structure
- [platform_2] - same platform provider
- [platform_3] - similar selectors

---

## References

- Diagnostic report: `reports/diagnostics/[platform_name]/`
- Screenshot: `reports/diagnostics/[platform_name]/screenshot.png`
- HTML snapshot: `reports/diagnostics/[platform_name]/page.html`
- Status tracker: `reports/platform_status.md`

---

## Commit Message Template

```
fix: update [platform_name] adapter selectors

- Changed selector from `[old]` to `[new]`
- [Added stealth browser settings / Updated wait conditions / etc.]
- Now finding [number] properties in Maine
- Fixes issue where platform returned 0 results
```

---

## Example: Real Fix Documentation

See `docs/fixes/maine_listings.md` for a real example of a completed fix.
