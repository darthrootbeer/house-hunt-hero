from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class HouseCashinAdapter(IngestionAdapter):
    """Fetches wholesale property listings from HouseCashin (wholesale real estate network)."""

    source_id = "housecashin"
    SEARCH_URL = "https://www.housecashin.com"

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

                # Look for wholesale property listings
                items = page.query_selector_all(
                    ".property, .listing, .deal, .wholesale, [class*='property'], "
                    "[class*='listing'], [class*='deal'], [class*='wholesale']"
                )

                if not items:
                    items = page.query_selector_all("a[href*='/property'], a[href*='/listing'], a[href*='/deal']")

                for item in items[:50]:
                    try:
                        if item.tag_name == "a":
                            url = item.get_attribute("href") or ""
                        else:
                            link = item.query_selector("a")
                            url = link.get_attribute("href") if link else ""

                        if not url or url.startswith("#") or url.startswith("javascript:"):
                            continue

                        if url.startswith("/"):
                            url = f"https://www.housecashin.com{url}"
                        elif not url.startswith("http"):
                            url = f"https://www.housecashin.com/{url}"

                        title_el = item.query_selector("h2, h3, h4, .title, [class*='title']")
                        title = title_el.inner_text() if title_el else "Wholesale Property"

                        location_el = item.query_selector(".location, [class*='location'], .address, [class*='address']")
                        location = location_el.inner_text() if location_el else ""

                        price_el = item.query_selector(".price, [class*='price'], .wholesale-price, [class*='wholesale']")
                        price = price_el.inner_text() if price_el else ""

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "location": location,
                                    "type": "wholesale",
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
