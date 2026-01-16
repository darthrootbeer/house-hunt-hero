"""Shared browser utilities for ingestion adapters."""

from __future__ import annotations

from contextlib import contextmanager
from playwright.sync_api import sync_playwright


STEALTH_SCRIPT = '''
    Object.defineProperty(navigator, "webdriver", {
        get: () => undefined
    });
'''


@contextmanager
def stealth_browser(timeout: int = 60000):
    """Context manager for stealth browser sessions.
    
    Usage:
        with stealth_browser() as page:
            page.goto(url)
            # ... do stuff
    
    Args:
        timeout: Default timeout in milliseconds for page operations
    
    Yields:
        Page: A Playwright page configured with stealth settings
    """
    pw = sync_playwright().start()
    try:
        browser = pw.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
        )
        context.add_init_script(STEALTH_SCRIPT)
        context.set_default_timeout(timeout)
        page = context.new_page()
        
        yield page
        
    finally:
        if 'browser' in locals():
            browser.close()
        pw.stop()


def create_stealth_context(playwright):
    """Create a stealth browser context from an existing playwright instance.
    
    Usage:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            context = create_stealth_context(p)
            page = context.new_page()
    
    Args:
        playwright: A Playwright instance
    
    Returns:
        BrowserContext: A context configured with stealth settings
    """
    browser = playwright.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
    )
    context.add_init_script(STEALTH_SCRIPT)
    return browser, context
