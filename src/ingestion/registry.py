from __future__ import annotations

from typing import List

from .adapters import (
    CraigslistOwnerAdapter,
    CraigslistMaineAdapter,
    CraigslistNHAdapter,
    OwneramaAdapter,
    BrokerlessAdapter,
    FlatFeeGroupAdapter,
    TheRockFoundationAdapter,
    FSBOHomeListingsAdapter,
    DIYFlatFeeAdapter,
    ISoldMyHouseAdapter,
    HoangRealtyFSBOAdapter,
    OodleAdapter,
    TownAdsAdapter,
    SunJournalAdapter,
    AdvertiserDemocratAdapter,
    MidcoastVillagerAdapter,
    PortlandPressHeraldAdapter,
    FacebookMarketplaceAdapter,
    FacebookGroupsAdapter,
    NextdoorAdapter,
    BankOwnedPropertiesAdapter,
    DistressedProAdapter,
    MaineCommunityBankAdapter,
    OnPointRealtyAdapter,
    YorkCountyProbateAdapter,
    MunicipalTaxAssessorAdapter,
)
from .base import IngestionAdapter


def get_adapters() -> List[IngestionAdapter]:
    return [
        CraigslistOwnerAdapter(),   # SF Bay Area Craigslist
        CraigslistMaineAdapter(),   # Maine Craigslist (matches house profile)
        CraigslistNHAdapter(),      # New Hampshire Craigslist (near Maine)
        OwneramaAdapter(),          # Ownerama FSBO platform
        BrokerlessAdapter(),        # Brokerless FSBO platform
        FlatFeeGroupAdapter(),      # Flat Fee Group FSBO platform
        TheRockFoundationAdapter(), # The Rock Foundation FSBO platform
        FSBOHomeListingsAdapter(),  # FSBOHomeListings.com
        DIYFlatFeeAdapter(),        # DIY Flat Fee MLS
        ISoldMyHouseAdapter(),      # ISoldMyHouse.com
        HoangRealtyFSBOAdapter(),   # Hoang Realty FSBO Program
        OodleAdapter(),             # Oodle classifieds
        TownAdsAdapter(),           # Town-Ads.com classifieds
        SunJournalAdapter(),        # Sun Journal (Lewiston)
        AdvertiserDemocratAdapter(), # Advertiser Democrat (Oxford Hills)
        MidcoastVillagerAdapter(),  # Midcoast Villager (Knox/Waldo)
        PortlandPressHeraldAdapter(), # Portland Press Herald
        FacebookMarketplaceAdapter(), # Facebook Marketplace
        FacebookGroupsAdapter(),    # Facebook Groups
        NextdoorAdapter(),          # Nextdoor
        BankOwnedPropertiesAdapter(), # BankOwnedProperties.org aggregator
        DistressedProAdapter(),      # DistressedPro.com aggregator
        MaineCommunityBankAdapter(), # Maine Community Bank REO listings
        OnPointRealtyAdapter(),      # State Tax-Acquired Properties (MRS)
        YorkCountyProbateAdapter(),  # York County Probate Court estate notices
        # MunicipalTaxAssessorAdapter() - Disabled by default, configure per municipality
    ]
