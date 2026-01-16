"""
Test CSS selectors on live pages to validate they match elements.

This script helps identify broken selectors by testing them directly on live pages
without running the full adapter logic.
"""

import argparse
import inspect
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright, Page

from src.ingestion.registry import get_adapters


def extract_selectors_from_adapter(adapter) -> List[str]:
    """
    Extract CSS selectors from adapter source code.
    
    Looks for query_selector_all() calls and extracts the selector strings.
    """
    selectors = []
    
    # Get the source code of the adapter class
    try:
        source = inspect.getsource(adapter.__class__)
        
        # Find all query_selector_all calls
        # Pattern: page.query_selector_all("selector") or page.query_selector_all('selector')
        pattern = r'query_selector_all\(["\']([^"\']+)["\']\)'
        matches = re.findall(pattern, source)
        selectors.extend(matches)
        
        # Also check for query_selector calls
        pattern = r'query_selector\(["\']([^"\']+)["\']\)'
        matches = re.findall(pattern, source)
        selectors.extend(matches)
        
    except Exception as e:
        print(f"  Warning: Could not extract selectors: {e}")
    
    return selectors


def get_adapter_search_url(adapter) -> str:
    """Get the search URL from adapter."""
    # Try different attribute names
    for attr in ['SEARCH_URL', 'search_url', 'BASE_URL', 'base_url']:
        url = getattr(adapter, attr, None)
        if url:
            return url
    return ""


def test_selector_on_page(page: Page, selector: str) -> Tuple[int, str]:
    """
    Test a selector on a page and return count and sample HTML.
    
    Returns:
        (count, sample_html)
    """
    try:
        elements = page.query_selector_all(selector)
        count = len(elements)
        
        # Get sample HTML from first element
        sample_html = ""
        if elements:
            try:
                # Get outer HTML of first element (limited to 500 chars)
                sample_html = elements[0].evaluate('el => el.outerHTML')[:500]
            except:
                sample_html = "[Could not extract HTML]"
        
        return count, sample_html
    except Exception as e:
        return 0, f"[Error: {str(e)[:100]}]"


