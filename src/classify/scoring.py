from __future__ import annotations

from typing import Dict

from ..normalization.schema import Listing


def score_listing(listing: Listing, profile: Dict) -> Dict:
    # Placeholder scoring logic
    return {
        "confidence": 0.5,
        "reasons": ["placeholder scoring"],
    }
