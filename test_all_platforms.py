"""
Test all property search platforms and generate a comprehensive report.

This script tests all active adapters to verify they can fetch property listings
and generates a plain-language report suitable for non-technical users.
"""

import time
from datetime import datetime
from collections import defaultdict

from src.ingestion.registry import get_adapters


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


def test_all_platforms():
    """Test all platforms and collect results."""
    print("="*70)
    print("HOUSE HUNT HERO - PLATFORM TEST")
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
        }
        
        results.append(result)
        
        status_icon = "✅" if result['status'] == 'Working' else "⚠️" if result['status'] == 'Empty' else "❌"
        print(f"{status_icon} {len(listings)} properties ({duration:.1f}s)")
    
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
    # Run tests
    results = test_all_platforms()
    
    # Generate report
    print("\nGenerating report...")
    report = generate_report(results)
    
    # Save report
    report_path = 'reports/platform_test_report.md'
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"✅ Report saved to: {report_path}")
    
    # Print summary
    working = len([r for r in results if r['status'] == 'Working'])
    total = len(results)
    print(f"\nSummary: {working}/{total} platforms working")


if __name__ == "__main__":
    main()
