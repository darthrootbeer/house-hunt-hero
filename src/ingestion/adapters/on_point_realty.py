from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class OnPointRealtyAdapter(IngestionAdapter):
    """Fetches State Tax-Acquired Properties from On Point Realty (Maine Revenue Services broker)."""

    source_id = "on_point_realty"
    SEARCH_URL = "https://onpointrealtyme.com/state-tax-acquired-properties/"

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

                # Try various selectors for property listings
                # Real estate sites commonly use: .property, .listing, .property-card, etc.
                items = page.query_selector_all(
                    ".property, .listing, .property-card, [class*='property'], [class*='listing'], "
                    ".property-item, .listing-item, article.property, article.listing"
                )

                if not items:
                    # Try alternative approach - look for links that might be listings
                    items = page.query_selector_all("a[href*='/property'], a[href*='/listing'], a[href*='/detail']")

                for item in items[:50]:  # Limit to first 50 listings
                    try:
                        # Try to get URL
                        if item.tag_name == "a":
                            url = item.get_attribute("href") or ""
                        else:
                            link = item.query_selector("a")
                            url = link.get_attribute("href") if link else ""

                        if not url or url.startswith("#"):
                            continue

                        # Make URL absolute if relative
                        if url.startswith("/"):
                            url = f"https://onpointrealtyme.com{url}"
                        elif not url.startswith("http"):
                            url = f"https://onpointrealtyme.com/{url}"

                        # Try to get title
                        title_el = item.query_selector("h2, h3, h4, .title, [class*='title'], .property-title")
                        title = title_el.inner_text() if title_el else "State Tax-Acquired Property"

                        # Try to get price
                        price_el = item.query_selector(".price, [class*='price'], .property-price")
                        price = price_el.inner_text() if price_el else ""

                        # Try to get location/address
                        location_el = item.query_selector(
                            ".location, [class*='location'], .address, [class*='address'], .property-address"
                        )
                        location = location_el.inner_text() if location_el else ""

                        # Try to get description/details
                        desc_el = item.query_selector(".description, [class*='description'], .property-details")
                        description = desc_el.inner_text() if desc_el else ""

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "location": location,
                                    "description": description,
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
