#!/usr/bin/env python3
"""Test script for Maine MLS, Brokerage, and Credit Union adapters."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

# Import all new adapters
from src.ingestion.adapters.maine_listings import MaineListingsAdapter
from src.ingestion.adapters.maine_state_mls import MaineStateMLSAdapter
from src.ingestion.adapters.listings_direct import ListingsDirectAdapter
from src.ingestion.adapters.meservier_associates import MeservierAssociatesAdapter
from src.ingestion.adapters.locations_real_estate_group import LocationsRealEstateGroupAdapter
from src.ingestion.adapters.swan_agency import SwanAgencyAdapter
from src.ingestion.adapters.the_maine_agents import TheMaineAgentsAdapter
from src.ingestion.adapters.sargent_real_estate import SargentRealEstateAdapter
from src.ingestion.adapters.allied_realty import AlliedRealtyAdapter
from src.ingestion.adapters.landing_real_estate import LandingRealEstateAdapter
from src.ingestion.adapters.la_count_real_estate import LaCountRealEstateAdapter
from src.ingestion.adapters.realty_of_maine import RealtyOfMaineAdapter
from src.ingestion.adapters.maine_real_estate_co import MaineRealEstateCoAdapter
from src.ingestion.adapters.fontaine_family import FontaineFamilyAdapter
from src.ingestion.adapters.maine_highlands_fcu import MaineHighlandsFCUAdapter


def test_adapter(adapter, name: str, timeout_seconds: int = 60):
    """Test a single adapter and return results."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Source ID: {adapter.source_id}")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    try:
        listings = adapter.fetch()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"✓ Fetch completed in {elapsed:.1f}s")
        print(f"  Listings found: {len(listings)}")
        
        if listings:
            # Show sample listing
            sample = listings[0]
            print(f"\n  Sample listing:")
            print(f"    URL: {sample.listing_url[:80]}..." if len(sample.listing_url) > 80 else f"    URL: {sample.listing_url}")
            print(f"    Title: {sample.title[:60]}..." if len(sample.title) > 60 else f"    Title: {sample.title}")
            print(f"    Raw payload keys: {list(sample.raw_payload.keys())}")
            
            # Validate listings
            valid = 0
            issues = []
            for i, listing in enumerate(listings):
                if not listing.listing_url:
                    issues.append(f"Listing {i}: Missing URL")
                elif not listing.listing_url.startswith("http"):
                    issues.append(f"Listing {i}: Invalid URL - {listing.listing_url[:50]}")
                elif not listing.source:
                    issues.append(f"Listing {i}: Missing source")
                else:
                    valid += 1
            
            print(f"  Valid listings: {valid}/{len(listings)}")
            if issues and len(issues) <= 3:
                for issue in issues:
                    print(f"    ⚠ {issue}")
            elif issues:
                print(f"    ⚠ {len(issues)} issues found")
        
        return {
            "name": name,
            "source_id": adapter.source_id,
            "success": True,
            "listings_found": len(listings),
            "elapsed_seconds": elapsed,
            "error": None
        }
        
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"✗ Error after {elapsed:.1f}s: {type(e).__name__}: {str(e)[:100]}")
        return {
            "name": name,
            "source_id": adapter.source_id,
            "success": False,
            "listings_found": 0,
            "elapsed_seconds": elapsed,
            "error": f"{type(e).__name__}: {str(e)[:200]}"
        }


def main():
    """Run tests on all new adapters."""
    print("=" * 70)
    print("MAINE MLS, BROKERAGE, AND CREDIT UNION ADAPTER TESTS")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Define adapters to test
    adapters = [
        # MLS Platforms
        (MaineListingsAdapter(), "Maine Listings (Official MLS)"),
        (MaineStateMLSAdapter(), "Maine State MLS"),
        
        # Brokerages
        (ListingsDirectAdapter(), "Listings Direct"),
        (MeservierAssociatesAdapter(), "Meservier & Associates"),
        (LocationsRealEstateGroupAdapter(), "Locations Real Estate Group"),
        (SwanAgencyAdapter(), "Swan Agency"),
        (TheMaineAgentsAdapter(), "The Maine Agents"),
        (SargentRealEstateAdapter(), "Sargent Real Estate"),
        (AlliedRealtyAdapter(), "Allied Realty"),
        (LandingRealEstateAdapter(), "Landing Real Estate"),
        (LaCountRealEstateAdapter(), "La Count Real Estate"),
        (RealtyOfMaineAdapter(), "Realty of Maine"),
        (MaineRealEstateCoAdapter(), "Maine Real Estate Co."),
        (FontaineFamilyAdapter(), "Fontaine Family"),
        
        # Credit Unions
        (MaineHighlandsFCUAdapter(), "Maine Highlands FCU"),
    ]
    
    results = []
    
    for adapter, name in adapters:
        result = test_adapter(adapter, name)
        results.append(result)
    
    # Summary
    print("\n")
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    with_listings = [r for r in results if r["listings_found"] > 0]
    
    print(f"\nTotal adapters tested: {len(results)}")
    print(f"Successful fetches: {len(successful)}")
    print(f"Failed fetches: {len(failed)}")
    print(f"Adapters with listings: {len(with_listings)}")
    
    total_listings = sum(r["listings_found"] for r in results)
    print(f"Total listings found: {total_listings}")
    
    if with_listings:
        print("\n--- Adapters with listings ---")
        for r in with_listings:
            print(f"  ✓ {r['name']}: {r['listings_found']} listings")
    
    if failed:
        print("\n--- Failed adapters ---")
        for r in failed:
            print(f"  ✗ {r['name']}: {r['error'][:60]}...")
    
    # Return results for programmatic use
    return results


if __name__ == "__main__":
    results = main()
