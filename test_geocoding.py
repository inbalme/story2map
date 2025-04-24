#!/usr/bin/env python3
"""
Test script for debugging the geocoding functionality in LocationExtractor.
This isolates just the geocoding part for focused debugging.
"""

import os
import logging
import json
import geocoder
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_geocoding():
    """Test the geocoding functionality directly."""
    
    # Sample locations to test geocoding
    test_locations = [
        "Eiffel Tower, Paris",
        "Empire State Building, New York",
        "Taj Mahal, India",
        "Sydney Opera House",
        "Colosseum, Rome",
        # Add more locations to test
    ]
    
    results = []
    
    logger.info("Starting geocoding tests")
    
    for location in test_locations:
        logger.debug(f"Geocoding: {location}")
        
        # This is a good place for a breakpoint
        try:
            # Use the same geocoding method as in LocationExtractor
            g = geocoder.arcgis(location)
            
            # Another good breakpoint location
            if g.ok:
                result = {
                    "name": location,
                    "latitude": g.lat,
                    "longitude": g.lng,
                    "address": g.address,
                    "success": True
                }
                logger.info(f"Successfully geocoded: {location}")
            else:
                result = {
                    "name": location,
                    "success": False,
                    "error": "Geocoding failed"
                }
                logger.warning(f"Failed to geocode: {location}")
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error geocoding {location}: {e}")
            results.append({
                "name": location,
                "success": False,
                "error": str(e)
            })
    
    # Print results
    print("\n--- Geocoding Results ---")
    print(json.dumps(results, indent=2))
    print("-------------------------\n")
    
    # Additional debugging: test with a deliberate error
    try:
        logger.debug("Testing with empty location string")
        g = geocoder.arcgis("")
        print(f"Empty string test result: {'Success' if g.ok else 'Failed'}")
    except Exception as e:
        logger.error(f"Error with empty string test: {e}")

def test_alternative_geocoding_providers():
    """
    Test alternative geocoding providers as a fallback option.
    This is useful if arcgis is having issues.
    """
    location = "Eiffel Tower, Paris"
    
    providers = [
        ("ArcGIS", lambda loc: geocoder.arcgis(loc)),
        ("OpenStreetMap", lambda loc: geocoder.osm(loc)),
        ("Google", lambda loc: geocoder.google(loc, key=os.getenv("GOOGLE_MAPS_API_KEY")))
    ]
    
    print("\n--- Alternative Geocoding Providers ---")
    
    for name, provider_func in providers:
        try:
            logger.debug(f"Testing {name} provider with '{location}'")
            
            # Skip Google if no API key is available
            if name == "Google" and not os.getenv("GOOGLE_MAPS_API_KEY"):
                print(f"{name}: Skipped (no API key)")
                continue
                
            g = provider_func(location)
            
            if g.ok:
                print(f"{name}: Success ({g.lat}, {g.lng})")
            else:
                print(f"{name}: Failed")
        except Exception as e:
            print(f"{name}: Error - {str(e)}")
    
    print("------------------------------------\n")

def main():
    """Main function to run all tests."""
    logger.info("Starting geocoding test script")
    test_geocoding()
    test_alternative_geocoding_providers()
    logger.info("Test script completed")

if __name__ == "__main__":
    # Set breakpoint here to debug the entire script execution
    main() 