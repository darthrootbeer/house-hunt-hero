from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from ..base import IngestionAdapter, RawListing


class MaineCreditUnionsDirectoryAdapter(IngestionAdapter):
    """Maine Credit Unions directory - Directory only, no property listings."""

    source_id = "maine_credit_unions_directory"

    def fetch(self) -> List[RawListing]:
        # Maine Credit Unions is a directory of credit unions, not a source of property listings
        # Individual credit unions would need to be checked separately
        return []
