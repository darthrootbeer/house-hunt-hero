from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class CraigslistMaineAdapter(IngestionAdapter):
    """Fetches FSBO housing listings from Craigslist Maine."""

    source_id = "craigslist_maine"
    # Real estate in Maine
    SEARCH_URL = "https://maine.craigslist.org/search/rea#search=1~gallery~0~0"

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
                # Wait for listings to load
                page.wait_for_selector(".cl-search-result", timeout=10000)

                # Extract all listing items
                items = page.query_selector_all(".cl-search-result")

                for item in items[:25]:  # Limit to first 25 listings
                    try:
                        # Get the main link element
                        link = item.query_selector("a.main")
                        if not link:
                            continue

                        url = link.get_attribute("href") or ""

                        # Title is in img alt attribute
                        img = item.query_selector("img")
                        title = img.get_attribute("alt") if img else "No title"
                        # Remove trailing image number (e.g., " 1" at end)
                        if title and title[-2:].strip().isdigit():
                            title = title.rsplit(" ", 1)[0]

                        # Get price if available
                        price_el = item.query_selector(".price")
                        price = price_el.inner_text() if price_el else ""

                        # Get location/meta info
                        meta_el = item.query_selector(".meta")
                        meta = meta_el.inner_text() if meta_el else ""

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "meta": meta,
                                },
                            )
                        )
                    except Exception:
                        # Skip individual items that fail to parse
                        continue

                browser.close()

        except PlaywrightTimeout:
            # Return empty list if page fails to load
            pass
        except Exception:
            # Return empty list on any other error
            pass

        return listings
