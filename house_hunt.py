"""House Hunt Hero - Consolidated MVP implementation."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Literal, Optional

import yaml

# Types
ListingStatus = Literal["off_market", "pre_zillow", "already_public"]


@dataclass
class Address:
    raw: str
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


@dataclass
class Listing:
    listing_id: str
    source: str
    source_timestamp: datetime
    listing_url: str
    address: Address
    price: Optional[int] = None
    description_raw: Optional[str] = None
    image_urls: List[str] = field(default_factory=list)
    seller_type: str = "unknown"
    keywords_detected: List[str] = field(default_factory=list)


# State storage
class StateStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_listings (
                listing_id TEXT PRIMARY KEY,
                first_seen TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                listing_id TEXT,
                sent_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def has_seen(self, listing_id: str) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT 1 FROM seen_listings WHERE listing_id = ? LIMIT 1",
            (listing_id,),
        )
        return cur.fetchone() is not None

    def mark_seen(self, listing_id: str, first_seen: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO seen_listings (listing_id, first_seen) VALUES (?, ?)",
            (listing_id, first_seen),
        )
        self.conn.commit()

    def record_alert(self, listing_id: str, sent_at: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO alerts (listing_id, sent_at) VALUES (?, ?)",
            (listing_id, sent_at),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


# Ingestion - direct implementation (no adapter pattern)
def fetch_craigslist_listings() -> List[Dict]:
    """Fetch listings from Craigslist. Placeholder for real implementation."""
    return [
        {
            "source": "craigslist_owner",
            "source_timestamp": datetime.now(timezone.utc),
            "listing_url": "https://example.com/listing/placeholder",
            "title": "Placeholder listing",
            "raw_payload": {},
        }
    ]


# Normalization
def normalize_listing(raw: Dict) -> Listing:
    """Convert raw listing to normalized format."""
    return Listing(
        listing_id=f"{raw['source']}:{raw['listing_url']}",
        source=raw["source"],
        source_timestamp=raw.get("source_timestamp") or datetime.now(timezone.utc),
        listing_url=raw["listing_url"],
        address=Address(raw=raw.get("title", "")),
        description_raw=raw.get("title"),
    )


# Deduplication
def check_listing_status(listing: Listing) -> ListingStatus:
    """Check if listing exists on Zillow/Redfin. Placeholder for real implementation."""
    return "off_market"


# Scoring
def score_listing(listing: Listing, profile: Dict) -> Dict:
    """Score listing against house profile. Placeholder for real implementation."""
    return {
        "confidence": 0.5,
        "reasons": ["placeholder scoring"],
    }


# Alerting
def send_email(payload: Dict) -> None:
    """Send email alert. Placeholder for real implementation."""
    print(f"[email] {payload.get('listing_id')}")


def send_pushover(payload: Dict) -> None:
    """Send Pushover alert. Placeholder for real implementation."""
    print(f"[pushover] {payload.get('listing_id')}")


def dispatch_alert(payload: Dict) -> None:
    """Dispatch alerts via all configured channels."""
    send_email(payload)
    send_pushover(payload)


# Main execution
def load_yaml(path: str) -> Dict:
    """Load YAML config file."""
    data = yaml.safe_load(Path(path).read_text())
    return data or {}


def should_alert(status: str, score: Dict, runtime_cfg: Dict) -> bool:
    """Determine if listing should trigger an alert."""
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
    """Run one complete cycle: fetch, normalize, check, score, alert."""
    sources_cfg = load_yaml(sources_cfg_path)
    runtime_cfg = load_yaml(runtime_cfg_path)
    profile = load_yaml(profile_path)

    state = StateStore(state_path)

    # Fetch from all sources (currently just Craigslist)
    raw_listings = fetch_craigslist_listings()

    # Normalize
    listings = [normalize_listing(raw) for raw in raw_listings]
    now = datetime.now(timezone.utc).isoformat()

    # Process each listing
    for listing in listings:
        if state.has_seen(listing.listing_id):
            continue

        status = check_listing_status(listing)
        score = score_listing(listing, profile)

        if should_alert(status, score, runtime_cfg):
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


if __name__ == "__main__":
    run_once(
        sources_cfg_path="configs/sources.example.yaml",
        runtime_cfg_path="configs/runtime.example.yaml",
        profile_path="configs/house_profile.json",
        state_path="state/state.db",
    )
