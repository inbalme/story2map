#!/usr/bin/env python3
"""
Test script for debugging the LocationExtractor class.
Run this script directly in your IDE with breakpoints set for debugging.
"""

import os
import logging
import json
from dotenv import load_dotenv
from utils.location_extractor import LocationExtractor

# Configure logging to see debug messages
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see all log messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env', override=True)

def test_location_extraction():
    """Test the location extraction functionality."""
    
    # Sample texts containing locations (with varying complexity)
    test_texts = [
        # Simple text with explicit locations
        "I visited the Eiffel Tower in Paris and stayed at the Marriott Hotel.",
        
        # More complex text with multiple locations and context
        """We started our trip in New York City, visiting the Empire State Building 
        and having dinner at Peter Luger Steakhouse in Brooklyn. Later we went to 
        Washington D.C. to see the White House and the Smithsonian Museum.""",
        
        # Add your own text here that you want to test
        # "Your text here..."
    ]
    
    # Initialize the LocationExtractor
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("No Gemini API key found in environment variables. Set GEMINI_API_KEY in .env file.")
        return
    
    extractor = LocationExtractor(api_key=api_key)
    logger.info("LocationExtractor initialized")
    
    # Process each test text
    for i, text in enumerate(test_texts):
        logger.info(f"Processing test text #{i+1}")
        
        # This is a good place to set a breakpoint in your IDE
        logger.debug(f"Text to process: {text[:100]}...")
        
        # Extract locations
        locations = extractor.extract_locations(text)
        
        # Another good place for a breakpoint
        logger.info(f"Found {len(locations)} locations")
        
        # Print the results in a readable format
        print(f"\n--- Results for Test Text #{i+1} ---")
        if locations:
            print(json.dumps(locations, indent=2))
        else:
            print("No locations found")
        print("-----------------------------------\n")
        
        # Optional: Test specific part of the extraction process
        # For example, you could test just the geocoding step:
        # if locations:
        #     sample_location = {"name": "Eiffel Tower"}
        #     geocoded = extractor._geocode_locations([sample_location])
        #     print(f"Geocoding test result: {geocoded}")

def main():
    """Main function to run the tests."""
    logger.info("Starting LocationExtractor test script")
    test_location_extraction()
    logger.info("Test script completed")

if __name__ == "__main__":
    # Set breakpoint here to debug the entire script execution
    main() 