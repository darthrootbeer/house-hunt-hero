"""Test all ingestion adapters and generate a summary report."""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Check for playwright
try:
    import playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Warning: playwright not installed. Adapters requiring playwright will fail.")
    print("   Install with: pip install playwright && playwright install chromium\n")

# Import base classes first (should not require playwright)
try:
    from ingestion.base import RawListing
except Exception as e:
    print(f"❌ Failed to import base classes: {e}")
    sys.exit(1)

# Try to import registry, but handle playwright dependency
def get_adapters_safe():
    """Get adapters, handling missing dependencies."""
    try:
        from ingestion.registry import get_adapters
        return get_adapters()
    except ImportError as e:
        if "playwright" in str(e).lower():
            # Try to import adapters individually, skipping those that need playwright
            adapters = []
            
            # Import adapters that don't need playwright first
            try:
                # These might work without playwright
                from ingestion.adapters.ownerama import OwneramaAdapter
                adapters.append(OwneramaAdapter())
            except:
                pass
            
            # For now, return empty list if we can't import registry
            return []
        raise


class TestResult:
    """Test result for a single adapter."""
    def __init__(self, adapter_name: str, adapter):
        self.adapter_name = adapter_name
        self.adapter = adapter
        self.success = False
        self.error = None
        self.listings_count = 0
        self.listings_sample = []
        self.execution_time = None
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting."""
        return {
            "adapter": self.adapter_name,
            "source_id": self.adapter.source_id,
            "success": self.success,
            "error": str(self.error) if self.error else None,
            "listings_count": self.listings_count,
            "execution_time": self.execution_time,
            "sample_listings": [
                {
                    "title": l.title[:50] + "..." if len(l.title) > 50 else l.title,
                    "url": l.listing_url[:80] + "..." if len(l.listing_url) > 80 else l.listing_url,
                }
                for l in self.listings_sample[:3]
            ]
        }


def test_adapter(adapter_name: str, adapter) -> TestResult:
    """Test a single adapter."""
    result = TestResult(adapter_name, adapter)
    
    # Skip adapters that require playwright if not available
    if not PLAYWRIGHT_AVAILABLE:
        # Check if adapter uses playwright by inspecting its fetch method
        import inspect
        source = inspect.getsource(adapter.fetch)
        if "playwright" in source.lower() or "sync_playwright" in source:
            result.error = "playwright not installed (required for this adapter)"
            result.success = False
            result.execution_time = 0.0
            return result
    
    try:
        import time
        start_time = time.time()
        
        listings = adapter.fetch()
        
        result.execution_time = time.time() - start_time
        result.listings_count = len(listings)
        result.listings_sample = listings[:3]
        result.success = True
        
        # Validate listing structure
        if listings:
            for listing in listings[:3]:  # Check first 3
                if not isinstance(listing, RawListing):
                    result.error = f"Invalid listing type: {type(listing)}"
                    result.success = False
                    break
                if not listing.source:
                    result.error = "Missing source"
                    result.success = False
                    break
                if not listing.listing_url:
                    result.error = "Missing listing_url"
                    result.success = False
                    break
                if not listing.title:
                    result.error = "Missing title"
                    result.success = False
                    break
                    
    except Exception as e:
        result.error = e
        result.success = False
        if result.execution_time is None:
            result.execution_time = 0.0
        
    return result


def generate_report(results: List[TestResult]) -> str:
    """Generate a markdown report from test results."""
    report = []
    report.append("# Adapter Test Report")
    report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n**Total Adapters Tested:** {len(results)}\n")
    
    # Summary statistics
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    with_listings = [r for r in successful if r.listings_count > 0]
    without_listings = [r for r in successful if r.listings_count == 0]
    
    report.append("## Summary Statistics\n")
    report.append(f"- ✅ **Successfully Executed:** {len(successful)}/{len(results)}")
    report.append(f"- ❌ **Failed:** {len(failed)}/{len(results)}")
    report.append(f"- 📋 **Returned Listings:** {len(with_listings)}")
    report.append(f"- 🔍 **No Listings Found:** {len(without_listings)} (may be normal)\n")
    
    # Working adapters (with listings)
    if with_listings:
        report.append("## ✅ Working Adapters (Listings Found)\n")
        report.append("| Adapter | Source ID | Listings | Time (s) | Sample Title |")
        report.append("|---------|-----------|----------|----------|--------------|")
        for r in sorted(with_listings, key=lambda x: x.listings_count, reverse=True):
            sample = r.listings_sample[0].title[:40] + "..." if r.listings_sample and len(r.listings_sample[0].title) > 40 else (r.listings_sample[0].title if r.listings_sample else "N/A")
            report.append(f"| {r.adapter_name} | `{r.adapter.source_id}` | {r.listings_count} | {r.execution_time:.2f} | {sample} |")
        report.append("")
    
    # Working adapters (no listings - may be normal)
    if without_listings:
        report.append("## ⚠️  Working Adapters (No Listings - May Be Normal)\n")
        report.append("| Adapter | Source ID | Time (s) | Notes |")
        report.append("|---------|-----------|----------|-------|")
        for r in without_listings:
            report.append(f"| {r.adapter_name} | `{r.adapter.source_id}` | {r.execution_time:.2f} | No listings found at this time |")
        report.append("")
    
    # Failed adapters
    if failed:
        report.append("## ❌ Failed Adapters\n")
        report.append("| Adapter | Source ID | Error |")
        report.append("|---------|-----------|-------|")
        for r in failed:
            error_msg = str(r.error)[:100] + "..." if len(str(r.error)) > 100 else str(r.error)
            report.append(f"| {r.adapter_name} | `{r.adapter.source_id}` | `{error_msg}` |")
        report.append("")
    
    # Detailed results by category
    report.append("## Detailed Results by Category\n")
    
    # Group by category
    categories = {
        "Craigslist": [],
        "FSBO Platforms": [],
        "Classifieds & Newspapers": [],
        "Facebook": [],
        "Nextdoor": [],
        "Bank REO": [],
        "Government": [],
    }
    
    fsbo_adapters = ["OwneramaAdapter", "BrokerlessAdapter", "FlatFeeGroupAdapter", 
                     "TheRockFoundationAdapter", "FSBOHomeListingsAdapter", 
                     "DIYFlatFeeAdapter", "ISoldMyHouseAdapter", "HoangRealtyFSBOAdapter"]
    
    classifieds_adapters = ["OodleAdapter", "TownAdsAdapter", "SunJournalAdapter",
                           "AdvertiserDemocratAdapter", "MidcoastVillagerAdapter",
                           "PortlandPressHeraldAdapter"]
    
    facebook_adapters = ["FacebookMarketplaceAdapter", "FacebookGroupsAdapter"]
    
    bank_adapters = ["BankOwnedPropertiesAdapter", "DistressedProAdapter", "MaineCommunityBankAdapter"]
    
    government_adapters = ["OnPointRealtyAdapter", "YorkCountyProbateAdapter", "MunicipalTaxAssessorAdapter"]
    
    for r in results:
        if "Craigslist" in r.adapter_name:
            categories["Craigslist"].append(r)
        elif any(fsbo in r.adapter_name for fsbo in fsbo_adapters):
            categories["FSBO Platforms"].append(r)
        elif any(cls in r.adapter_name for cls in classifieds_adapters):
            categories["Classifieds & Newspapers"].append(r)
        elif any(fb in r.adapter_name for fb in facebook_adapters):
            categories["Facebook"].append(r)
        elif "Nextdoor" in r.adapter_name:
            categories["Nextdoor"].append(r)
        elif any(bank in r.adapter_name for bank in bank_adapters):
            categories["Bank REO"].append(r)
        elif any(gov in r.adapter_name for gov in government_adapters):
            categories["Government"].append(r)
    
    for category, category_results in categories.items():
        if not category_results:
            continue
            
        report.append(f"### {category}\n")
        for r in category_results:
            status = "✅" if r.success else "❌"
            listings_info = f"{r.listings_count} listings" if r.success else "FAILED"
            report.append(f"- {status} **{r.adapter_name}** (`{r.adapter.source_id}`): {listings_info}")
            if r.error:
                report.append(f"  - Error: `{r.error}`")
            if r.listings_sample:
                report.append(f"  - Sample: {r.listings_sample[0].title[:60]}...")
        report.append("")
    
    return "\n".join(report)


def main():
    """Test all adapters and generate report."""
    print("="*80)
    print("Testing All Ingestion Adapters")
    print("="*80)
    print()
    
    # Try to get adapters
    try:
        from ingestion.registry import get_adapters
        adapters = get_adapters()
    except ImportError as e:
        if "playwright" in str(e).lower():
            print("❌ Cannot test adapters: playwright is not installed")
            print("   Please install with: pip install playwright && playwright install chromium")
            sys.exit(1)
        else:
            print(f"❌ Failed to import adapters: {e}")
            sys.exit(1)
    
    print(f"Found {len(adapters)} adapters to test\n")
    
    results = []
    
    for i, adapter in enumerate(adapters, 1):
        adapter_name = adapter.__class__.__name__
        print(f"[{i}/{len(adapters)}] Testing {adapter_name}...", end=" ", flush=True)
        
        result = test_adapter(adapter_name, adapter)
        results.append(result)
        
        if result.success:
            status = f"✅ {result.listings_count} listings"
        else:
            status = f"❌ {result.error}"
        print(status)
    
    print()
    print("="*80)
    print("Generating Report...")
    print("="*80)
    
    # Generate and save report
    report = generate_report(results)
    
    report_file = Path(__file__).parent / "ADAPTER_TEST_REPORT.md"
    with open(report_file, "w") as f:
        f.write(report)
    
    print(f"\n✅ Report saved to: {report_file}")
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print()
    
    # Print summary
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    with_listings = [r for r in successful if r.listings_count > 0]
    
    print(f"✅ Successfully Executed: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    print(f"📋 Returned Listings: {len(with_listings)}")
    print()
    
    if failed:
        print("Failed Adapters:")
        for r in failed:
            print(f"  - {r.adapter_name}: {r.error}")
    
    # Return non-zero exit code if any failed
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
