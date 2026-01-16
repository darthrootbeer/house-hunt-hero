from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class LandingRealEstateAdapter(IngestionAdapter):
    """Fetches listings from Landing Real Estate (landinghomesmaine.com)."""

    source_id = "landing_real_estate"
    BASE_URL = "https://landinghomesmaine.com"
    # Their IDX listings page sorted by most recently updated
    SEARCH_URL = "https://landinghomesmaine.com/our-listings/"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []

        try:
            with sync_playwright() as p:
                # Use stealth settings to avoid bot detection
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                )
                # Mask automation detection
                context.add_init_script('''
                    Object.defineProperty(navigator, "webdriver", {
                        get: () => undefined
                    });
                ''')
                page = context.new_page()

                page.goto(self.SEARCH_URL, timeout=60000)
                page.wait_for_timeout(5000)  # Wait for dynamic content

                # Landing uses IDX feed with links like /idx/ADDRESS-mls_XXXXX
                # Find all property listing links
                items = page.query_selector_all("a[href*='/idx/']")

                for item in items[:50]:  # Limit to first 50 listings
                    try:
                        url = item.get_attribute("href") or ""
                        
                        if not url or url.startswith("#") or url.startswith("javascript:"):
                            continue

                        if url.startswith("/"):
                            url = f"{self.BASE_URL}{url}"
                        elif not url.startswith("http"):
                            continue
                        
                        # Skip if not a property listing URL (should contain mls_)
                        if "mls_" not in url:
                            continue

                        # Get the full link text which contains property info
                        link_text = item.inner_text().strip()
                        
                        # Try to find property image which often has price overlay
                        img = item.query_selector("img")
                        img_alt = img.get_attribute("alt") if img else ""
                        
                        # Extract price (e.g., "$365,000")
                        price = ""
                        price_match = re.search(r'\$[\d,]+', link_text)
                        if price_match:
                            price = price_match.group()
                        
                        # Extract address - look for line with street pattern
                        # Format is like: "$499,900\n143 Hollis Road, Dayton, ME\nPending..."
                        title = ""
                        lines = link_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            # Address line typically has comma and state code
                            if ', ME' in line and not line.startswith('$'):
                                title = line
                                break
                        
                        if not title and img_alt and "Property photo for" in img_alt:
                            title = img_alt.replace("Property photo for ", "").strip()
                        
                        if not title:
                            title = "Landing Real Estate Property"
                        
                        # Extract status
                        status = ""
                        if "Active" in link_text:
                            status = "Active"
                        elif "Pending" in link_text:
                            status = "Pending"
                        elif "Closed" in link_text:
                            status = "Closed"
                        
                        # Extract beds/baths/sqft from link text
                        beds = ""
                        baths = ""
                        sqft = ""
                        beds_match = re.search(r'(\d+)BD', link_text)
                        baths_match = re.search(r'(\d+)BA', link_text)
                        sqft_match = re.search(r'([\d,]+)SF', link_text)
                        if beds_match:
                            beds = beds_match.group(1)
                        if baths_match:
                            baths = baths_match.group(1)
                        if sqft_match:
                            sqft = sqft_match.group(1)

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "status": status,
                                    "beds": beds,
                                    "baths": baths,
                                    "sqft": sqft,
                                    "full_text": link_text[:500],
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
