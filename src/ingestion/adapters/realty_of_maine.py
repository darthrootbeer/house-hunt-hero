from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List

from playwright.sync_api import TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing
from ..browser_utils import stealth_browser


class RealtyOfMaineAdapter(IngestionAdapter):
    """Fetches listings from Realty of Maine (realtyofmaine.com)."""

    source_id = "realty_of_maine"
    BASE_URL = "https://www.realtyofmaine.com"
    # Their listings page - has IDX feed with all listings
    SEARCH_URL = "https://www.realtyofmaine.com/listings/"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []
        seen_urls = set()

        try:
            with stealth_browser() as page:
                page.goto(self.SEARCH_URL, timeout=60000)
                page.wait_for_timeout(10000)  # Wait for IDX feed to load

                # Realty of Maine uses /listing/ID/ADDRESS/ URL pattern
                items = page.query_selector_all("a[href*='/listing/']")

                for item in items[:100]:
                    try:
                        url = item.get_attribute("href") or ""
                        
                        if not url or url.startswith("#") or url.startswith("javascript:"):
                            continue

                        # Skip non-detail URLs (just /listings/ without ID)
                        if url.count('/') < 4:
                            continue

                        if url.startswith("/"):
                            url = f"{self.BASE_URL}{url}"
                        elif not url.startswith("http"):
                            continue
                        
                        # Skip duplicates
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        # Get link text for address/details
                        # Format: "1/43\n$315,000\nNaples, ME\n16 Mason Avenue\n3 Beds1 Bath1,500 SqFt"
                        link_text = item.inner_text().strip()
                        lines = link_text.split('\n')
                        
                        # Extract address - look for the street name line
                        title = ""
                        location = ""
                        for line in lines:
                            line = line.strip()
                            if ', ME' in line:
                                location = line
                            elif re.search(r'\d+\s+\w+', line) and not line.startswith('$') and 'Bed' not in line and 'Bath' not in line:
                                if not title:
                                    title = line
                        
                        if title and location:
                            title = f"{title}, {location}"
                        elif location:
                            title = location
                        elif not title:
                            title = "Realty of Maine Property"
                        
                        # Extract price
                        price = ""
                        price_match = re.search(r'\$[\d,]+', link_text)
                        if price_match:
                            price = price_match.group()
                        
                        # Extract beds/baths/sqft
                        beds = ""
                        baths = ""
                        sqft = ""
                        beds_match = re.search(r'(\d+)\s*Bed', link_text)
                        baths_match = re.search(r'(\d+)\s*Bath', link_text)
                        sqft_match = re.search(r'([\d,]+)\s*SqFt', link_text)
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
                                    "location": location,
                                    "beds": beds,
                                    "baths": baths,
                                    "sqft": sqft,
                                },
                            )
                        )
                    except Exception:
                        continue

        except PlaywrightTimeout:
            pass
        except Exception:
            pass

        return listings
