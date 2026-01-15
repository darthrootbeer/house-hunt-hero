from __future__ import annotations

from typing import Dict


def send_email(payload: Dict) -> None:
    # Placeholder: wire up SMTP in implementation
    print(f"[email] {payload.get('listing_id')}")


def send_pushover(payload: Dict) -> None:
    # Placeholder: wire up Pushover API in implementation
    print(f"[pushover] {payload.get('listing_id')}")


def dispatch_alert(payload: Dict) -> None:
    send_email(payload)
    send_pushover(payload)
