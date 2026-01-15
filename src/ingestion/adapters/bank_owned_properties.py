from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class BankOwnedPropertiesAdapter(IngestionAdapter):
    """Fetches REO/bank-owned property listings from BankOwnedProperties.org."""

    source_id = "bank_owned_properties"
    # Maine listings on BankOwnedProperties.org
    SEARCH_URL = "https://www.bankownedproperties.org/bankhomes/MAINE.html"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })

                page.goto(self.SEARCH_URL, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)

                # Try various selectors for listings
                # Common patterns: .listing, .property, .result-item, table rows with property data
                items = page.query_selector_all(
                    ".listing, .property, .result-item, "
                    "[class*='listing'], [class*='property'], "
                    "table tr, .property-card, .home-card"
                )

                if not items:
                    # Try looking for links that might be listings
                    items = page.query_selector_all("a[href*='/bankhomes'], a[href*='/property'], a[href*='/listing']")

                for item in items[:100]:  # Limit to first 100 listings
                    try:
                        # Try to get URL
                        url = ""
                        if item.tag_name == "a":
                            url = item.get_attribute("href") or ""
                        else:
                            link = item.query_selector("a")
                            url = link.get_attribute("href") if link else ""

                        # If no URL found, skip (or construct one if we have property ID)
                        if not url or url.startswith("#") or url.startswith("javascript:"):
                            # Try to find address or property identifier to construct URL
                            address_el = item.query_selector(".address, [class*='address'], .location")
                            if not address_el:
                                continue
                            # Construct a potential listing URL from the property details
                            url = f"{self.SEARCH_URL}#{item.get_attribute('id') or ''}"

                        # Make URL absolute if relative
                        if url and url.startswith("/"):
                            url = f"https://www.bankownedproperties.org{url}"
                        elif url and not url.startswith("http"):
                            url = f"https://www.bankownedproperties.org/{url}"

                        # Try to get title/address
                        title_el = item.query_selector("h2, h3, h4, .title, [class*='title'], .address, [class*='address']")
                        title = title_el.inner_text().strip() if title_el else "No title"

                        # Try to get price
                        price_el = item.query_selector(".price, [class*='price'], [class*='cost']")
                        price = price_el.inner_text().strip() if price_el else ""

                        # Try to get location
                        location_el = item.query_selector(".location, [class*='location'], .city, .county")
                        location = location_el.inner_text().strip() if location_el else ""

                        # Try to get beds/baths
                        beds_el = item.query_selector("[class*='bed'], [class*='bath']")
                        beds_baths = beds_el.inner_text().strip() if beds_el else ""

                        # Skip if no meaningful data
                        if not title or title == "No title":
                            continue

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url if url else self.SEARCH_URL,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "location": location,
                                    "beds_baths": beds_baths,
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
