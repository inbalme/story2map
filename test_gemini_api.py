#!/usr/bin/env python3
"""
Test script for debugging the Gemini API integration in LocationExtractor.
This isolates just the Gemini API interaction for focused debugging.
"""

import os
import logging
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_gemini_api():
    """Test the Gemini API functionality directly."""
    
    # Sample text to test extraction
    test_text = """
    We started our trip in New York City, visiting the Empire State Building 
    and having dinner at Peter Luger Steakhouse in Brooklyn. Later we went to 
    Washington D.C. to see the White House and the Smithsonian Museum.
    """
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("No Gemini API key found in environment variables. Set GEMINI_API_KEY in .env file.")
        return
    
    logger.info("Starting Gemini API test")
    
    try:
        # Configure Gemini API - This is a good breakpoint location
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        logger.info("Gemini API initialized successfully")
        
        # Create prompt similar to what's used in LocationExtractor
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
        
        prompt += test_text
        
        # Set breakpoint here to inspect prompt
        logger.debug(f"Sending prompt to Gemini: {prompt[:100]}...")
        
        # Make the API call - Another good breakpoint location
        response = model.generate_content(prompt)
        
        # Inspect raw response - Another good breakpoint location
        logger.debug(f"Received raw response: {response.text[:100]}...")
        
        # Process response similar to LocationExtractor
        content = response.text
        
        # Parse JSON from response
        import re
        
        json_match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            # Try to extract anything that looks like JSON
            json_str = content.strip()
            if not (json_str.startswith('[') and json_str.endswith(']')):
                logger.warning(f"Could not extract JSON from response: {content}")
                json_str = "[]"
        
        # Print results
        try:
            locations = json.loads(json_str)
            
            print("\n--- Extracted Locations via Gemini ---")
            print(json.dumps(locations, indent=2))
            print("------------------------------------\n")
            
            logger.info(f"Successfully extracted {len(locations)} locations")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.debug(f"Raw response: {content}")
            
    except Exception as e:
        logger.error(f"Error in Gemini API test: {e}")

def test_gemini_response_handling():
    """Test different potential Gemini API responses to ensure robust handling."""
    
    # Sample responses - these simulate what Gemini might return
    test_responses = [
        # Well-formatted JSON response
        """
        [
            {
                "name": "Empire State Building",
                "tags": ["landmark", "attraction", "viewpoint"],
                "description": "A famous skyscraper in New York City"
            },
            {
                "name": "Brooklyn",
                "tags": ["cultural"],
                "description": "A borough of New York City"
            }
        ]
        """,
        
        # JSON with surrounding text
        """
        Here are the locations I found:
        
        [
            {
                "name": "White House",
                "tags": ["landmark", "cultural"],
                "description": "The official residence of the US President"
            }
        ]
        """,
        
        # Malformed JSON
        """
        [
            {
                "name": "Smithsonian Museum"
                "tags": ["cultural", "attraction"],
                "description": "A group of museums in Washington D.C."
            }
        ]
        """,
        
        # Empty JSON
        "[]",
        
        # Non-JSON
        "I couldn't find any locations in the text provided."
    ]
    
    print("\n--- Testing Response Handling ---")
    
    for i, response in enumerate(test_responses):
        print(f"\nTest response #{i+1}:")
        
        try:
            # Extract JSON using the same regex as in LocationExtractor
            import re
            
            json_match = re.search(r'\[\s*{.*}\s*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                print(f"Extracted JSON with regex: {json_str[:50]}...")
            else:
                # Try to extract anything that looks like JSON
                json_str = response.strip()
                if json_str.startswith('[') and json_str.endswith(']'):
                    print(f"Using full response as JSON: {json_str[:50]}...")
                else:
                    print(f"Could not extract JSON from response: {response[:50]}...")
                    json_str = "[]"
            
            # Try to parse the JSON
            try:
                locations = json.loads(json_str)
                print(f"Successfully parsed JSON with {len(locations)} locations")
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                
        except Exception as e:
            print(f"Processing error: {e}")
    
    print("\n------------------------------------")

def main():
    """Main function to run all tests."""
    logger.info("Starting Gemini API test script")
    test_gemini_api()
    test_gemini_response_handling()
    logger.info("Test script completed")

if __name__ == "__main__":
    # Set breakpoint here to debug the entire script execution
    main() 