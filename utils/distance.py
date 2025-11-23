"""Distance and scoring utility functions."""

import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float, unit: str = 'miles') -> float:
    """
    Calculate distance between two coordinate points using Haversine formula.
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
        unit: 'miles', 'km', or 'meters' (default: 'miles')
        
    Returns:
        Distance in specified unit
    """
    R_MILES = 3959
    R_KM = 6371
    R_METERS = 6371000
    
    radius = {'miles': R_MILES, 'km': R_KM, 'meters': R_METERS}.get(unit, R_MILES)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return radius * c


def calculate_popularity_score(rating: float, review_count: int) -> float:
    """
    Calculate popularity score based on rating and review count.
    Uses logarithmic scaling for reviews to prevent over-weighting popular places.
    
    Args:
        rating: Rating out of 5.0
        review_count: Number of reviews
        
    Returns:
        Popularity score (higher is better)
    """
    return rating * math.log10(review_count + 1) if review_count > 0 else rating
