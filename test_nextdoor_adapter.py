#!/usr/bin/env python3
"""
Test script for Nextdoor adapter.
Note: Nextdoor may require authentication.
"""

from src.ingestion.adapters import NextdoorAdapter


def test_adapter():
    """Test Nextdoor adapter."""
    print("Nextdoor Adapter Testing")
    print("=" * 60)
    print("Note: Nextdoor may require neighborhood verification and authentication")
    
    adapter = NextdoorAdapter()
    
    print(f"\n{'='*60}")
    print(f"Testing {adapter.source_id}")
    print(f"{'='*60}")
    
    try:
        listings = adapter.fetch()
        
        print(f"✓ Adapter executed successfully")
        print(f"  Listings retrieved: {len(listings)}")
        
        if len(listings) == 0:
            print(f"  ⚠️  No listings found")
            print(f"     Note: Nextdoor may require login or neighborhood verification")
            return {
                "adapter": "Nextdoor",
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
            "adapter": "Nextdoor",
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
            "adapter": "Nextdoor",
            "source_id": adapter.source_id,
            "status": "error",
            "count": 0,
            "errors": [f"{type(e).__name__}: {str(e)}"]
        }


if __name__ == "__main__":
    result = test_adapter()
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    status_icon = "✓" if result["status"] == "success" else "⚠️" if "no_listings" in result["status"] else "✗"
    print(f"{status_icon} {result['adapter']}: {result['count']} listings, status: {result['status']}")
