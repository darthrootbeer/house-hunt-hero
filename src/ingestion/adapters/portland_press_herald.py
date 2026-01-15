from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class PortlandPressHeraldAdapter(IngestionAdapter):
    """Fetches real estate listings from Portland Press Herald classifieds (Maine)."""

    source_id = "portland_press_herald"
    # Try common newspaper classifieds URL patterns
    SEARCH_URL = "https://www.pressherald.com/classifieds/real-estate"

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

                items = page.query_selector_all(
                    ".listing, .ad, .item, [class*='listing'], [class*='ad'], [class*='item'], "
                    ".classified-item, article, .classified, .ad-listing"
                )

                if not items:
                    items = page.query_selector_all("a[href*='/real-estate'], a[href*='/classifieds'], a[href*='/ads']")

                for item in items[:50]:
                    try:
                        if item.tag_name == "a":
                            url = item.get_attribute("href") or ""
                        else:
                            link = item.query_selector("a")
                            url = link.get_attribute("href") if link else ""

                        if not url or url.startswith("#"):
                            continue

                        if url.startswith("/"):
                            url = f"https://www.pressherald.com{url}"

                        title_el = item.query_selector("h2, h3, h4, .title, [class*='title'], .headline")
                        title = title_el.inner_text() if title_el else "No title"

                        price_el = item.query_selector(".price, [class*='price'], .cost")
                        price = price_el.inner_text() if price_el else ""

                        location_el = item.query_selector(".location, [class*='location'], .city, .address")
                        location = location_el.inner_text() if location_el else ""

                        date_el = item.query_selector(".date, [class*='date'], .posted")
                        date = date_el.inner_text() if date_el else ""

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "location": location,
                                    "date": date,
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
