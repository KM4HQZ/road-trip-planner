"""Configuration and constants for the road trip planner."""

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
