from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class HomesAuctionAdapter(IngestionAdapter):
    """Fetches auction property listings from Homes.com auction section."""

    source_id = "homes_auction"
    # Maine auction listings
    SEARCH_URL = "https://www.homes.com/maine/auction/"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })

                page.goto(self.SEARCH_URL, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)

                # Look for auction property listings
                # Homes.com uses property cards/listing items
                items = page.query_selector_all(
                    ".property-card, .listing-item, .property-item, [class*='property-card'], "
                    "[class*='listing'], [class*='property'], .search-results-item, .auction-property"
                )

                if not items:
                    # Try alternative approach - look for links
                    items = page.query_selector_all("a[href*='/property'], a[href*='/auction'], a[href*='/listing']")

                for item in items[:50]:  # Limit to first 50 listings
                    try:
                        # Try to get URL
                        if item.tag_name == "a":
                            url = item.get_attribute("href") or ""
                        else:
                            link = item.query_selector("a")
                            url = link.get_attribute("href") if link else ""

                        if not url or url.startswith("#") or url.startswith("javascript:"):
                            continue

                        # Make URL absolute if relative
                        if url.startswith("/"):
                            url = f"https://www.homes.com{url}"
                        elif not url.startswith("http"):
                            url = f"https://www.homes.com/{url}"

                        # Try to get title/address
                        title_el = item.query_selector(
                            "h2, h3, h4, .address, .property-address, .title, [class*='title'], [class*='address']"
                        )
                        title = title_el.inner_text() if title_el else "Auction Property"

                        # Try to get price/starting bid
                        price_el = item.query_selector(
                            ".price, [class*='price'], .bid, .starting-bid, .auction-price, [class*='bid']"
                        )
                        price = price_el.inner_text() if price_el else ""

                        # Try to get location/address
                        location_el = item.query_selector(
                            ".location, [class*='location'], .address, [class*='address'], .city-state"
                        )
                        location = location_el.inner_text() if location_el else ""

                        # Try to get auction date
                        date_el = item.query_selector(
                            ".date, [class*='date'], .auction-date, [class*='auction-date'], .event-date"
                        )
                        auction_date = date_el.inner_text() if date_el else ""

                        # Try to get property details (bedrooms, baths, sqft)
                        details_el = item.query_selector(
                            ".property-details, [class*='details'], .beds-baths, [class*='specs']"
                        )
                        details = details_el.inner_text() if details_el else ""

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "location": location,
                                    "auction_date": auction_date,
                                    "details": details,
                                    "type": "auction",
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
