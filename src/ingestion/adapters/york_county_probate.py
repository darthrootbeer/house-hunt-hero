from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class YorkCountyProbateAdapter(IngestionAdapter):
    """Fetches estate notices from York County Probate Court."""

    source_id = "york_county_probate"
    SEARCH_URL = "https://www.yorkcountymaine.gov/registry-of-probate"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })

                page.goto(self.SEARCH_URL, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)

                # Look for estate notice links - may be PDF links or HTML pages
                # Common patterns: links to PDFs or notices
                items = page.query_selector_all(
                    "a[href*='estate'], a[href*='notice'], a[href*='probate'], "
                    "a[href*='.pdf'], .estate-notice, .probate-notice, [class*='estate'], [class*='notice']"
                )

                for item in items[:50]:  # Limit to first 50 notices
                    try:
                        url = item.get_attribute("href") or ""

                        if not url or url.startswith("#") or url.startswith("javascript:"):
                            continue

                        # Make URL absolute if relative
                        if url.startswith("/"):
                            url = f"https://www.yorkcountymaine.gov{url}"
                        elif not url.startswith("http"):
                            url = f"https://www.yorkcountymaine.gov/{url}"

                        # Try to get title/text
                        title = item.inner_text() if item else "Estate Notice"
                        if not title or len(title) < 3:
                            # Try to get text from parent or nearby elements
                            parent = item.evaluate_handle("el => el.parentElement")
                            if parent:
                                title_el = page.query_selector(f"a[href='{url}']")
                                if title_el:
                                    title = title_el.inner_text() or "Estate Notice"

                        # Skip if it's clearly not a property-related notice
                        if not any(keyword in title.lower() for keyword in ["estate", "probate", "property", "real estate"]):
                            continue

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "type": "estate_notice",
                                    "county": "York",
                                },
                            )
                        )
                    except Exception:
                        continue

                browser.close()

        except PlaywrightTimeout:
            pass
        except Exception:
            pass

        return listings
