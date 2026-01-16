"""Shared browser utilities for ingestion adapters."""

from __future__ import annotations

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


def create_stealth_browser():
    """Create a Playwright browser with stealth settings to avoid bot detection.
    
    Returns:
        tuple: (playwright_instance, browser, context, page)
        
    Usage:
        pw, browser, context, page = create_stealth_browser()
        try:
            page.goto(url)
            # ... do stuff
        finally:
            browser.close()
            pw.stop()
    """
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
    )
    # Mask automation detection
    context.add_init_script('''
        Object.defineProperty(navigator, "webdriver", {
            get: () => undefined
        });
    ''')
    page = context.new_page()
    
    return pw, browser, context, page


class StealthBrowser:
    """Context manager for stealth browser sessions."""
    
    def __init__(self):
        self.pw = None
        self.browser = None
        self.context = None
        self.page = None
    
    def __enter__(self):
        self.pw, self.browser, self.context, self.page = create_stealth_browser()
        return self.page
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.pw:
            self.pw.stop()
        return False
