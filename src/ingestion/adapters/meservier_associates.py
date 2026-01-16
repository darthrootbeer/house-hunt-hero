from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class MeservierAssociatesAdapter(IngestionAdapter):
    """Fetches listings from Meservier & Associates (meservier.com)."""

    source_id = "meservier_associates"
    BASE_URL = "https://meservier.com"
    SEARCH_URL = "https://meservier.com/listings/"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })

                page.goto(self.SEARCH_URL, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=20000)

                items = page.query_selector_all(
                    ".property-card, .listing-card, .result-item, [class*='property-card'], [class*='listing-card'], "
                    ".property-item, .listing-item, article.property, article.listing, "
                    "a[href*='/property'], a[href*='/listing'], a[href*='/detail']"
                )

                if not items:
                    items = page.query_selector_all("[class*='property'], [class*='listing'], [data-property-id]")

                for item in items[:100]:
                    try:
                        if item.tag_name == "a":
                            url = item.get_attribute("href") or ""
                        else:
                            link = item.query_selector("a")
                            url = link.get_attribute("href") if link else ""

                        if not url or url.startswith("#") or url.startswith("javascript:"):
                            continue

                        if url.startswith("/"):
                            url = f"{self.BASE_URL}{url}"
                        elif not url.startswith("http"):
                            continue

                        title_el = item.query_selector("h2, h3, h4, .title, [class*='title'], .address")
                        title = title_el.inner_text().strip() if title_el else "Meservier & Associates Property"

                        price_el = item.query_selector(".price, [class*='price']")
                        price = price_el.inner_text().strip() if price_el else ""

                        location_el = item.query_selector(".location, [class*='location'], .address")
                        location = location_el.inner_text().strip() if location_el else ""

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "location": location,
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
