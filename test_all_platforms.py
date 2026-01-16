"""
Test all property search platforms and generate a comprehensive report.

This script tests all active adapters to verify they can fetch property listings
and generates a plain-language report suitable for non-technical users.
"""

import argparse
import time
import os
import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path

from src.ingestion.registry import get_adapters
from playwright.sync_api import sync_playwright


def capture_diagnostics(adapter, adapter_id, diagnose_mode=False):
    """
    Capture diagnostic information for a platform.
    
    Returns dict with:
    - screenshot_path: Path to screenshot file
    - html_path: Path to HTML snapshot file
    - network_requests: List of network requests
    - console_messages: List of console messages
    - timing_metrics: Dict of timing information
    """
    diagnostics_dir = Path(f"reports/diagnostics/{adapter_id}")
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    
    diagnostics = {
        'screenshot_path': None,
        'html_path': None,
        'network_requests': [],
        'console_messages': [],
        'timing_metrics': {},
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            # Capture network requests
            network_requests = []
            def handle_request(request):
                if request.resource_type in ['xhr', 'fetch', 'document']:
                    network_requests.append({
                        'url': request.url,
                        'method': request.method,
                        'type': request.resource_type,
                    })
            page.on('request', handle_request)
            
            # Capture console messages
            console_messages = []
            def handle_console(msg):
                if msg.type in ['error', 'warning']:
                    console_messages.append({
                        'type': msg.type,
                        'text': msg.text,
                    })
            page.on('console', handle_console)
            
            # Get search URL from adapter
            search_url = getattr(adapter, 'search_url', None)
            if not search_url:
                # Try to get from config
                config_path = Path(f"configs/sources/{adapter_id}.yaml")
                if config_path.exists():
                    import yaml
                    with open(config_path) as f:
                        config = yaml.safe_load(f)
                        search_url = config.get('search_url') or config.get('base_url')
            
            if not search_url:
                return diagnostics
            
            # Navigate and capture timing
            start_time = time.time()
            page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
            page_load_time = time.time() - start_time
            
            # Wait for potential dynamic content
            wait_start = time.time()
            try:
                page.wait_for_load_state('networkidle', timeout=10000)
            except:
                pass
            network_idle_time = time.time() - wait_start
            
            # Capture screenshot
            screenshot_path = diagnostics_dir / 'screenshot.png'
            page.screenshot(path=str(screenshot_path), full_page=True)
            diagnostics['screenshot_path'] = str(screenshot_path)
            
            # Capture HTML snapshot
            html_path = diagnostics_dir / 'page.html'
            html_content = page.content()
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            diagnostics['html_path'] = str(html_path)
            
            # Store captured data
            diagnostics['network_requests'] = network_requests
            diagnostics['console_messages'] = console_messages
            diagnostics['timing_metrics'] = {
                'page_load_seconds': round(page_load_time, 2),
                'network_idle_seconds': round(network_idle_time, 2),
                'total_seconds': round(page_load_time + network_idle_time, 2),
            }
            
            browser.close()
            
    except Exception as e:
        print(f"  [Diagnostic capture failed: {type(e).__name__}]")
    
    return diagnostics


def save_diagnostic_report(adapter_id, diagnostics):
    """Save a diagnostic report summary for an adapter."""
    diagnostics_dir = Path(f"reports/diagnostics/{adapter_id}")
    report_path = diagnostics_dir / 'diagnostic_report.md'
    
    lines = [
        f"# Diagnostic Report: {adapter_id}",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Timing Metrics",
        "",
    ]
    
    if diagnostics['timing_metrics']:
        for key, value in diagnostics['timing_metrics'].items():
            lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
    else:
        lines.append("- No timing data captured")
    
    lines.extend([
        "",
        "## Screenshots & HTML",
        "",
    ])
    
    if diagnostics['screenshot_path']:
        lines.append(f"- Screenshot saved to: `{diagnostics['screenshot_path']}`")
    if diagnostics['html_path']:
        lines.append(f"- HTML snapshot saved to: `{diagnostics['html_path']}`")
    
    lines.extend([
        "",
        "## Network Requests",
        "",
    ])
    
    if diagnostics['network_requests']:
        lines.append(f"Total requests captured: {len(diagnostics['network_requests'])}")
        lines.append("")
        for req in diagnostics['network_requests'][:20]:  # Limit to first 20
            lines.append(f"- `{req['method']}` {req['type']}: {req['url'][:100]}")
    else:
        lines.append("- No network requests captured")
    
    lines.extend([
        "",
        "## Console Messages",
        "",
    ])
    
    if diagnostics['console_messages']:
        lines.append(f"Total messages captured: {len(diagnostics['console_messages'])}")
        lines.append("")
        for msg in diagnostics['console_messages'][:20]:  # Limit to first 20
            lines.append(f"- **{msg['type'].upper()}:** {msg['text'][:200]}")
    else:
        lines.append("- No console errors or warnings")
    
    with open(report_path, 'w') as f:
        f.write("\n".join(lines))


def categorize_result(adapter_id, listings_count, error):
    """Categorize test result into: Working, Empty, Problem, or NeedsAttention."""
    if error:
        return "Problem"
    elif listings_count > 0:
        return "Working"
    elif listings_count == 0:
        # Some platforms legitimately may have no listings
        return "Empty"
    else:
        return "NeedsAttention"


def get_category_name(adapter_id):
    """Categorize adapter by its purpose/type."""
    categories = {
        'FSBO Platforms': ['ownerama', 'brokerless', 'flat_fee_group', 'the_rock_foundation',
                          'fsbo_home_listings', 'diy_flat_fee', 'isold_my_house', 'hoang_realty_fsbo',
                          'fsbo_com'],
        'Classifieds & Local News': ['craigslist_owner', 'craigslist_maine', 'craigslist_nh',
                                     'oodle', 'town_ads', 'sun_journal', 'advertiser_democrat',
                                     'midcoast_villager', 'portland_press_herald'],
        'Social & Community': ['facebook_marketplace', 'facebook_groups', 'nextdoor'],
        'Bank REO & Foreclosures': ['bank_owned_properties', 'distressed_pro', 'maine_community_bank',
                                   'fontaine_family'],
        'Government & Tax Sales': ['on_point_realty', 'york_county_probate', 'municipal_tax_assessor'],
        'Auctions': ['estatesale', 'gotoauction', 'homes_auction'],
        'Investment & Wholesale': ['quickflip_construction', 'motivate_maine', 'connected_investors',
                                  'discounted_property_solutions', 'housecashin', 'offermarket'],
        'MLS Services': ['maine_listings', 'maine_state_mls'],
        'Maine Brokerages': ['listings_direct', 'meservier_associates', 'locations_real_estate_group',
                           'swan_agency', 'the_maine_agents', 'sargent_real_estate', 'allied_realty',
                           'landing_real_estate', 'la_count_real_estate', 'realty_of_maine',
                           'maine_real_estate_co'],
        'Credit Unions': ['maine_highlands_fcu', 'maine_state_credit_union', 'maine_credit_unions_directory'],
        'Commercial Real Estate': ['boulos_company', 'necpe', 'malone_commercial', 'loopnet', 'nai_dunham'],
        'National Aggregators': ['zillow', 'realtor_com', 'redfin', 'trulia', 'homes_com'],
    }
    
    for category, adapters in categories.items():
        if adapter_id in adapters:
            return category
    return 'Other'


def test_all_platforms(diagnose_mode=False):
    """Test all platforms and collect results."""
    print("="*70)
    print("HOUSE HUNT HERO - PLATFORM TEST")
    if diagnose_mode:
        print("(Diagnostic Mode Enabled)")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    adapters = get_adapters()
    print(f"Testing {len(adapters)} property search platforms...\n")
    
    results = []
    
    for i, adapter in enumerate(adapters, 1):
        adapter_id = adapter.source_id
        print(f"[{i}/{len(adapters)}] Testing {adapter_id}...", end=" ", flush=True)
        
        start_time = time.time()
        error = None
        listings = []
        
        try:
            listings = adapter.fetch()
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)[:100]}"
        
        duration = time.time() - start_time
        
        result = {
            'adapter_id': adapter_id,
            'count': len(listings),
            'duration': duration,
            'error': error,
            'category': get_category_name(adapter_id),
            'status': categorize_result(adapter_id, len(listings), error),
            'sample_titles': [l.title[:80] for l in listings[:3]] if listings else [],
            'diagnostics': None,
        }
        
        results.append(result)
        
        status_icon = "✅" if result['status'] == 'Working' else "⚠️" if result['status'] == 'Empty' else "❌"
        print(f"{status_icon} {len(listings)} properties ({duration:.1f}s)", end="")
        
        # Capture diagnostics for zero-property platforms or if diagnose mode enabled
        should_diagnose = diagnose_mode or (len(listings) == 0 and not error)
        if should_diagnose:
            print(" [Capturing diagnostics...]", end="", flush=True)
            diagnostics = capture_diagnostics(adapter, adapter_id, diagnose_mode)
            result['diagnostics'] = diagnostics
            if diagnostics['screenshot_path'] or diagnostics['html_path']:
                save_diagnostic_report(adapter_id, diagnostics)
                print(" Done")
            else:
                print(" Skipped")
        else:
            print()
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return results


