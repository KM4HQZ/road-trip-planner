"""Location data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Location:
    """Represents a location on the trip."""
    name: str
    lat: float
    lon: float
    type: str  # 'start', 'stop', 'destination', 'waypoint'
    wikivoyage_url: Optional[str] = None
