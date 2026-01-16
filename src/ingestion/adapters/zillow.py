from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing
from ..browser_utils import create_stealth_browser


class ZillowAdapter(IngestionAdapter):
    """Fetches listings from Zillow (Maine).
    
    Note: Zillow has sophisticated anti-bot measures. This adapter provides basic
    functionality but may require additional stealth measures or API access for
    production use.
    """

    source_id = "zillow"
    BASE_URL = "https://www.zillow.com"
    # Maine for-sale listings
    SEARCH_URL = "https://www.zillow.com/homes/for_sale/Maine/"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []
        seen_urls = set()

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_browser(p)
                page = context.new_page()

                page.goto(self.SEARCH_URL, timeout=60000)
                # Wait for search results
                page.wait_for_timeout(8000)

                # Zillow uses article elements with data attributes
                items = page.query_selector_all("article[data-test='property-card'], a[data-test='property-card-link'], li[class*='ListItem']")

                for item in items[:100]:  # Limit to first 100
                    try:
                        # Try to find link within card
                        link_elem = item.query_selector("a[href*='/homedetails/']")
                        if not link_elem:
                            link_elem = item if item.tag_name == 'a' else None
                        
                        if not link_elem:
                            continue
                        
                        url = link_elem.get_attribute("href") or ""
                        
                        if not url or url.startswith("#") or url.startswith("javascript:"):
                            continue

                        # Make URL absolute
                        if url.startswith("/"):
                            url = f"{self.BASE_URL}{url}"
                        elif not url.startswith("http"):
                            continue
                        
                        # Filter for detail pages
                        if "/homedetails/" not in url:
                            continue
                        
                        # Skip duplicates
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        # Extract info from card
                        card_text = item.inner_text().strip()
                        
                        # Extract address/title
                        title = "Property"
                        try:
                            address_elem = item.query_selector("[data-test='property-card-addr'], .address, [class*='StyledPropertyCardAddress']")
                            if address_elem:
                                title = address_elem.inner_text().strip()
                        except:
                            pass
                        
                        # Extract price
                        price = ""
                        try:
                            price_elem = item.query_selector("[data-test='property-card-price'], .price, [class*='PropertyPrice']")
                            if price_elem:
                                price = price_elem.inner_text().strip()
                        except:
                            pass
                        
                        # Extract beds/baths
                        beds = ""
                        baths = ""
                        beds_match = re.search(r'(\d+)\s*bd', card_text, re.IGNORECASE)
                        baths_match = re.search(r'(\d+(?:\.\d+)?)\s*ba', card_text, re.IGNORECASE)
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
                                title=title[:200] if title else "Property",
                                raw_payload={
                                    "price": price,
                                    "beds": beds,
                                    "baths": baths,
                                    "sqft": sqft,
                                    "card_text": card_text[:500] if card_text else "",
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
