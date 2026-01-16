from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class CraigslistNHAdapter(IngestionAdapter):
    """Fetches FSBO housing listings from Craigslist New Hampshire (near Maine)."""

    source_id = "craigslist_nh"
    # Real estate in New Hampshire
    SEARCH_URL = "https://nh.craigslist.org/search/rea#search=1~gallery~0~0"

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

                        # Try multiple fallback strategies for title extraction
                        title = None
                        
                        # Strategy 1: Try img alt attribute (primary method)
                        img = item.query_selector("img")
                        if img:
                            title = img.get_attribute("alt") or None
                            if title:
                                # Remove trailing image number (e.g., " 1" at end)
                                if title and len(title) > 2 and title[-2:].strip().isdigit():
                                    title = title.rsplit(" ", 1)[0]
                        
                        # Strategy 2: Fall back to link text if img alt fails
                        if not title or title == "No title":
                            link_text = link.inner_text().strip()
                            if link_text:
                                title = link_text
                        
                        # Strategy 3: Try finding title in listing text elements
                        if not title or title == "No title":
                            title_el = item.query_selector(".title, .postingtitle, [class*='title']")
                            if title_el:
                                title = title_el.inner_text().strip()
                        
                        # Strategy 4: Try any text content from the main item
                        if not title or title == "No title":
                            item_text = item.inner_text().strip()
                            # Take first line as title if it's reasonable length
                            if item_text:
                                first_line = item_text.split("\n")[0].strip()
                                if first_line and len(first_line) > 3:
                                    title = first_line[:100]  # Limit length
                        
                        # Skip if we still don't have a valid title
                        if not title or title == "No title" or len(title.strip()) < 3:
                            continue

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
                        continue

                browser.close()

        except PlaywrightTimeout:
            pass
        except Exception:
            pass

        return listings


# Keep FSBOComAdapter as alias for backwards compatibility
FSBOComAdapter = CraigslistNHAdapter
