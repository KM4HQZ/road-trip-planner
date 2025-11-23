"""Hotel data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Hotel:
    """Hotel information."""
    name: str
    address: str
    location: str
    rating: float
    user_ratings_total: int
    price_level: Optional[str]
    place_id: str
    lat: float
    lon: float
    phone: Optional[str] = None
    website: Optional[str] = None
    score: float = 0.0
