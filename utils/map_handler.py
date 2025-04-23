"""
Utility functions for handling maps, geocoding places, and calculating routes.
Uses Google Maps API for geocoding and route calculation.
"""

import os
import json
import time
import streamlit as st
import pandas as pd
import numpy as np
import polyline
import requests
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import io

# Load environment variables
load_dotenv()

def get_google_maps_api_key():
    """Get Google Maps API key from environment variables"""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        st.error("Google Maps API key not found in environment variables.")
    return api_key

def geocode_place(place_name: str) -> Optional[Dict[str, Any]]:
    """
    Geocode a place name using Google Maps Geocoding API
    
    Args:
        place_name: Name of the place to geocode
        
    Returns:
        Dictionary with place information including coordinates, or None if geocoding failed
    """
    api_key = get_google_maps_api_key()
    if not api_key:
        return None
    
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place_name}&key={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if data["status"] == "OK" and data["results"]:
            result = data["results"][0]
            location = result["geometry"]["location"]
            
            return {
                "name": place_name,
                "formatted_address": result["formatted_address"],
                "lat": location["lat"],
                "lng": location["lng"],
                "place_id": result.get("place_id", ""),
                "types": result.get("types", [])
            }
        else:
            st.warning(f"Could not geocode '{place_name}': {data['status']}")
            return None
    except Exception as e:
        st.error(f"Error geocoding '{place_name}': {e}")
        return None

def geocode_places(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Geocode a list of places
    
    Args:
        places: List of place dictionaries
        
    Returns:
        List of place dictionaries with added geocoding information
    """
    geocoded_places = []
    
    with st.spinner("Geocoding places..."):
        progress_bar = st.progress(0)
        
        for i, place in enumerate(places):
            geocoded_place = geocode_place(place["name"])
            if geocoded_place:
                # Merge the original place data with geocoded data
                merged_place = {**place, **geocoded_place}
                geocoded_places.append(merged_place)
                
                # Avoid rate limiting
                if i < len(places) - 1:
                    time.sleep(0.2)
                    
            progress_bar.progress((i + 1) / len(places))
    
    return geocoded_places

def create_folium_map(places: List[Dict[str, Any]], 
                     selected_places: List[str] = None,
                     route_data: Dict = None) -> folium.Map:
    """
    Create a Folium map with markers for the places
    
    Args:
        places: List of geocoded place dictionaries
        selected_places: List of selected place names
        route_data: Route data dictionary if available
        
    Returns:
        Folium Map object
    """
    if not places:
        return folium.Map(location=[0, 0], zoom_start=2)
    
    # Calculate center of the map
    lats = [p["lat"] for p in places if "lat" in p]
    lngs = [p["lng"] for p in places if "lng" in p]
    
    if not lats or not lngs:
        return folium.Map(location=[0, 0], zoom_start=2)
    
    center_lat = sum(lats) / len(lats)
    center_lng = sum(lngs) / len(lngs)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lng], zoom_start=10)
    
    # Add a marker cluster
    marker_cluster = MarkerCluster().add_to(m)
    
    # Add markers for each place
    for place in places:
        if "lat" not in place or "lng" not in place:
            continue
            
        # Determine marker color based on sentiment
        sentiment = place.get("sentiment", "neutral")
        if sentiment == "positive":
            color = "green"
        elif sentiment == "negative":
            color = "red"
        else:
            color = "blue"
            
        # Check if this place is selected
        is_selected = selected_places and place["name"] in selected_places
        
        # Create popup content
        popup_content = f"""
        <b>{place['name']}</b><br>
        {place.get('formatted_address', '')}<br>
        Type: {place.get('type', 'Unknown')}<br>
        Sentiment: {sentiment.capitalize()}<br>
        """
        
        if "notes" in place and place["notes"]:
            popup_content += f"Notes: {place['notes']}<br>"
        
        # Create marker with custom icon
        icon = folium.Icon(color=color, icon="info-sign" if is_selected else "")
        marker = folium.Marker(
            location=[place["lat"], place["lng"]],
            popup=folium.Popup(popup_content, max_width=300),
            icon=icon
        )
        
        marker.add_to(marker_cluster)
    
    # Add route polyline if route_data is provided
    if route_data and route_data.get("polyline"):
        points = polyline.decode(route_data["polyline"])
        folium.PolyLine(
            points,
            weight=5,
            color="blue",
            opacity=0.7,
            tooltip=f"{route_data.get('distance', 'Unknown')} - {route_data.get('duration', 'Unknown')}"
        ).add_to(m)
    
    return m

def get_route(origin: Dict[str, Any], 
             destination: Dict[str, Any], 
             waypoints: List[Dict[str, Any]] = None,
             mode: str = "driving") -> Optional[Dict[str, Any]]:
    """
    Get route information between places using Google Maps Directions API
    
    Args:
        origin: Origin place dictionary with lat/lng
        destination: Destination place dictionary with lat/lng
        waypoints: Optional list of waypoint dictionaries with lat/lng
        mode: Travel mode (driving, walking, bicycling, transit)
        
    Returns:
        Dictionary with route information or None if failed
    """
    api_key = get_google_maps_api_key()
    if not api_key:
        return None
    
    try:
        # Prepare origin and destination
        origin_param = f"{origin['lat']},{origin['lng']}"
        destination_param = f"{destination['lat']},{destination['lng']}"
        
        # Prepare waypoints if any
        waypoints_param = ""
        if waypoints:
            waypoint_coords = [f"{w['lat']},{w['lng']}" for w in waypoints]
            waypoints_param = f"&waypoints=optimize:true|{"|".join(waypoint_coords)}"
        
        # Build URL
        url = (f"https://maps.googleapis.com/maps/api/directions/json?"
               f"origin={origin_param}&destination={destination_param}"
               f"{waypoints_param}&mode={mode}&key={api_key}")
        
        response = requests.get(url)
        data = response.json()
        
        if data["status"] == "OK" and data["routes"]:
            route = data["routes"][0]
            leg = route["legs"][0]  # For simplicity, just use the first leg
            
            return {
                "distance": leg["distance"]["text"],
                "duration": leg["duration"]["text"],
                "start_address": leg["start_address"],
                "end_address": leg["end_address"],
                "steps": [
                    {
                        "instruction": step["html_instructions"],
                        "distance": step["distance"]["text"],
                        "duration": step["duration"]["text"]
                    }
                    for step in leg["steps"]
                ],
                "polyline": route["overview_polyline"]["points"]
            }
        else:
            st.warning(f"Could not get route: {data['status']}")
            return None
    except Exception as e:
        st.error(f"Error getting route: {e}")
        return None

def save_map_data(places: List[Dict[str, Any]], filename: str) -> bool:
    """
    Save map data to a JSON file
    
    Args:
        places: List of place dictionaries
        filename: Filename to save the data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Add .json extension if not present
        if not filename.endswith(".json"):
            filename += ".json"
            
        filepath = os.path.join("data", filename)
        
        with open(filepath, "w") as f:
            json.dump(places, f, indent=2)
            
        return True
    except Exception as e:
        st.error(f"Error saving map data: {e}")
        return False

def load_map_data(filename: str) -> List[Dict[str, Any]]:
    """
    Load map data from a JSON file
    
    Args:
        filename: Filename to load the data from
        
    Returns:
        List of place dictionaries
    """
    try:
        # Add .json extension if not present
        if not filename.endswith(".json"):
            filename += ".json"
            
        filepath = os.path.join("data", filename)
        
        with open(filepath, "r") as f:
            places = json.load(f)
            
        return places
    except Exception as e:
        st.error(f"Error loading map data: {e}")
        return []

def get_saved_maps() -> List[str]:
    """
    Get list of saved map filenames
    
    Returns:
        List of filenames without extension
    """
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Get all JSON files in the data directory
        files = [f for f in os.listdir("data") if f.endswith(".json")]
        
        # Return filenames without extension
        return [os.path.splitext(f)[0] for f in files]
    except Exception as e:
        st.error(f"Error getting saved maps: {e}")
        return [] 