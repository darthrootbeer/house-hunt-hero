from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing
from ..browser_utils import create_stealth_browser


class KWLandAdapter(IngestionAdapter):
    """Fetches land listings from KW Land (Keller Williams Land Division)."""

    source_id = "kw_land"
    BASE_URL = "https://www.kwland.com"
    SEARCH_URL = "https://www.kwland.com/search?state=ME"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []
        seen_urls = set()

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_browser(p)
                page = context.new_page()

                page.goto(self.SEARCH_URL, timeout=60000)
                page.wait_for_timeout(8000)

                items = page.query_selector_all("a[href*='/property/'], a[href*='/listing/'], .property-card")

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
                        
                        # Skip raw land
                        if 'vacant' in card_text.lower():
                            continue
                        
                        title = "Land Property"
                        lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                        if lines:
                            title = lines[0]
                        
                        price = ""
                        price_match = re.search(r'\$[\d,]+', card_text)
                        if price_match:
                            price = price_match.group()
                        
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
