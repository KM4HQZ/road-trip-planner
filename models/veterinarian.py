"""Veterinarian data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Veterinarian:
    """24/7 Emergency Veterinarian information."""
    name: str
    address: str
    location: str
    rating: float
    user_ratings_total: int
    place_id: str
    lat: float
    lon: float
    phone: Optional[str] = None
    website: Optional[str] = None
    is_24_hours: bool = False
    score: float = 0.0
