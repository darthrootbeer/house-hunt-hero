"""Test script for bank REO adapters."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestion.adapters.bank_owned_properties import BankOwnedPropertiesAdapter
from ingestion.adapters.distressed_pro import DistressedProAdapter
from ingestion.adapters.maine_community_bank import MaineCommunityBankAdapter


def test_adapter(adapter_name: str, adapter):
    """Test a single adapter."""
    print(f"\n{'='*60}")
    print(f"Testing {adapter_name}")
    print(f"{'='*60}")
    
    try:
        listings = adapter.fetch()
        print(f"✅ Retrieved {len(listings)} listings")
        
        if listings:
            print(f"\nFirst listing:")
            first = listings[0]
            print(f"  Source: {first.source}")
            print(f"  Title: {first.title}")
            print(f"  URL: {first.listing_url}")
            print(f"  Payload: {first.raw_payload}")
        else:
            print("  ⚠️  No listings found (this may be normal if no properties are currently available)")
            
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing Bank REO Adapters")
    print("="*60)
    
    results = {}
    
    # Test aggregators
    results["BankOwnedProperties"] = test_adapter(
        "BankOwnedPropertiesAdapter",
        BankOwnedPropertiesAdapter()
    )
    
    results["DistressedPro"] = test_adapter(
        "DistressedProAdapter",
        DistressedProAdapter()
    )
    
    # Test Maine Community Bank
    results["MaineCommunityBank"] = test_adapter(
        "MaineCommunityBankAdapter",
        MaineCommunityBankAdapter()
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)
