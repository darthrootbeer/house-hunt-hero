from __future__ import annotations

from datetime import datetime
from typing import List

from ..base import IngestionAdapter, RawListing


class CraigslistOwnerAdapter(IngestionAdapter):
    source_id = "craigslist_owner"

    def fetch(self) -> List[RawListing]:
        # Placeholder adapter; real implementation will scrape public pages.
        return [
            RawListing(
                source=self.source_id,
                source_timestamp=datetime.utcnow(),
                listing_url="https://example.com/listing/placeholder",
                title="Placeholder listing",
                raw_payload={},
            )
        ]
