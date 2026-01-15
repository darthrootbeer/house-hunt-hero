from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class MunicipalTaxAssessorAdapter(IngestionAdapter):
    """
    Fetches tax-acquired property listings from municipal tax assessor websites.
    Note: As of Aug 2024, many municipalities must list through licensed brokers.
    This adapter can be configured for municipalities that still publish directly.
    """

    source_id = "municipal_tax_assessor"
    # This will be overridden by config or can be set per municipality
    SEARCH_URL = None
    municipality_name = None

    def __init__(self, search_url: str = None, municipality_name: str = None):
        """Initialize with optional search URL and municipality name."""
        if search_url:
            self.SEARCH_URL = search_url
        if municipality_name:
            self.municipality_name = municipality_name
        super().__init__()

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []

        if not self.SEARCH_URL:
            # No URL configured - return empty list
            return listings

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })

                page.goto(self.SEARCH_URL, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)

                # Look for tax-acquired property listings
                # Common patterns vary by municipality
                items = page.query_selector_all(
                    ".tax-acquired, .tax-foreclosure, .tax-sale, [class*='tax-acquired'], "
                    "[class*='tax-foreclosure'], [class*='tax-sale'], .property, .listing, "
                    "a[href*='tax'], a[href*='foreclosure'], a[href*='acquired']"
                )

                if not items:
                    # Try alternative approach
                    items = page.query_selector_all("a[href*='property'], a[href*='listing']")

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
                            # Extract base URL from SEARCH_URL
                            from urllib.parse import urlparse
                            parsed = urlparse(self.SEARCH_URL)
                            base = f"{parsed.scheme}://{parsed.netloc}"
                            url = f"{base}{url}"
                        elif not url.startswith("http"):
                            from urllib.parse import urlparse
                            parsed = urlparse(self.SEARCH_URL)
                            base = f"{parsed.scheme}://{parsed.netloc}"
                            url = f"{base}/{url}"

                        # Try to get title
                        title_el = item.query_selector("h2, h3, h4, .title, [class*='title']")
                        title = title_el.inner_text() if title_el else "Tax-Acquired Property"

                        # Try to get address/location
                        location_el = item.query_selector(
                            ".location, [class*='location'], .address, [class*='address']"
                        )
                        location = location_el.inner_text() if location_el else ""

                        # Try to get price
                        price_el = item.query_selector(".price, [class*='price']")
                        price = price_el.inner_text() if price_el else ""

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "location": location,
                                    "municipality": self.municipality_name or "",
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
