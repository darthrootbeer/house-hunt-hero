from __future__ import annotations

from typing import List

from .adapters import CraigslistOwnerAdapter
from .base import IngestionAdapter


def get_adapters() -> List[IngestionAdapter]:
    return [
        CraigslistOwnerAdapter(),
    ]
