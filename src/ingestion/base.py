from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class RawListing:
    source: str
    source_timestamp: datetime
    listing_url: str
    title: str
    raw_payload: Dict


class IngestionAdapter:
    source_id: str

    def fetch(self) -> List[RawListing]:
        raise NotImplementedError
