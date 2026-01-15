from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from ..base import IngestionAdapter, RawListing


class HoangRealtyFSBOAdapter(IngestionAdapter):
    """
    Hoang Realty FSBO Program adapter.
    
    Note: Based on research, Hoang Realty may require direct contact for FSBO listings.
    This adapter returns empty list as listings may not be publicly searchable.
    """

    source_id = "hoang_realty_fsbo"
    # Contact info for reference
    CONTACT_URL = "https://hoangrealty.com/for-sale-by-owner"

    def fetch(self) -> List[RawListing]:
        """
        Fetch listings from Hoang Realty FSBO Program.
        
        Note: This source may require direct contact. Returns empty list
        as listings are not publicly searchable on their website.
        """
        # Based on research, Hoang Realty FSBO listings are not publicly
        # searchable on their website. They require direct contact.
        # This adapter is a placeholder that can be enhanced if a public
        # listing page becomes available.
        return []
