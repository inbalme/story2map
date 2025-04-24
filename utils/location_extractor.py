import os
import logging
import google.generativeai as genai
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add a debug level log message for illustration
logger.debug("LocationExtractor module loaded")

# Load environment variables
load_dotenv()

class LocationExtractor:
    """Class to extract location information from text using Gemini."""
    
    def __init__(self, api_key: str = None):
        """Initialize the LocationExtractor with a Gemini API key."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("No Gemini API key provided. Location extraction will not work.")
            return
            
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
            self.model = None
    
    def extract_locations(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract locations from the given text along with relevant tags.
        
        Args:
            text: The text to extract locations from
            
        Returns:
            A list of dictionaries, each containing location information:
            {
                'name': str,
                'latitude': float,
                'longitude': float,
                'tags': List[str],
                'description': str
            }
        """
        if not self.model:
            logger.error("Gemini model not initialized. Cannot extract locations.")
            return []
            
        try:
            # Prompt for the Gemini model to extract locations and tag them
            prompt = """
            Extract all place names or locations mentioned in the following text. 
            For each location, provide:
            1. The exact name as it appears in the text
            2. The most relevant tags from this list: landmark, accommodation, eating, drinking, snacks, 
               groceries, restaurant, bar, cafe, nightlife, attraction, viewpoint, concert, shopping, transportation, natural, cultural
            3. A brief description based on the context in the text (if available)
            
            Format your response as a JSON array of objects with these fields:
            [
                {
                    "name": "Location name",
                    "tags": ["tag1", "tag2"],
                    "description": "Brief description from the context"
                }
            ]
            
            Only return the JSON array, nothing else. If no locations are found, return an empty array: []
            
            Here is the text:
            
            """
            
            prompt += text
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            content = response.text
            
            # Parse out the JSON from the response
            import json
            import re
            
            # Clean up the response to extract just the JSON part
            json_match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Try to extract anything that looks like JSON
                json_str = content.strip()
                if not (json_str.startswith('[') and json_str.endswith(']')):
                    # If response doesn't look like JSON at all, return empty list
                    logger.warning(f"Could not extract JSON from response: {content}")
                    return []
            
            try:
                locations = json.loads(json_str)
                
                # Geocode to get coordinates
                enriched_locations = self._geocode_locations(locations)
                return enriched_locations
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Gemini response: {e}")
                logger.debug(f"Raw response: {content}")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting locations with Gemini: {e}")
            return []
    
    def _geocode_locations(self, locations: List[Dict]) -> List[Dict]:
        """
        Add latitude and longitude to the location dictionaries.
        
        Args:
            locations: List of location dictionaries
            
        Returns:
            The same list with latitude and longitude added to each dictionary
        """
        import geocoder
        
        enriched_locations = []
        
        for loc in locations:
            try:
                g = geocoder.arcgis(loc['name'])
                if g.ok:
                    loc['latitude'] = g.lat
                    loc['longitude'] = g.lng
                    enriched_locations.append(loc)
                else:
                    logger.warning(f"Could not geocode location: {loc['name']}")
            except Exception as e:
                logger.error(f"Error geocoding {loc['name']}: {e}")
        
        return enriched_locations 