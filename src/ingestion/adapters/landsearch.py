from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing
from ..browser_utils import create_stealth_browser


class LandSearchAdapter(IngestionAdapter):
    """Fetches land listings with structures from LandSearch (Maine).
    
    Note: Focuses on properties with houses/structures, not raw land.
    """

    source_id = "landsearch"
    BASE_URL = "https://www.landsearch.com"
    # Maine land with structures
    SEARCH_URL = "https://www.landsearch.com/properties/maine"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []
        seen_urls = set()

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_browser(p)
                page = context.new_page()

                page.goto(self.SEARCH_URL, timeout=60000)
                page.wait_for_timeout(8000)

                items = page.query_selector_all("a[href*='/property/'], .property-card, [class*='PropertyCard']")

                for item in items[:100]:
                    try:
                        url = item.get_attribute("href") or ""
                        
                        if not url or url.startswith("#"):
                            continue

                        if url.startswith("/"):
                            url = f"{self.BASE_URL}{url}"
                        elif not url.startswith("http"):
                            continue
                        
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        card_text = item.inner_text().strip()
                        
                        # Filter: skip if explicitly "raw land" or "vacant land"
                        if any(term in card_text.lower() for term in ['raw land', 'vacant land', 'undeveloped']):
                            continue
                        
                        title = "Land Property"
                        
                        # Extract address or description
                        lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                        if lines:
                            title = lines[0]
                        
                        # Extract price
                        price = ""
                        price_match = re.search(r'\$[\d,]+', card_text)
                        if price_match:
                            price = price_match.group()
                        
                        # Extract acreage
                        acres = ""
                        acres_match = re.search(r'([\d.]+)\s*acres?', card_text, re.IGNORECASE)
                        if acres_match:
                            acres = acres_match.group(1)

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title[:200],
                                raw_payload={
                                    "price": price,
                                    "acres": acres,
                                    "card_text": card_text[:500],
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
