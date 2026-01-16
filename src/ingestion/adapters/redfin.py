from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing
from ..browser_utils import create_stealth_browser


class RedfinAdapter(IngestionAdapter):
    """Fetches listings from Redfin (Maine).
    
    Note: Redfin has anti-bot measures. This adapter may require refinement.
    """

    source_id = "redfin"
    BASE_URL = "https://www.redfin.com"
    # Maine for-sale listings
    SEARCH_URL = "https://www.redfin.com/state/Maine"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []
        seen_urls = set()

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_browser(p)
                page = context.new_page()

                page.goto(self.SEARCH_URL, timeout=60000)
                page.wait_for_timeout(8000)

                # Redfin uses property cards with specific classes
                items = page.query_selector_all("[class*='HomeCard'], [data-rf-test-name='abp-streetline'], .HomeViews")

                for item in items[:100]:
                    try:
                        link_elem = item.query_selector("a[href*='/home/']")
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
                            address_elem = item.query_selector("[class*='address'], [class*='homeAddress']")
                            if address_elem:
                                title = address_elem.inner_text().strip()
                        except:
                            pass
                        
                        # Extract price
                        price = ""
                        price_match = re.search(r'\$[\d,]+[KkMm]?', card_text)
                        if price_match:
                            price = price_match.group()
                        
                        # Extract beds/baths
                        beds = ""
                        baths = ""
                        beds_match = re.search(r'(\d+)\s*Bed', card_text, re.IGNORECASE)
                        baths_match = re.search(r'(\d+(?:\.\d+)?)\s*Bath', card_text, re.IGNORECASE)
                        if beds_match:
                            beds = beds_match.group(1)
                        if baths_match:
                            baths = baths_match.group(1)
                        
                        # Extract sqft
                        sqft = ""
                        sqft_match = re.search(r'([\d,]+)\s*Sq\.?\s*Ft', card_text, re.IGNORECASE)
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
