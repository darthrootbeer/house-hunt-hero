from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ..base import IngestionAdapter, RawListing


class FacebookGroupsAdapter(IngestionAdapter):
    """
    Fetches real estate listings from Facebook Groups.
    
    Note: Facebook Groups require group membership and authentication.
    This adapter attempts basic scraping but will likely return empty results
    without proper authentication. May need Graph API access or manual group IDs.
    
    Common Maine real estate groups:
    - Maine Real Estate Buy/Sell/Trade
    - Maine Homes for Sale
    - Portland Maine Real Estate
    """

    source_id = "facebook_groups"
    # Default to a general Maine real estate search
    # Note: Actual group IDs should be configured in source config
    # Format: https://www.facebook.com/groups/{group_id}/search/?query=house
    SEARCH_URL = "https://www.facebook.com/groups/search/?q=maine%20real%20estate"

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
                if "log in" in page_title or "login" in page_title or "sign in" in page_title:
                    # Facebook is requiring login - return empty list
                    browser.close()
                    return []

                # Try to find group posts
                items = page.query_selector_all(
                    "[role='article'], "
                    ".userContentWrapper, "
                    "[data-pagelet], "
                    "a[href*='/groups/']"
                )

                # If no items found, try scrolling
                if not items:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                    items = page.query_selector_all("[role='article']")

                for item in items[:50]:
                    try:
                        # Try to find a link to the post
                        link = item.query_selector("a[href*='/posts/'], a[href*='/permalink/']")
                        if not link:
                            continue

                        url = link.get_attribute("href") or ""
                        if not url or url.startswith("#"):
                            continue

                        if url.startswith("/"):
                            url = f"https://www.facebook.com{url}"

                        # Try to get post text as title
                        text_el = item.query_selector(
                            "[data-testid='post_message'], "
                            ".userContent, "
                            "[class*='text'], "
                            "span"
                        )
                        title = ""
                        if text_el:
                            title_text = text_el.inner_text().strip()
                            # Use first 100 chars as title
                            title = title_text[:100] if title_text else "No title"

                        if not title:
                            title = "No title"

                        # Try to get price from post text
                        item_text = item.inner_text().lower()
                        price = ""
                        if "$" in item_text:
                            # Try to extract price pattern
                            import re
                            price_match = re.search(r'\$[\d,]+', item.inner_text())
                            price = price_match.group(0) if price_match else ""

                        listings.append(
                            RawListing(
                                source=self.source_id,
                                source_timestamp=datetime.now(timezone.utc),
                                listing_url=url,
                                title=title,
                                raw_payload={
                                    "price": price,
                                    "source_type": "facebook_group",
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
