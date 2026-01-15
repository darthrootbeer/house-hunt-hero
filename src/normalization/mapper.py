from __future__ import annotations

from datetime import datetime
from typing import List

from ..ingestion.base import RawListing
from .schema import Address, Listing


def normalize(raw: RawListing) -> Listing:
    return Listing(
        listing_id=f"{raw.source}:{raw.listing_url}",
        source=raw.source,
        source_timestamp=raw.source_timestamp or datetime.utcnow(),
        listing_url=raw.listing_url,
        address=Address(raw=raw.title),
        description_raw=raw.title,
    )


def normalize_many(raw_listings: List[RawListing]) -> List[Listing]:
    return [normalize(item) for item in raw_listings]
