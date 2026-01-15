from __future__ import annotations

from typing import List

from .adapters import CraigslistOwnerAdapter, CraigslistMaineAdapter, CraigslistNHAdapter
from .base import IngestionAdapter


def get_adapters() -> List[IngestionAdapter]:
    return [
        CraigslistOwnerAdapter(),   # SF Bay Area Craigslist
        CraigslistMaineAdapter(),   # Maine Craigslist (matches house profile)
        CraigslistNHAdapter(),      # New Hampshire Craigslist (near Maine)
    ]
