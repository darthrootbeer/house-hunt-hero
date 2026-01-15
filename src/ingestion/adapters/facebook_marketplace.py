from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class FacebookMarketplaceAdapter(IngestionAdapter):
    """
    Fetches real estate listings from Facebook Marketplace.
    
    Note: Facebook aggressively blocks scrapers and requires authentication.
    This adapter attempts basic scraping but may need Graph API access or
    more sophisticated handling to work reliably.
    """

    source_id = "facebook_marketplace"
    # Facebook Marketplace search for Maine real estate
    # Note: This URL pattern may need adjustment based on Facebook's current structure
    SEARCH_URL = "https://www.facebook.com/marketplace/maine/search/?query=house&exact=false"

    def fetch(self) -> List[RawListing]:
        listings: List[RawListing] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                page.goto(self.SEARCH_URL, timeout=30000)
                # Facebook may redirect or require login - handle gracefully
                page.wait_for_load_state("domcontentloaded", timeout=15000)

                # Check if we're on a login page or blocked
                page_title = page.title().lower()
                if "log in" in page_title or "login" in page_title or "sign in" in page_title:
                    # Facebook is requiring login - return empty list
                    browser.close()
                    return []

                # Try to find marketplace listings
                # Facebook Marketplace uses dynamic loading - may need to scroll
                items = page.query_selector_all(
                    "[data-testid='marketplace-product-item'], "
                    "[role='article'], "
                    "a[href*='/marketplace/item/'], "
                    ".marketplace-item, "
                    "[class*='marketplace']"
                )

                # If no items found, try scrolling to trigger lazy loading
                if not items:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)  # Wait for content to load
                    items = page.query_selector_all(
                        "[data-testid='marketplace-product-item'], "
                        "[role='article'], "
                        "a[href*='/marketplace/item/']"
                    )

                for item in items[:50]:
                    try:
                        # Try to get link
                        link = item.query_selector("a[href*='/marketplace/item/']") if item.tag_name != "a" else item
                        if not link:
                            continue

                        url = link.get_attribute("href") or ""
                        if not url or url.startswith("#"):
                            continue

                        # Make URL absolute
                        if url.startswith("/"):
                            url = f"https://www.facebook.com{url}"

                        # Try to get title
                        title_el = item.query_selector("span, div, [class*='title'], [class*='name']")
                        title = title_el.inner_text().strip() if title_el and title_el.inner_text() else "No title"

                        # Try to get price
                        price_el = item.query_selector("[class*='price'], [class*='cost']")
                        price = price_el.inner_text().strip() if price_el and price_el.inner_text() else ""

                        # Try to get location
                        location_el = item.query_selector("[class*='location'], [class*='city']")
                        location = location_el.inner_text().strip() if location_el and location_el.inner_text() else ""

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title if title else "No title",
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
        except Exception as e:
            # Facebook may block requests - return empty list gracefully
            pass

        return listings
