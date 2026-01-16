from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing
from ..browser_utils import create_stealth_browser


class BoulosCompanyAdapter(IngestionAdapter):
    """Fetches investment/multi-family listings from The Boulos Company."""

    source_id = "boulos_company"
    BASE_URL = "https://boulos.com"
    # Investment properties page (includes multi-family)
    SEARCH_URL = "https://boulos.com/properties/investment-properties/"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []
        seen_urls = set()

        try:
            with sync_playwright() as p:
                browser, context = create_stealth_browser(p)
                page = context.new_page()

                page.goto(self.SEARCH_URL, timeout=60000)
                # Wait for listings to load (they may be in iframe or dynamically loaded)
                page.wait_for_timeout(5000)

                # Boulos uses embedded search interface - listings are in cards
                # Try multiple selectors to find listing links
                items = page.query_selector_all("a[href*='/property'], a[href*='/listing'], .property-card a, .listing-card a, [class*='property'] a[href*='boulos.com']")

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
                        
                        # Filter for actual property detail pages
                        if "/property" not in url.lower() and "/listing" not in url.lower():
                            continue
                        
                        # Skip duplicates
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        # Extract text content from the card
                        card_text = item.inner_text().strip()
                        
                        # Try to get title from nearby elements
                        title = "Commercial Property"
                        try:
                            # Look for address or property name in card
                            card_element = item.query_selector("xpath=ancestor::*[contains(@class, 'card') or contains(@class, 'property') or contains(@class, 'listing')]")
                            if card_element:
                                card_full_text = card_element.inner_text().strip()
                                lines = [l.strip() for l in card_full_text.split('\n') if l.strip()]
                                if lines:
                                    title = lines[0]  # First line is usually the address/name
                        except:
                            pass
                        
                        # Extract price from card text
                        price = ""
                        price_match = re.search(r'\$[\d,]+', card_text)
                        if price_match:
                            price = price_match.group()

                        # Extract square footage
                        sqft = ""
                        sqft_match = re.search(r'([\d,]+)\s*SF', card_text, re.IGNORECASE)
                        if sqft_match:
                            sqft = sqft_match.group(1)

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title[:200] if title else "Commercial Property",
                                raw_payload={
                                    "price": price,
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
