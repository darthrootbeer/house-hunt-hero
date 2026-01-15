from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from ..alerting.dispatch import dispatch_alert
from ..classify.scoring import score_listing
from ..dedupe.zillow_redfin import check_listing_status
from ..ingestion.registry import get_adapters
from ..normalization.mapper import normalize_many
from ..storage.state import StateStore
from ..utils.config import load_yaml


def _should_alert(status: str, score: Dict, runtime_cfg: Dict) -> bool:
    required_status = set(runtime_cfg.get("alerting", {}).get("require_status", []))
    if required_status and status not in required_status:
        return False
    minimum = runtime_cfg.get("scoring", {}).get("minimum_confidence", 0.7)
    return score.get("confidence", 0) >= minimum


def run_once(
    sources_cfg_path: str,
    runtime_cfg_path: str,
    profile_path: str,
    state_path: str,
) -> None:
    sources_cfg = load_yaml(sources_cfg_path)
    runtime_cfg = load_yaml(runtime_cfg_path)
    profile = load_yaml(profile_path)

    state = StateStore(state_path)

    adapters = get_adapters()
    raw_listings = []
    for adapter in adapters:
        raw_listings.extend(adapter.fetch())

    listings = normalize_many(raw_listings)
    now = datetime.now(timezone.utc).isoformat()

    for listing in listings:
        if state.has_seen(listing.listing_id):
            continue

        status = check_listing_status(listing)
        score = score_listing(listing, profile)

        if _should_alert(status, score, runtime_cfg):
            payload = {
                "listing_id": listing.listing_id,
                "status": status,
                "confidence": score.get("confidence", 0),
                "reason": score.get("reasons", []),
                "source": {
                    "id": listing.source,
                    "first_seen": listing.source_timestamp.isoformat(),
                },
                "listing": {
                    "address_raw": listing.address.raw,
                    "price": listing.price,
                    "url": listing.listing_url,
                },
            }
            dispatch_alert(payload)
            state.record_alert(listing.listing_id, now)

        state.mark_seen(listing.listing_id, now)

    state.close()
