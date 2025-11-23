"""Attraction data models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Attraction:
    """Park or attraction information."""
    name: str
    address: str
    location: str
    type: str  # 'park', 'attraction'
    rating: float
    user_ratings_total: int
    lat: float
    lon: float
    website: Optional[str] = None
    wikipedia_url: Optional[str] = None
    wikipedia_summary: Optional[str] = None


@dataclass
class NationalPark:
    """Major National Park information."""
    name: str
    address: str
    state: str
    rating: float
    user_ratings_total: int
    lat: float
    lon: float
    website: Optional[str] = None
    wikipedia_url: Optional[str] = None
    wikipedia_summary: Optional[str] = None
