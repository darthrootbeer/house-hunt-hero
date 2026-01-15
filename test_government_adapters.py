#!/usr/bin/env python3
"""Test script for government tax foreclosure adapters."""

from src.ingestion.adapters.on_point_realty import OnPointRealtyAdapter
from src.ingestion.adapters.york_county_probate import YorkCountyProbateAdapter
from src.ingestion.adapters.municipal_tax_assessor import MunicipalTaxAssessorAdapter


def test_on_point_realty():
    """Test On Point Realty adapter (MRS tax-acquired properties)."""
    print("\n=== Testing On Point Realty Adapter ===")
    adapter = OnPointRealtyAdapter()
    print(f"Source ID: {adapter.source_id}")
    print(f"Search URL: {adapter.SEARCH_URL}")
    
    try:
        listings = adapter.fetch()
        print(f"✓ Found {len(listings)} listings")
        
        if listings:
            print("\nSample listings:")
            for i, listing in enumerate(listings[:3], 1):
                print(f"  {i}. {listing.title}")
                print(f"     URL: {listing.listing_url}")
                print(f"     Price: {listing.raw_payload.get('price', 'N/A')}")
                print(f"     Location: {listing.raw_payload.get('location', 'N/A')}")
        else:
            print("  (No listings found - may need selector refinement)")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_york_county_probate():
    """Test York County Probate adapter (estate notices)."""
    print("\n=== Testing York County Probate Adapter ===")
    adapter = YorkCountyProbateAdapter()
    print(f"Source ID: {adapter.source_id}")
    print(f"Search URL: {adapter.SEARCH_URL}")
    
    try:
        listings = adapter.fetch()
        print(f"✓ Found {len(listings)} estate notices")
        
        if listings:
            print("\nSample notices:")
            for i, listing in enumerate(listings[:3], 1):
                print(f"  {i}. {listing.title}")
                print(f"     URL: {listing.listing_url}")
        else:
            print("  (No notices found - may need selector refinement)")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_municipal_tax_assessor():
    """Test Municipal Tax Assessor adapter (generic, needs config)."""
    print("\n=== Testing Municipal Tax Assessor Adapter ===")
    
    # Test without URL (should return empty list)
    adapter = MunicipalTaxAssessorAdapter()
    print(f"Source ID: {adapter.source_id}")
    print(f"Search URL: {adapter.SEARCH_URL or '(not configured)'}")
    
    try:
        listings = adapter.fetch()
        print(f"✓ Without URL configured: {len(listings)} listings (expected 0)")
        
        # Example: Test with a sample URL (would need real municipal URL)
        # adapter_with_url = MunicipalTaxAssessorAdapter(
        #     search_url="https://example.com/tax-acquired",
        #     municipality_name="Example Town"
        # )
        # listings = adapter_with_url.fetch()
        # print(f"With URL: {len(listings)} listings")
        
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("Testing Government Tax Foreclosure Adapters")
    print("=" * 50)
    
    test_on_point_realty()
    test_york_county_probate()
    test_municipal_tax_assessor()
    
    print("\n" + "=" * 50)
    print("Testing complete!")
