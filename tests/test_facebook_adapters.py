#!/usr/bin/env python3
"""
Test script for Facebook adapters.
Note: Facebook may block scrapers - results may be empty.
"""

from src.ingestion.adapters import (
    FacebookMarketplaceAdapter,
    FacebookGroupsAdapter,
)


def test_adapter(adapter, adapter_name):
    """Test a single adapter."""
    print(f"\n{'='*60}")
    print(f"Testing {adapter_name} ({adapter.source_id})")
    print(f"{'='*60}")
    
    try:
        listings = adapter.fetch()
        
        print(f"✓ Adapter executed successfully")
        print(f"  Listings retrieved: {len(listings)}")
        
        if len(listings) == 0:
            print(f"  ⚠️  No listings found")
            print(f"     Note: Facebook may require login or block scrapers")
            return {
                "adapter": adapter_name,
                "source_id": adapter.source_id,
                "status": "no_listings_or_blocked",
                "count": 0,
                "errors": []
            }
        
        print(f"\n  Sample listings:")
        for i, listing in enumerate(listings[:3], 1):
            print(f"    {i}. {listing.title[:60]}...")
            print(f"       URL: {listing.listing_url[:80]}...")
        
        errors = []
        for i, listing in enumerate(listings, 1):
            if not listing.listing_url or not listing.listing_url.startswith("http"):
                errors.append(f"Listing {i}: invalid URL")
            if not listing.title or listing.title == "No title":
                errors.append(f"Listing {i}: missing title")
        
        if errors:
            print(f"\n  ⚠️  Validation issues: {len(errors)}")
        else:
            print(f"\n  ✓ All listings validated")
        
        return {
            "adapter": adapter_name,
            "source_id": adapter.source_id,
            "status": "success" if not errors else "validation_errors",
            "count": len(listings),
            "errors": errors
        }
        
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {str(e)}")
        return {
            "adapter": adapter_name,
            "source_id": adapter.source_id,
            "status": "error",
            "count": 0,
            "errors": [f"{type(e).__name__}: {str(e)}"]
        }


def main():
    """Test Facebook adapters."""
    print("Facebook Adapter Testing")
    print("=" * 60)
    print("Note: Facebook may block scrapers without authentication")
    
    adapters = [
        (FacebookMarketplaceAdapter(), "Facebook Marketplace"),
        (FacebookGroupsAdapter(), "Facebook Groups"),
    ]
    
    results = []
    for adapter, name in adapters:
        result = test_adapter(adapter, name)
        results.append(result)
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r["status"] == "success")
    no_listings_count = sum(1 for r in results if r["status"] in ["no_listings_or_blocked", "no_listings"])
    error_count = sum(1 for r in results if r["status"] in ["error", "validation_errors"])
    
    print(f"Total adapters tested: {len(results)}")
    print(f"  ✓ Successfully retrieved listings: {success_count}")
    print(f"  ⚠️  No listings (may be blocked/require auth): {no_listings_count}")
    print(f"  ✗ Errors: {error_count}")
    print(f"  Total listings: {sum(r['count'] for r in results)}")
    
    print(f"\nDetailed Results:")
    for result in results:
        status_icon = "✓" if result["status"] == "success" else "⚠️" if "no_listings" in result["status"] else "✗"
        print(f"  {status_icon} {result['adapter']}: {result['count']} listings, status: {result['status']}")
    
    return results


if __name__ == "__main__":
    main()
