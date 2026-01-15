#!/usr/bin/env python3
"""
Test script for classifieds/newspaper adapters.
"""

from src.ingestion.adapters import (
    OodleAdapter,
    TownAdsAdapter,
    SunJournalAdapter,
    AdvertiserDemocratAdapter,
    MidcoastVillagerAdapter,
    PortlandPressHeraldAdapter,
)


def test_adapter(adapter, adapter_name):
    """Test a single adapter and return results."""
    print(f"\n{'='*60}")
    print(f"Testing {adapter_name} ({adapter.source_id})")
    print(f"{'='*60}")
    
    try:
        listings = adapter.fetch()
        
        print(f"✓ Adapter executed successfully")
        print(f"  Listings retrieved: {len(listings)}")
        
        if len(listings) == 0:
            print(f"  ⚠️  No listings found (may be expected if no listings exist)")
            return {
                "adapter": adapter_name,
                "source_id": adapter.source_id,
                "status": "no_listings",
                "count": 0,
                "errors": []
            }
        
        # Inspect first few listings
        print(f"\n  Sample listings:")
        for i, listing in enumerate(listings[:3], 1):
            print(f"    {i}. {listing.title[:60]}...")
            print(f"       URL: {listing.listing_url[:80]}...")
            print(f"       Source: {listing.source}")
            print(f"       Payload: {list(listing.raw_payload.keys())}")
        
        # Validate listings
        errors = []
        for i, listing in enumerate(listings, 1):
            if listing.source != adapter.source_id:
                errors.append(f"Listing {i}: source_id mismatch")
            if not listing.listing_url:
                errors.append(f"Listing {i}: missing listing_url")
            elif not listing.listing_url.startswith("http"):
                errors.append(f"Listing {i}: listing_url is not absolute")
            if not listing.title or listing.title == "No title":
                errors.append(f"Listing {i}: missing or empty title")
        
        if errors:
            print(f"\n  ⚠️  Validation issues found: {len(errors)}")
            for error in errors[:5]:
                print(f"    - {error}")
        else:
            print(f"\n  ✓ All listings validated successfully")
        
        return {
            "adapter": adapter_name,
            "source_id": adapter.source_id,
            "status": "success" if not errors else "validation_errors",
            "count": len(listings),
            "errors": errors
        }
        
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "adapter": adapter_name,
            "source_id": adapter.source_id,
            "status": "error",
            "count": 0,
            "errors": [f"{type(e).__name__}: {str(e)}"]
        }


def main():
    """Test all classifieds/newspaper adapters."""
    print("Classifieds/Newspaper Adapter Testing")
    print("=" * 60)
    
    adapters = [
        (OodleAdapter(), "Oodle"),
        (TownAdsAdapter(), "Town-Ads.com"),
        (SunJournalAdapter(), "Sun Journal"),
        (AdvertiserDemocratAdapter(), "Advertiser Democrat"),
        (MidcoastVillagerAdapter(), "Midcoast Villager"),
        (PortlandPressHeraldAdapter(), "Portland Press Herald"),
    ]
    
    results = []
    for adapter, name in adapters:
        result = test_adapter(adapter, name)
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r["status"] == "success")
    no_listings_count = sum(1 for r in results if r["status"] == "no_listings")
    error_count = sum(1 for r in results if r["status"] in ["error", "validation_errors"])
    total_listings = sum(r["count"] for r in results)
    
    print(f"Total adapters tested: {len(results)}")
    print(f"  ✓ Successfully retrieved listings: {success_count}")
    print(f"  ⚠️  No listings found (may be expected): {no_listings_count}")
    print(f"  ✗ Errors or validation issues: {error_count}")
    print(f"  Total listings retrieved: {total_listings}")
    
    print(f"\nDetailed Results:")
    for result in results:
        status_icon = "✓" if result["status"] == "success" else "⚠️" if result["status"] == "no_listings" else "✗"
        print(f"  {status_icon} {result['adapter']}: {result['count']} listings, status: {result['status']}")
    
    return results


if __name__ == "__main__":
    main()
