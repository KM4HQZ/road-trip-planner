"""Configuration and constants for the road trip planner."""

from dataclasses import dataclass


@dataclass
class TripConfig:
    """Configuration for what to search and include in trip planning."""
    
    # Accommodation options
    search_hotels: bool = True
    pet_friendly_only: bool = True  # If False, search all hotels
    
    # Emergency services
    search_vets: bool = True
    
    # Attraction categories
    search_national_parks: bool = True
    search_monuments: bool = True
    search_parks: bool = True
    search_museums: bool = True
    search_restaurants: bool = True
    search_dog_parks: bool = True
    search_viewpoints: bool = True
    search_ev_chargers: bool = True
    
    # Export options
    export_gpx: bool = True
    export_map: bool = True
    export_summary: bool = True
    export_data: bool = True
    
    @classmethod
    def all_enabled(cls):
        """Create config with all options enabled (default)."""
        return cls()
    
    @classmethod
    def minimal(cls):
        """Create config with minimal options (route only)."""
        return cls(
            search_hotels=False,
            search_vets=False,
            search_national_parks=False,
            search_monuments=False,
            search_parks=False,
            search_museums=False,
            search_restaurants=False,
            search_dog_parks=False,
            search_viewpoints=False,
            search_ev_chargers=False,
            export_gpx=False,
            export_summary=False
        )


# State abbreviation mapping
STATE_ABBREV_TO_NAME = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming'
}

# Reverse mapping for state name -> abbreviation
STATE_NAME_TO_ABBREV = {v.lower(): k for k, v in STATE_ABBREV_TO_NAME.items()}

# Pet-friendly hotel chains
PET_FRIENDLY_CHAINS = [
    'la quinta', 'drury', 'kimpton', 'red roof', 'motel 6',
    'best western', 'residence inn', 'towneplace', 'staybridge',
    'aloft', 'element', 'extended stay', 'candlewood', 'homewood',
    'springhill', 'fairfield', 'comfort inn', 'quality inn',
    'sleep inn', 'econo lodge', 'days inn', 'super 8',
    'knights inn', 'travelodge', 'ramada', 'wyndham',
    'howard johnson', 'microtel', 'baymont', 'hampton', 'hilton',
    'marriott', 'hyatt', 'sheraton', 'westin', 'doubletree',
    'holiday inn', 'courtyard', 'country inn'
]
