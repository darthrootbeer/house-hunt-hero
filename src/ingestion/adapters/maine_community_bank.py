from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class MaineCommunityBankAdapter(IngestionAdapter):
    """Fetches REO/bank-owned property listings from Maine Community Bank."""

    source_id = "maine_community_bank"
    # Maine Community Bank REO listings page
    SEARCH_URL = "https://maine.bank/personal/home-loans/bank-owned-properties/"

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

                # Check if page says "no properties available"
                page_text = page.inner_text("body").lower()
                if "no properties available" in page_text or "no properties" in page_text:
                    browser.close()
                    return listings  # Return empty list if no properties

                # Try various selectors for property listings
                items = page.query_selector_all(
                    ".property, .listing, .result-item, "
                    "[class*='property'], [class*='listing'], "
                    ".property-card, .home-card, .reo-listing, "
                    "[class*='reo'], table tr"
                )

                if not items:
                    # Try looking for links that might be listings
                    items = page.query_selector_all("a[href*='/property'], a[href*='/listing'], a[href*='/reo']")

                for item in items[:50]:  # Limit to first 50 listings
                    try:
                        # Try to get URL
                        url = ""
                        if item.tag_name == "a":
                            url = item.get_attribute("href") or ""
                        else:
                            link = item.query_selector("a")
                            url = link.get_attribute("href") if link else ""

                        # If no URL found, skip
                        if not url or url.startswith("#") or url.startswith("javascript:"):
                            continue

                        # Make URL absolute if relative
                        if url.startswith("/"):
                            url = f"https://maine.bank{url}"
                        elif not url.startswith("http"):
                            url = f"https://maine.bank/{url}"

                        # Try to get title/address
                        title_el = item.query_selector("h2, h3, h4, .title, [class*='title'], .address, [class*='address']")
                        title = title_el.inner_text().strip() if title_el else "No title"

                        # Try to get price
                        price_el = item.query_selector(".price, [class*='price'], [class*='cost']")
                        price = price_el.inner_text().strip() if price_el else ""

                        # Try to get location
                        location_el = item.query_selector(".location, [class*='location'], .city, .county")
                        location = location_el.inner_text().strip() if location_el else ""

                        # Skip if no meaningful data
                        if not title or title == "No title":
                            continue

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "location": location,
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
