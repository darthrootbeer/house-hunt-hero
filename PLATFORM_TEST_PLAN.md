# Platform Search Test Plan

## Overview

This plan outlines how to test all 49 active property search platforms to verify they can successfully find and return property listings. The test will generate a clear, easy-to-read report showing which platforms are working and which ones need attention.

## Goals

1. Test every active platform to see if it can find properties
2. Verify that each platform returns actual property listings (not just empty results)
3. Generate a report that anyone can understand, without technical jargon
4. Identify which platforms are working well and which ones need fixes

## What Will Be Tested

All 49 active platforms organized by category:

### Classifieds & Marketplaces (3 platforms)
- Craigslist (SF Bay Area)
- Craigslist (Maine)
- Craigslist (New Hampshire)

### For Sale By Owner Platforms (8 platforms)
- Ownerama
- Brokerless
- Flat Fee Group
- The Rock Foundation
- FSBOHomeListings.com
- DIY Flat Fee MLS
- ISoldMyHouse.com
- Hoang Realty FSBO Program

### Online Classifieds (2 platforms)
- Oodle
- Town-Ads.com

### Local Newspapers (4 platforms)
- Sun Journal (Lewiston)
- Advertiser Democrat (Oxford Hills)
- Midcoast Villager (Knox/Waldo)
- Portland Press Herald

### Social Media Platforms (3 platforms)
- Facebook Marketplace
- Facebook Groups
- Nextdoor

### Bank & REO Properties (3 platforms)
- BankOwnedProperties.org
- DistressedPro.com
- Maine Community Bank

### Government Sources (2 platforms)
- OnPoint Realty (State Tax-Acquired Properties)
- York County Probate Court

### Auction Sites (3 platforms)
- EstateSale.com
- GoToAuction.com
- Homes.com (auctions)

### Investment & Wholesale Networks (6 platforms)
- QuickFlip Construction
- Motivate Maine Wholesale Network
- Connected Investors
- Discounted Property Solutions
- HouseCashin
- OfferMarket

### MLS & Real Estate Agencies (13 platforms)
- Maine Listings (Official MLS)
- Maine State MLS
- Listings Direct
- Meservier & Associates
- Locations Real Estate Group
- Swan Agency Real Estate
- The Maine Agents
- Sargent Real Estate
- Allied Realty
- Landing Real Estate
- La Count Real Estate
- Realty of Maine
- Maine Real Estate Co.

### Credit Unions & REO (2 platforms)
- Fontaine Family (REO Division)
- Maine Highlands Federal Credit Union

## How Testing Will Work

### Step 1: Run Each Platform Search
For each platform:
1. Start a search using the platform's search system
2. Wait for results to load
3. Collect all property listings found
4. Record how long the search took
5. Note any errors or problems

### Step 2: Validate Results
For each platform that returns listings:
1. Check that each listing has:
   - A property title or description
   - A link to view the full listing
   - Basic property information
2. Verify the listings are real properties (not errors or empty pages)
3. Count how many valid listings were found

### Step 3: Categorize Results
Each platform will be placed into one of these categories:
- **Working Well**: Found listings and all listings are valid
- **Working But Empty**: Search worked but no properties found (may be normal)
- **Has Problems**: Search failed or returned invalid results
- **Needs Attention**: Search worked but some listings had issues

## Report Structure

The report will be written in plain language that anyone can understand. It will include:

### Executive Summary
- Total platforms tested
- How many are working well
- How many found properties
- How many need attention

### Results by Category
Each category (Classifieds, FSBO, Newspapers, etc.) will show:
- Which platforms are working
- How many properties each found
- Any issues that came up

### Platform Details
For each platform:
- **Status**: Working / Empty / Problem
- **Properties Found**: Number of listings
- **Search Time**: How long it took
- **Sample Properties**: 2-3 example property titles
- **Notes**: Any special observations

### Issues & Recommendations
- List of platforms that need fixes
- What the problem is (in plain language)
- Suggested next steps

## Success Criteria

A platform is considered successful if:
1. The search completes without crashing
2. It returns at least one valid property listing, OR
3. It returns zero listings but the search clearly worked (no errors)

A platform needs attention if:
1. The search crashes or times out
2. It returns invalid or broken listings
3. It can't access the website at all

## Expected Outcomes

- **Best Case**: All 49 platforms work and return results
- **Realistic Case**: 30-40 platforms work, some return results, some are empty (which is normal)
- **Needs Work**: 10-20 platforms have issues that need fixing

## Report Format

The final report will be saved as a Markdown file that can be:
- Read in any text editor
- Converted to PDF
- Shared with team members
- Used to track improvements over time

## Next Steps After Testing

1. Review the report to see which platforms are working
2. Fix any platforms that have problems
3. Investigate platforms that returned zero results (may be normal or may need adjustment)
4. Update the system based on findings
5. Re-test platforms that had issues after fixes are made
