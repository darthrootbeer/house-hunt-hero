from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Address(BaseModel):
    raw: str
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class Geo(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None


class Listing(BaseModel):
    listing_id: str
    source: str
    source_timestamp: datetime
    listing_url: str
    address: Address
    geo: Geo = Field(default_factory=Geo)
    price: Optional[int] = None
    description_raw: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)
    seller_type: str = "unknown"
    keywords_detected: List[str] = Field(default_factory=list)

