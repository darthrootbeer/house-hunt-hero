from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class MaineStateMLSAdapter(IngestionAdapter):
    """Fetches listings from Maine State MLS (mainestatemls.com) - Statewide and nationwide MLS service."""

    source_id = "maine_state_mls"
    # Home page - may need to navigate to search/IDX interface
    BASE_URL = "https://mainestatemls.com"
    # Try common IDX search URLs
    SEARCH_URL = "https://mainestatemls.com/search/"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })

                # Try the search URL first
                try:
                    page.goto(self.SEARCH_URL, timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=20000)
                except Exception:
                    # If search URL doesn't work, try home page and look for search interface
                    page.goto(self.BASE_URL, timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=20000)

                # Look for IDX search widget or listing elements
                # IDX plugins often use: .idx-results, .property-results, .listing-results, etc.
                items = page.query_selector_all(
                    ".idx-results .property, .idx-results .listing, "
                    ".property-results .property, .listing-results .listing, "
                    ".property-card, .listing-card, .result-item, "
                    "[class*='property-card'], [class*='listing-card'], "
                    "a[href*='/property'], a[href*='/listing'], a[href*='/detail'], "
                    "[data-property-id], [data-listing-id]"
                )

                if not items:
                    # Try more generic selectors
                    items = page.query_selector_all("[class*='property'], [class*='listing'], [class*='result']")

                for item in items[:100]:  # Limit to first 100 listings
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
                            url = f"{self.BASE_URL}{url}"
                        elif not url.startswith("http"):
                            continue

                        # Try to get title/address
                        title_el = item.query_selector("h2, h3, h4, .title, [class*='title'], .address, [class*='address'], .property-address")
                        title = title_el.inner_text().strip() if title_el else "Maine State MLS Listing"

                        # Try to get price
                        price_el = item.query_selector(".price, [class*='price'], .property-price")
                        price = price_el.inner_text().strip() if price_el else ""

                        # Try to get location/address
                        location_el = item.query_selector(
                            ".location, [class*='location'], .address, [class*='address'], .property-location"
                        )
                        location = location_el.inner_text().strip() if location_el else ""

                        # Try to get MLS number
                        mls_el = item.query_selector(".mls-number, [class*='mls'], [data-mls]")
                        mls_number = mls_el.inner_text().strip() if mls_el else (item.get_attribute("data-mls") or "")

                        # Try to get property details
                        details_el = item.query_selector(".property-details, [class*='details'], .beds-baths")
                        details = details_el.inner_text().strip() if details_el else ""

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "location": location,
                                    "mls_number": mls_number,
                                    "details": details,
                                },
                            )
                        )
                    except Exception:
                        continue

                browser.close()

        except PlaywrightTimeout:
            pass
        except Exception as e:
            # Log error for debugging but don't fail completely
            pass

        return listings
