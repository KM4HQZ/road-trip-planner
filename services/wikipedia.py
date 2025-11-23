"""Wikipedia and Wikivoyage service."""

import requests
from typing import Optional, Dict


class WikipediaHelper:
    """Fetches Wikipedia and Wikivoyage content."""
    
    WIKI_API = "https://en.wikipedia.org/w/api.php"
    WIKIVOYAGE_API = "https://en.wikivoyage.org/w/api.php"
    USER_AGENT = "RoadTripPlanner/1.0 (https://github.com/KM4HQZ/road-trip-planner; Educational use)"
    
    @staticmethod
    def search_wikipedia(query: str) -> Optional[Dict[str, str]]:
        """
        Search Wikipedia and return article URL and summary.
        
        Args:
            query: Search term (e.g., "Grand Canyon National Park")
            
        Returns:
            Dict with 'url', 'title', 'summary' or None
        """
        try:
            headers = {'User-Agent': WikipediaHelper.USER_AGENT}
            
            # Search for article
            search_params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'format': 'json',
                'srlimit': 1
            }
            
            response = requests.get(WikipediaHelper.WIKI_API, params=search_params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('query', {}).get('search'):
                return None
            
            page_title = data['query']['search'][0]['title']
            
            # Get extract (summary)
            extract_params = {
                'action': 'query',
                'titles': page_title,
                'prop': 'extracts|info',
                'exintro': True,
                'explaintext': True,
                'inprop': 'url',
                'format': 'json'
            }
            
            response = requests.get(WikipediaHelper.WIKI_API, params=extract_params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return None
            
            page = list(pages.values())[0]
            
            # Get first 2-3 sentences for popup
            extract = page.get('extract', '')
            sentences = extract.split('. ')
            short_summary = '. '.join(sentences[:2]) + '.' if len(sentences) >= 2 else extract
            
            return {
                'url': page.get('fullurl', ''),
                'title': page.get('title', ''),
                'summary': short_summary[:300] + '...' if len(short_summary) > 300 else short_summary
            }
            
        except Exception as e:
            print(f"  ⚠️  Wikipedia search failed for '{query}': {e}")
            return None
    
    @staticmethod
    def search_wikivoyage(city_name: str) -> Optional[str]:
        """
        Get Wikivoyage URL for a city.
        
        Args:
            city_name: City name (e.g., "Denver")
            
        Returns:
            Wikivoyage URL or None
        """
        try:
            headers = {'User-Agent': WikipediaHelper.USER_AGENT}
            
            # Try exact match first
            params = {
                'action': 'query',
                'titles': city_name,
                'prop': 'info',
                'inprop': 'url',
                'format': 'json'
            }
            
            response = requests.get(WikipediaHelper.WIKIVOYAGE_API, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return None
            
            page = list(pages.values())[0]
            
            # Check if page exists (missing=-1)
            if page.get('missing'):
                return None
            
            return page.get('fullurl')
            
        except Exception as e:
            print(f"  ⚠️  Wikivoyage search failed for '{city_name}': {e}")
            return None
