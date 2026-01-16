#!/usr/bin/env python3
"""Test script for auction house adapters."""

from src.ingestion.adapters.estatesale import EstateSaleAdapter
from src.ingestion.adapters.gotoauction import GoToAuctionAdapter
from src.ingestion.adapters.homes_auction import HomesAuctionAdapter


def test_estatesale():
    """Test EstateSale.com adapter."""
    print("\n=== Testing EstateSale.com Adapter ===")
    adapter = EstateSaleAdapter()
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
                print(f"     Auction Date: {listing.raw_payload.get('auction_date', 'N/A')}")
                print(f"     Price: {listing.raw_payload.get('price', 'N/A')}")
        else:
            print("  (No listings found - may need selector refinement)")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_gotoauction():
    """Test GoToAuction.com adapter."""
    print("\n=== Testing GoToAuction.com Adapter ===")
    adapter = GoToAuctionAdapter()
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
                print(f"     Auction Date: {listing.raw_payload.get('auction_date', 'N/A')}")
                print(f"     Price: {listing.raw_payload.get('price', 'N/A')}")
        else:
            print("  (No listings found - may need selector refinement)")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_homes_auction():
    """Test Homes.com auction adapter."""
    print("\n=== Testing Homes.com Auction Adapter ===")
    adapter = HomesAuctionAdapter()
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
                print(f"     Auction Date: {listing.raw_payload.get('auction_date', 'N/A')}")
                print(f"     Price: {listing.raw_payload.get('price', 'N/A')}")
        else:
            print("  (No listings found - may need selector refinement)")
            
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("Testing Auction House Adapters")
    print("=" * 50)
    
    test_estatesale()
    test_gotoauction()
    test_homes_auction()
    
    print("\n" + "=" * 50)
    print("Testing complete!")
