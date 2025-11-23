"""Data models for the road trip planner."""

from .location import Location
from .hotel import Hotel
from .veterinarian import Veterinarian
from .attraction import Attraction, NationalPark

__all__ = [
    'Location',
    'Hotel',
    'Veterinarian',
    'Attraction',
    'NationalPark',
]