def generate_report(results):
    """Generate a plain-language markdown report."""
    
    # Calculate summary stats
    total_platforms = len(results)
    working = len([r for r in results if r['status'] == 'Working'])
    empty = len([r for r in results if r['status'] == 'Empty'])
    problems = len([r for r in results if r['status'] == 'Problem'])
    total_listings = sum(r['count'] for r in results)
    
    # Group by category and status
    by_category = defaultdict(list)
    for r in results:
        by_category[r['category']].append(r)
    
    # Generate report
    lines = [
        "# House Hunt Hero - Platform Test Report",
        "",
        f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        f"**Platforms Tested:** {total_platforms}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"We tested {total_platforms} property search platforms to verify they can find real estate listings.",
        "",
        "### Results:",
        f"- **{working} platforms** are working and found properties ({working/total_platforms*100:.0f}%)",
        f"- **{empty} platforms** ran successfully but found no properties",
        f"- **{problems} platforms** encountered issues",
        f"- **Total properties found:** {total_listings:,}",
        "",
        "---",
        "",
        "## Results by Category",
        "",
    ]
    
    # Sort categories by number of working platforms
    sorted_categories = sorted(by_category.items(), 
                              key=lambda x: len([r for r in x[1] if r['status'] == 'Working']),
                              reverse=True)
    
    for category, cat_results in sorted_categories:
        cat_working = len([r for r in cat_results if r['status'] == 'Working'])
        cat_total = len(cat_results)
        cat_listings = sum(r['count'] for r in cat_results)
        
        lines.extend([
            f"### {category}",
            "",
            f"**Status:** {cat_working}/{cat_total} platforms working | {cat_listings:,} properties found",
            "",
        ])
        
        # Sort by status (Working first) then by count
        sorted_results = sorted(cat_results, 
                               key=lambda x: (x['status'] != 'Working', -x['count']))
        
        for r in sorted_results:
            status_emoji = {
                'Working': '✅',
                'Empty': '⚠️',
                'Problem': '❌',
                'NeedsAttention': '⚠️',
            }[r['status']]
            
            lines.append(f"**{status_emoji} {r['adapter_id']}**")
            
            if r['status'] == 'Working':
                lines.append(f"- **Found:** {r['count']} properties")
                if r['sample_titles']:
                    lines.append("- **Sample listings:**")
                    for title in r['sample_titles']:
                        lines.append(f"  - {title}")
            elif r['status'] == 'Empty':
                lines.append("- Platform is working but no properties found at this time")
                lines.append("- This may be normal if platform has limited inventory")
            elif r['status'] == 'Problem':
                lines.append("- **Issue:** Platform encountered an error during testing")
                if r['error']:
                    lines.append(f"- **Technical detail:** `{r['error']}`")
                lines.append("- **Recommendation:** Review adapter implementation")
            
            lines.append("")
        
        lines.append("")
    
    # Issues and recommendations
    lines.extend([
        "---",
        "",
        "## Issues & Recommendations",
        "",
    ])
    
    problem_results = [r for r in results if r['status'] == 'Problem']
    if problem_results:
        lines.extend([
            f"### Platforms with Issues ({len(problem_results)})",
            "",
            "The following platforms encountered errors and need attention:",
            "",
        ])
        for r in problem_results:
            lines.append(f"- **{r['adapter_id']}**: {r['error'][:150] if r['error'] else 'Unknown error'}")
        lines.append("")
    
    empty_results = [r for r in results if r['status'] == 'Empty']
    if empty_results:
        lines.extend([
            f"### Platforms with No Properties ({len(empty_results)})",
            "",
            "These platforms ran successfully but didn't find any properties:",
            "",
        ])
        for r in empty_results:
            lines.append(f"- **{r['adapter_id']}** - May need selector refinement or may have limited inventory")
            if r.get('diagnostics') and r['diagnostics'].get('screenshot_path'):
                lines.append(f"  - Diagnostics available: `reports/diagnostics/{r['adapter_id']}/`")
        lines.append("")
    
    lines.extend([
        "### General Recommendations",
        "",
        "1. **Focus on Working Platforms:** Prioritize the platforms that are successfully finding properties",
        "2. **Refine Selectors:** Platforms returning zero properties may need updated selectors for their page structure",
        "3. **Fix Errors:** Address platforms with errors to expand coverage",
        "4. **Monitor Changes:** Website structures change over time - periodic testing is recommended",
        "",
    ])
    
    # Footer
    lines.extend([
        "---",
        "",
        "## Technical Notes",
        "",
        "- Test duration varies by platform complexity and network speed",
        "- Empty results may indicate: (1) legitimate lack of inventory, (2) selector mismatch, or (3) anti-bot protection",
        "- Some platforms use JavaScript-heavy interfaces that require additional load time",
        "- Rate limiting is applied to avoid overwhelming source websites",
        "",
    ])
    
    return "\n".join(lines)


def main():
    """Main test execution."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Test all property search platforms and generate a comprehensive report.'
    )
    parser.add_argument(
        '--diagnose',
        action='store_true',
        help='Enable detailed diagnostics for all platforms (captures screenshots, HTML, network requests)'
    )
    args = parser.parse_args()
    
    # Run tests
    results = test_all_platforms(diagnose_mode=args.diagnose)
    
    # Generate report
    print("\nGenerating report...")
    report = generate_report(results)
    
    # Save report
    report_path = 'reports/platform_test_report.md'
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"✅ Report saved to: {report_path}")
    
    # Count diagnostics captured
    diagnostics_captured = len([r for r in results if r.get('diagnostics') and r['diagnostics'].get('screenshot_path')])
    if diagnostics_captured > 0:
        print(f"📊 Diagnostics captured for {diagnostics_captured} platforms in reports/diagnostics/")
    
    # Print summary
    working = len([r for r in results if r['status'] == 'Working'])
    total = len(results)
    print(f"\nSummary: {working}/{total} platforms working")


if __name__ == "__main__":
    main()
