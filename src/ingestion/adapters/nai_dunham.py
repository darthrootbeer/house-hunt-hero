from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing
from ..browser_utils import create_stealth_browser


class NAIDunhamAdapter(IngestionAdapter):
    """Fetches listings from NAI The Dunham Group (Maine commercial real estate)."""

    source_id = "nai_dunham"
    BASE_URL = "https://www.thedunhamgroup.com"
    # Commercial properties for sale in Maine
    SEARCH_URL = "https://www.thedunhamgroup.com/properties"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []
        seen_urls = set()

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_browser(p)
                page = context.new_page()

                page.goto(self.SEARCH_URL, timeout=60000)
                # Wait for listings to load
                page.wait_for_timeout(5000)

                # Look for property links
                items = page.query_selector_all("a[href*='/property'], a[href*='/listing'], .property-card a, .listing-card a, [class*='property'] a, [class*='listing'] a")

                for item in items[:100]:  # Limit to first 100 listings
                    try:
                        url = item.get_attribute("href") or ""
                        
                        if not url or url.startswith("#") or url.startswith("javascript:"):
                            continue

                        # Make URL absolute if relative
                        if url.startswith("/"):
                            url = f"{self.BASE_URL}{url}"
                        elif not url.startswith("http"):
                            continue
                        
                        # Filter for property pages
                        if "/propert" not in url.lower() and "/listing" not in url.lower():
                            continue
                        
                        # Skip duplicates
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        # Extract property info
                        link_text = item.inner_text().strip()
                        
                        # Try to get card context
                        title = "Commercial Property"
                        card_text = link_text
                        property_type = ""
                        
                        try:
                            card_element = item.query_selector("xpath=ancestor::*[contains(@class, 'card') or contains(@class, 'property') or contains(@class, 'listing')]")
                            if card_element:
                                card_text = card_element.inner_text().strip()
                                lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                                
                                # First non-empty line is usually title/address
                                if lines:
                                    title = lines[0]
                                
                                # Look for property type
                                for line in lines:
                                    if any(t in line.lower() for t in ['multi-family', 'multifamily', 'industrial', 'retail', 'office', 'investment', 'mixed use']):
                                        property_type = line
                                        break
                        except:
                            pass
                        
                        # Extract price
                        price = ""
                        price_match = re.search(r'\$[\d,]+(?:\.\d{2})?(?:/SF)?(?:\s+Annual)?', card_text, re.IGNORECASE)
                        if price_match:
                            price = price_match.group()

                        # Extract square footage
                        sqft = ""
                        sqft_match = re.search(r'([\d,]+)\s*SF', card_text, re.IGNORECASE)
                        if sqft_match:
                            sqft = sqft_match.group(1)
                        
                        # Extract units
                        units = ""
                        units_match = re.search(r'(\d+)\s*units?', card_text, re.IGNORECASE)
                        if units_match:
                            units = units_match.group(1)
                        
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
                                title=title[:200] if title else "Commercial Property",
                                raw_payload={
                                    "price": price,
                                    "sqft": sqft,
                                    "units": units,
                                    "acres": acres,
                                    "property_type": property_type,
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
