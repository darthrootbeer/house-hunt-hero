from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class NextdoorAdapter(IngestionAdapter):
    """
    Fetches real estate listings from Nextdoor.
    
    Note: Nextdoor requires neighborhood verification and authentication.
    This adapter attempts basic scraping but may need login or API access
    to retrieve listings. Neighborhoods like Gorham, Brunswick, and other
    Maine communities are active on Nextdoor.
    """

    source_id = "nextdoor"
    # Nextdoor search for real estate in Maine
    # Note: May require authentication or neighborhood membership
    SEARCH_URL = "https://nextdoor.com/search/?query=house%20for%20sale&location=Maine"

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
                page.wait_for_load_state("domcontentloaded", timeout=15000)

                # Check if we're on a login page or blocked
                page_title = page.title().lower()
                page_url = page.url.lower()
                
                if "log in" in page_title or "login" in page_title or "sign in" in page_title:
                    # Nextdoor is requiring login - return empty list
                    browser.close()
                    return []

                if "join" in page_url or "login" in page_url or "signup" in page_url:
                    # Redirected to join/login page
                    browser.close()
                    return []

                # Try to find listings/posts
                items = page.query_selector_all(
                    "[data-testid*='post'], "
                    "[data-testid*='listing'], "
                    "[role='article'], "
                    ".post, "
                    "[class*='post'], "
                    "[class*='listing']"
                )

                # If no items found, try scrolling
                if not items:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                    items = page.query_selector_all(
                        "[data-testid*='post'], "
                        "[role='article'], "
                        ".post"
                    )

                for item in items[:50]:
                    try:
                        # Try to find a link to the post/listing
                        link = item.query_selector("a[href*='/post/'], a[href*='/p/']")
                        if not link:
                            # Try alternative - look for any link in the item
                            link = item.query_selector("a[href]")
                        
                        if not link:
                            continue

                        url = link.get_attribute("href") or ""
                        if not url or url.startswith("#"):
                            continue

                        if url.startswith("/"):
                            url = f"https://nextdoor.com{url}"

                        # Try to get post title/text
                        title_el = item.query_selector(
                            "h2, h3, [class*='title'], [class*='headline'], "
                            "[data-testid*='title'], "
                            "span, div"
                        )
                        title = ""
                        if title_el:
                            title_text = title_el.inner_text().strip()
                            # Use first 100 chars as title
                            title = title_text[:100] if title_text else "No title"

                        # Try to get price from post text
                        item_text = item.inner_text().lower()
                        price = ""
                        if "$" in item_text:
                            import re
                            price_match = re.search(r'\$[\d,]+', item.inner_text())
                            price = price_match.group(0) if price_match else ""

                        # Try to get location/neighborhood
                        location_el = item.query_selector(
                            "[class*='location'], [class*='neighborhood'], "
                            "[class*='city'], [class*='address']"
                        )
                        location = location_el.inner_text().strip() if location_el and location_el.inner_text() else ""

                        if not title:
                            title = "No title"

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "location": location,
                                    "source_type": "nextdoor_post",
                                },
                            )
                        )
                    except Exception:
                        continue

                browser.close()

        except PlaywrightTimeout:
            pass
        except Exception as e:
            # Nextdoor may block requests - return empty list gracefully
            pass

        return listings
