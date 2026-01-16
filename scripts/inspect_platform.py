#!/usr/bin/env python3
"""
Interactive tool for inspecting platform pages and finding CSS selectors.

Usage:
    python scripts/inspect_platform.py <adapter_name>
    python scripts/inspect_platform.py maine_listings
    python scripts/inspect_platform.py --list  # List all available adapters
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

from src.ingestion.registry import get_adapters


def get_adapter_search_url(adapter):
    """Get search URL from adapter."""
    for attr in ['SEARCH_URL', 'search_url', 'BASE_URL', 'base_url']:
        url = getattr(adapter, attr, None)
        if url:
            return url
    return None


def list_adapters():
    """List all available adapters."""
    adapters = get_adapters()
    print("Available adapters:")
    print()
    for adapter in sorted(adapters, key=lambda a: a.source_id):
        url = get_adapter_search_url(adapter)
        print(f"  {adapter.source_id}")
        if url:
            print(f"    URL: {url}")
    print()
    print(f"Total: {len(adapters)} adapters")


def inspect_platform(adapter_name: str, headless: bool = False):
    """
    Inspect a platform interactively.
    
    Args:
        adapter_name: Name of the adapter (e.g., 'maine_listings')
        headless: Run in headless mode (default: False, shows browser)
    """
    # Find adapter
    adapters = get_adapters()
    adapter = None
    for a in adapters:
        if a.source_id == adapter_name:
            adapter = a
            break
    
    if not adapter:
        print(f"Error: Adapter '{adapter_name}' not found")
        print("\nRun 'python scripts/inspect_platform.py --list' to see available adapters")
        return
    
    # Get search URL
    search_url = get_adapter_search_url(adapter)
    if not search_url:
        print(f"Error: No search URL found for adapter '{adapter_name}'")
        return
    
    print("="*70)
    print(f"INSPECTING PLATFORM: {adapter_name}")
    print("="*70)
    print(f"URL: {search_url}")
    print()
    
    # Create output directory
    output_dir = Path(f"reports/inspection/{adapter_name}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Launch browser
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        # Navigate
        print(f"Navigating to {search_url}...")
        try:
            page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
            page.wait_for_timeout(5000)  # Wait for dynamic content
            print("✅ Page loaded")
        except Exception as e:
            print(f"❌ Error loading page: {e}")
            browser.close()
            return
        
        # Take screenshot
        screenshot_path = output_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"📸 Screenshot saved: {screenshot_path}")
        
        # Get page snapshot
        print("\n" + "="*70)
        print("PAGE SNAPSHOT (Interactive Elements)")
        print("="*70)
        
        # Get links
        links = page.query_selector_all("a")
        print(f"\nTotal links found: {len(links)}")
        if links:
            print("\nFirst 10 links:")
            for i, link in enumerate(links[:10], 1):
                href = link.get_attribute("href") or ""
                text = link.inner_text()[:50]
                print(f"  {i}. href='{href[:80]}' text='{text}'")
        
        # Save HTML
        html_path = output_dir / f"page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        html_content = page.content()
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\n💾 HTML saved: {html_path}")
        
        # Interactive selector tester
        print("\n" + "="*70)
        print("INTERACTIVE SELECTOR TESTER")
        print("="*70)
        print("Enter CSS selectors to test (or 'quit' to exit)")
        print("Examples:")
        print("  a[href*='/listing/']")
        print("  .property-card")
        print("  div.result-item")
        print()
        
        findings = []
        
        while True:
            try:
                selector = input("Enter selector (or 'quit'): ").strip()
                
                if selector.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not selector:
                    continue
                
                # Test selector
                try:
                    elements = page.query_selector_all(selector)
                    count = len(elements)
                    
                    print(f"\n✅ Found {count} elements")
                    
                    if count > 0:
                        print(f"\nFirst 3 elements:")
                        for i, el in enumerate(elements[:3], 1):
                            # Get outer HTML (limited)
                            try:
                                html = el.evaluate('el => el.outerHTML')[:300]
                                print(f"\n  Element {i}:")
                                print(f"    {html}")
                                
                                # Try to get text
                                text = el.inner_text()[:100]
                                if text:
                                    print(f"    Text: {text}")
                                
                                # Try to get href
                                href = el.get_attribute("href")
                                if href:
                                    print(f"    href: {href}")
                            except:
                                print(f"    (Could not extract details)")
                        
                        # Record finding
                        findings.append({
                            'selector': selector,
                            'count': count,
                            'success': True
                        })
                    else:
                        print("⚠️  No elements matched this selector")
                        findings.append({
                            'selector': selector,
                            'count': 0,
                            'success': False
                        })
                
                except Exception as e:
                    print(f"❌ Error testing selector: {e}")
                    findings.append({
                        'selector': selector,
                        'error': str(e)
                    })
                
                print()
            
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except EOFError:
                break
        
        # Export findings
        print("\n" + "="*70)
        print("EXPORTING FINDINGS")
        print("="*70)
        
        findings_path = output_dir / f"findings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(findings_path, 'w') as f:
            f.write(f"Platform Inspection Report\n")
            f.write(f"=" * 70 + "\n\n")
            f.write(f"Adapter: {adapter_name}\n")
            f.write(f"URL: {search_url}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"\n")
            f.write(f"Screenshot: {screenshot_path}\n")
            f.write(f"HTML: {html_path}\n")
            f.write(f"\n")
            f.write(f"Selector Test Results\n")
            f.write(f"-" * 70 + "\n\n")
            
            for finding in findings:
                f.write(f"Selector: {finding['selector']}\n")
                if 'error' in finding:
                    f.write(f"  Error: {finding['error']}\n")
                else:
                    status = "✅ Working" if finding['success'] else "❌ No matches"
                    f.write(f"  Status: {status}\n")
                    f.write(f"  Count: {finding['count']}\n")
                f.write(f"\n")
        
        print(f"📝 Findings saved: {findings_path}")
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Adapter: {adapter_name}")
        print(f"URL: {search_url}")
        print(f"Screenshot: {screenshot_path}")
        print(f"HTML: {html_path}")
        print(f"Findings: {findings_path}")
        print(f"Selectors tested: {len(findings)}")
        print()
        
        browser.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Interactive tool for inspecting platform pages and finding CSS selectors',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/inspect_platform.py maine_listings
  python scripts/inspect_platform.py realty_of_maine --headless
  python scripts/inspect_platform.py --list
        """
    )
    parser.add_argument(
        'adapter_name',
        nargs='?',
        help='Name of the adapter to inspect (e.g., maine_listings)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available adapters'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (default: shows browser window)'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_adapters()
        return
    
    if not args.adapter_name:
        parser.print_help()
        print("\nError: adapter_name is required (or use --list to see available adapters)")
        sys.exit(1)
    
    inspect_platform(args.adapter_name, headless=args.headless)


if __name__ == "__main__":
    main()
