from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class FSBOHomeListingsAdapter(IngestionAdapter):
    """Fetches FSBO listings from FSBOHomeListings.com."""

    source_id = "fsbo_home_listings"
    
    # Major Maine cities to search
    CITIES = ["Portland", "Bangor", "Lewiston", "Auburn", "Biddeford", "Sanford", "Augusta", "Saco"]

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []
        seen_urls = set()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })

                # Search each major city
                for city in self.CITIES:
                    try:
                        url = f"https://www.fsbohomelistings.com/ME/{city}"
                        page.goto(url, timeout=30000)
                        page.wait_for_timeout(3000)  # Wait for dynamic content

                        # Find all listing links - they're in h4 headings with links to /details/
                        listing_links = page.query_selector_all("h4 a[href*='/details/']")

                        for link in listing_links:
                            try:
                                listing_url = link.get_attribute("href") or ""
                                if not listing_url or listing_url in seen_urls:
                                    continue

                                seen_urls.add(listing_url)

                                # URL is already absolute on this site
                                if listing_url.startswith("/"):
                                    listing_url = f"https://www.fsbohomelistings.com{listing_url}"

                                # Get title from link text
                                title = link.inner_text().strip() if link.inner_text() else "No title"

                                # Find the parent container to get more details
                                # The structure has address and price info as siblings after the h4
                                parent = link.evaluate_handle("el => el.closest('h4').parentElement")

                                # Try to extract price from sibling list items
                                price = ""
                                try:
                                    price_items = parent.query_selector_all("li")
                                    for li in price_items:
                                        text = li.inner_text()
                                        if "$" in text:
                                            price = text.strip()
                                            break
                                except Exception:
                                    pass

                                listings.append(
                                    RawListing(
                                        source=self.source_id,
                                        source_timestamp=datetime.now(timezone.utc),
                                        listing_url=listing_url,
                                        title=title,
                                        raw_payload={
                                            "price": price,
                                            "location": city,
                                        },
                                    )
                                )
                            except Exception:
                                continue

                    except Exception:
                        # Continue to next city if one fails
                        continue

                browser.close()

        except Exception:
            pass

        return listings