def validate_adapters(adapter_ids: List[str], all_empty: bool = False) -> Dict:
    """
    Validate selectors for specified adapters.
    
    Args:
        adapter_ids: List of adapter IDs to test (empty = test all)
        all_empty: If True, test all adapters that returned zero properties
    
    Returns:
        Dict with validation results
    """
    all_adapters = get_adapters()
    
    # Filter adapters to test
    if adapter_ids:
        adapters_to_test = [a for a in all_adapters if a.source_id in adapter_ids]
    elif all_empty:
        # Would need to track which adapters return zero - for now test all
        adapters_to_test = all_adapters
    else:
        adapters_to_test = all_adapters
    
    results = {}
    
    print(f"Testing selectors for {len(adapters_to_test)} adapters...\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        for i, adapter in enumerate(adapters_to_test, 1):
            adapter_id = adapter.source_id
            print(f"[{i}/{len(adapters_to_test)}] Testing {adapter_id}...", end=" ", flush=True)
            
            # Extract selectors
            selectors = extract_selectors_from_adapter(adapter)
            
            if not selectors:
                print("⚠️  No selectors found in code")
                results[adapter_id] = {
                    'url': '',
                    'selectors': {},
                    'error': 'No selectors found in adapter code'
                }
                continue
            
            # Get search URL
            search_url = get_adapter_search_url(adapter)
            if not search_url:
                print("⚠️  No search URL found")
                results[adapter_id] = {
                    'url': '',
                    'selectors': {},
                    'error': 'No search URL found'
                }
                continue
            
            # Navigate to page
            try:
                page = context.new_page()
                page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
                page.wait_for_timeout(5000)  # Wait for dynamic content
                
                # Test each selector
                selector_results = {}
                for selector in selectors:
                    count, sample_html = test_selector_on_page(page, selector)
                    selector_results[selector] = {
                        'count': count,
                        'sample_html': sample_html
                    }
                
                page.close()
                
                # Determine status
                total_elements = sum(r['count'] for r in selector_results.values())
                if total_elements > 0:
                    print(f"✅ {total_elements} elements found")
                else:
                    print(f"❌ No elements found")
                
                results[adapter_id] = {
                    'url': search_url,
                    'selectors': selector_results,
                    'error': None
                }
                
            except Exception as e:
                print(f"❌ Error: {type(e).__name__}")
                results[adapter_id] = {
                    'url': search_url,
                    'selectors': {},
                    'error': f"{type(e).__name__}: {str(e)[:100]}"
                }
        
        browser.close()
    
    return results


def generate_report(results: Dict) -> str:
    """Generate markdown report of selector validation results."""
    
    lines = [
        "# Selector Validation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Adapters Tested:** {len(results)}",
        "",
        "---",
        "",
        "## Summary",
        "",
    ]
    
    # Count working vs broken
    working = len([r for r in results.values() if not r.get('error') and 
                   any(s['count'] > 0 for s in r.get('selectors', {}).values())])
    no_elements = len([r for r in results.values() if not r.get('error') and 
                       all(s['count'] == 0 for s in r.get('selectors', {}).values())])
    errors = len([r for r in results.values() if r.get('error')])
    
    lines.extend([
        f"- **{working} adapters** have working selectors (found elements)",
        f"- **{no_elements} adapters** have selectors that found zero elements",
        f"- **{errors} adapters** encountered errors during testing",
        "",
        "---",
        "",
        "## Detailed Results",
        "",
    ])
    
    # Sort by status: working first, then no elements, then errors
    def sort_key(item):
        adapter_id, data = item
        if data.get('error'):
            return (2, adapter_id)
        total = sum(s['count'] for s in data.get('selectors', {}).values())
        if total > 0:
            return (0, adapter_id)
        return (1, adapter_id)
    
    sorted_results = sorted(results.items(), key=sort_key)
    
    for adapter_id, data in sorted_results:
        # Determine emoji
        if data.get('error'):
            emoji = "❌"
            status = "ERROR"
        elif data.get('selectors'):
            total = sum(s['count'] for s in data['selectors'].values())
            if total > 0:
                emoji = "✅"
                status = "WORKING"
            else:
                emoji = "⚠️"
                status = "NO ELEMENTS"
        else:
            emoji = "⚠️"
            status = "NO SELECTORS"
        
        lines.extend([
            f"### {emoji} {adapter_id} - {status}",
            "",
            f"**URL:** {data.get('url', 'N/A')}",
            "",
        ])
        
        if data.get('error'):
            lines.extend([
                f"**Error:** {data['error']}",
                "",
            ])
        elif data.get('selectors'):
            lines.append("**Selectors:**")
            lines.append("")
            
            for selector, info in data['selectors'].items():
                lines.append(f"**Selector:** `{selector}`")
                lines.append(f"- **Elements found:** {info['count']}")
                
                if info['count'] > 0:
                    lines.append("- **Sample HTML:**")
                    lines.append("```html")
                    lines.append(info['sample_html'])
                    lines.append("```")
                else:
                    lines.append("- **Issue:** Selector matched zero elements")
                
                lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # Comparison section
    lines.extend([
        "## Selector Strategy Comparison",
        "",
        "### Working Patterns",
        "",
    ])
    
    working_adapters = [(aid, data) for aid, data in results.items() 
                        if not data.get('error') and 
                        any(s['count'] > 0 for s in data.get('selectors', {}).values())]
    
    if working_adapters:
        lines.append("Common patterns in working selectors:")
        lines.append("")
        for adapter_id, data in working_adapters[:10]:  # Show first 10
            for selector in data['selectors'].keys():
                lines.append(f"- `{selector}` ({adapter_id})")
        lines.append("")
    else:
        lines.append("No working selectors found.")
        lines.append("")
    
    lines.extend([
        "### Non-Working Patterns",
        "",
    ])
    
    broken_adapters = [(aid, data) for aid, data in results.items() 
                       if not data.get('error') and 
                       all(s['count'] == 0 for s in data.get('selectors', {}).values())]
    
    if broken_adapters:
        lines.append("Common patterns in non-working selectors:")
        lines.append("")
        for adapter_id, data in broken_adapters[:10]:  # Show first 10
            for selector in data['selectors'].keys():
                lines.append(f"- `{selector}` ({adapter_id})")
        lines.append("")
    else:
        lines.append("All tested selectors are working.")
        lines.append("")
    
    return "\n".join(lines)


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Validate CSS selectors on live pages'
    )
    parser.add_argument(
        'adapters',
        nargs='*',
        help='Adapter IDs to test (e.g., maine_listings realty_of_maine). If none specified, tests all.'
    )
    parser.add_argument(
        '--output',
        default='reports/selector_validation_report.md',
        help='Output report path (default: reports/selector_validation_report.md)'
    )
    
    args = parser.parse_args()
    
    # Run validation
    results = validate_adapters(args.adapters)
    
    # Generate report
    print("\nGenerating report...")
    report = generate_report(results)
    
    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"✅ Report saved to: {output_path}")
    
    # Print summary
    working = len([r for r in results.values() if not r.get('error') and 
                   any(s['count'] > 0 for s in r.get('selectors', {}).values())])
    total = len(results)
    print(f"\nSummary: {working}/{total} adapters have working selectors")


if __name__ == "__main__":
    main()
