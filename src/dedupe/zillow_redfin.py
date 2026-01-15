from __future__ import annotations

from typing import Literal

from ..normalization.schema import Listing

ListingStatus = Literal["off_market", "pre_zillow", "already_public"]


def check_listing_status(listing: Listing) -> ListingStatus:
    # Placeholder: real implementation will compare against cached Zillow/Redfin data.
    return "off_market"
