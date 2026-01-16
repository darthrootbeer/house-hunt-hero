from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from ..base import IngestionAdapter, RawListing


class MaineStateCreditUnionAdapter(IngestionAdapter):
    """Maine State Credit Union - Commercial real estate loans only, no property listings."""

    source_id = "maine_state_credit_union"

    def fetch(self) -> List[RawListing]:
        # Maine State Credit Union provides commercial real estate loans, not property listings
        # Documented as contact_required in config
        return []
