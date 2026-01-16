#!/usr/bin/env python3
"""Test script for investment/wholesale platform adapters."""

from src.ingestion.adapters.quickflip_construction import QuickFlipConstructionAdapter
from src.ingestion.adapters.motivate_maine import MotivateMaineAdapter
from src.ingestion.adapters.connected_investors import ConnectedInvestorsAdapter
from src.ingestion.adapters.discounted_property_solutions import DiscountedPropertySolutionsAdapter
from src.ingestion.adapters.housecashin import HouseCashinAdapter
from src.ingestion.adapters.offermarket import OfferMarketAdapter


def test_quickflip_construction():
    """Test QuickFlip Construction adapter."""
    print("\n=== Testing QuickFlip Construction Adapter ===")
    adapter = QuickFlipConstructionAdapter()
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
                print(f"     Location: {listing.raw_payload.get('location', 'N/A')}")
                print(f"     Price: {listing.raw_payload.get('price', 'N/A')}")
        else:
            print("  (No listings found - may need selector refinement or buyer list signup)")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_motivate_maine():
    """Test Motivate Maine adapter."""
    print("\n=== Testing Motivate Maine Adapter ===")
    adapter = MotivateMaineAdapter()
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
                print(f"     Location: {listing.raw_payload.get('location', 'N/A')}")
                print(f"     Price: {listing.raw_payload.get('price', 'N/A')}")
        else:
            print("  (No listings found - may need selector refinement or buyer list signup)")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_connected_investors():
    """Test Connected Investors adapter."""
    print("\n=== Testing Connected Investors Adapter ===")
    adapter = ConnectedInvestorsAdapter()
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
                print(f"     Location: {listing.raw_payload.get('location', 'N/A')}")
                print(f"     Price: {listing.raw_payload.get('price', 'N/A')}")
                print(f"     Metrics: {listing.raw_payload.get('metrics', 'N/A')}")
        else:
            print("  (No listings found - may need selector refinement or membership signup)")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_discounted_property_solutions():
    """Test Discounted Property Solutions adapter."""
    print("\n=== Testing Discounted Property Solutions Adapter ===")
    adapter = DiscountedPropertySolutionsAdapter()
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
                print(f"     Location: {listing.raw_payload.get('location', 'N/A')}")
                print(f"     Price: {listing.raw_payload.get('price', 'N/A')}")
        else:
            print("  (No listings found - may need selector refinement or buyer list signup)")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_housecashin():
    """Test HouseCashin adapter."""
    print("\n=== Testing HouseCashin Adapter ===")
    adapter = HouseCashinAdapter()
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
                print(f"     Location: {listing.raw_payload.get('location', 'N/A')}")
                print(f"     Price: {listing.raw_payload.get('price', 'N/A')}")
        else:
            print("  (No listings found - may need selector refinement or buyer list signup)")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_offermarket():
    """Test OfferMarket adapter."""
    print("\n=== Testing OfferMarket Adapter ===")
    adapter = OfferMarketAdapter()
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
                print(f"     Location: {listing.raw_payload.get('location', 'N/A')}")
                print(f"     Price: {listing.raw_payload.get('price', 'N/A')}")
        else:
            print("  (No listings found - may need selector refinement or membership signup)")
            
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("Testing Investment/Wholesale Platform Adapters")
    print("=" * 50)
    
    test_quickflip_construction()
    test_motivate_maine()
    test_connected_investors()
    test_discounted_property_solutions()
    test_housecashin()
    test_offermarket()
    
    print("\n" + "=" * 50)
    print("Testing complete!")
    print("\nNote: Some platforms may require buyer list signup or membership")
    print("for full access to listings. Public listings may be limited.")
