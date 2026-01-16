from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing
from ..browser_utils import create_stealth_browser


class HomesComAdapter(IngestionAdapter):
    """Fetches listings from Homes.com (Maine).
    
    Note: Homes.com may have anti-bot measures. This adapter may need refinement.
    """

    source_id = "homes_com"
    BASE_URL = "https://www.homes.com"
    # Maine for-sale listings
    SEARCH_URL = "https://www.homes.com/maine/"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []
        seen_urls = set()

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_browser(p)
                page = context.new_page()

                page.goto(self.SEARCH_URL, timeout=60000)
                page.wait_for_timeout(8000)

                # Homes.com uses property cards
                items = page.query_selector_all("[data-testid='srp-home-card'], .property-card, [class*='PropertyCard']")

                for item in items[:100]:
                    try:
                        link_elem = item.query_selector("a[href*='/property/']")
                        if not link_elem:
                            continue
                        
                        url = link_elem.get_attribute("href") or ""
                        
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
                        
                        # Extract address
                        title = "Property"
                        try:
                            address_elem = item.query_selector("[data-testid='property-address'], .address")
                            if address_elem:
                                title = address_elem.inner_text().strip()
                        except:
                            pass
                        
                        # Extract price
                        price = ""
                        price_match = re.search(r'\$[\d,]+', card_text)
                        if price_match:
                            price = price_match.group()
                        
                        # Extract beds/baths
                        beds = ""
                        baths = ""
                        beds_match = re.search(r'(\d+)\s*bed', card_text, re.IGNORECASE)
                        baths_match = re.search(r'(\d+(?:\.\d+)?)\s*bath', card_text, re.IGNORECASE)
                        if beds_match:
                            beds = beds_match.group(1)
                        if baths_match:
                            baths = baths_match.group(1)
                        
                        # Extract sqft
                        sqft = ""
                        sqft_match = re.search(r'([\d,]+)\s*sqft', card_text, re.IGNORECASE)
                        if sqft_match:
                            sqft = sqft_match.group(1)

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title[:200],
                                raw_payload={
                                    "price": price,
                                    "beds": beds,
                                    "baths": baths,
                                    "sqft": sqft,
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
