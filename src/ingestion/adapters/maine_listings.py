from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class MaineListingsAdapter(IngestionAdapter):
    """Fetches listings from Maine Listings (mainelistings.com) - Official statewide MLS."""

    source_id = "maine_listings"
    BASE_URL = "https://mainelistings.com"
    # Main listings page
    SEARCH_URL = "https://mainelistings.com/listings"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []
        seen_urls = set()

        try:
            with sync_playwright() as p:
                # Use stealth settings to bypass Cloudflare
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                )
                context.add_init_script('''
                    Object.defineProperty(navigator, "webdriver", {
                        get: () => undefined
                    });
                ''')
                page = context.new_page()

                page.goto(self.SEARCH_URL, timeout=60000)
                page.wait_for_timeout(15000)  # Wait for Cloudflare and content load

                # Maine Listings uses URL format: /listings/ME/CITY/ZIP/ID/ADDRESS/MLSNUMBER
                # Find all listing links
                items = page.query_selector_all("a[href*='/listings/ME/']")

                for item in items[:100]:  # Limit to first 100 listings
                    try:
                        url = item.get_attribute("href") or ""
                        
                        if not url or url.startswith("#") or url.startswith("javascript:"):
                            continue

                        # Skip non-detail links (main page links, etc)
                        if url.count('/') < 6:  # Detail URLs have many segments
                            continue

                        # Make URL absolute if relative
                        if url.startswith("/"):
                            url = f"{self.BASE_URL}{url}"
                        elif not url.startswith("http"):
                            continue
                        
                        # Skip duplicates
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        # Extract address from URL
                        # Format: /listings/ME/CITY/ZIP/ID/address-city-me-zip/MLSID
                        parts = url.split('/')
                        address_part = parts[-2] if len(parts) >= 2 else ""
                        mls_number = parts[-1] if len(parts) >= 1 else ""
                        
                        # Convert URL slug to readable title
                        title = address_part.replace('-', ' ').title() if address_part else "Maine Listing"
                        
                        # Get link text for additional info
                        link_text = item.inner_text().strip()
                        
                        # Try to extract price from link text
                        price = ""
                        price_match = re.search(r'\$[\d,]+', link_text)
                        if price_match:
                            price = price_match.group()

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "mls_number": mls_number,
                                    "link_text": link_text[:200] if link_text else "",
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
