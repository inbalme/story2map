"""
Story2Map - Streamlit application for extracting place names from text and mapping them.
"""

import os
import time
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from utils.text_extraction import get_clipboard_text, get_text_from_image, get_text_from_url
from utils.place_extraction import (extract_places_with_spacy, extract_places_with_gemini, 
                                    combine_place_extractions)
from utils.map_handler import (geocode_places, create_folium_map, get_route,
                              save_map_data, load_map_data, get_saved_maps)
from streamlit_folium import folium_static
import base64
from io import BytesIO

# Load environment variables
load_dotenv()

# Initialize session state variables if they don't exist
if "places" not in st.session_state:
    st.session_state.places = []
if "geocoded_places" not in st.session_state:
    st.session_state.geocoded_places = []
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "route_data" not in st.session_state:
    st.session_state.route_data = None
if "selected_places" not in st.session_state:
    st.session_state.selected_places = []

def update_place_note(place_index, note, sentiment):
    """Update note and sentiment for a place"""
    if 0 <= place_index < len(st.session_state.geocoded_places):
        st.session_state.geocoded_places[place_index]["notes"] = note
        st.session_state.geocoded_places[place_index]["sentiment"] = sentiment

def main():
    st.title("Story2Map")
    st.subheader("Extract Places from Text and Map Them")
    
    # Create tabs for different sections of the app
    tab1, tab2, tab3 = st.tabs(["📝 Input Text", "🗺️ Map View", "🔍 Route Planning"])
    
    with tab1:
        input_text_section()
    
    with tab2:
        map_view_section()
    
    with tab3:
        route_planning_section()

def input_text_section():
    """Section for text input and place extraction"""
    # Create tabs for different input methods
    input_tab1, input_tab2, input_tab3 = st.tabs(["📋 Clipboard", "📷 Screenshot", "🔗 URL"])
    
    # Clipboard input
    with input_tab1:
        st.subheader("Paste Text from Clipboard")
        
        if st.button("Get Text from Clipboard"):
            with st.spinner("Getting text from clipboard..."):
                clipboard_text = get_clipboard_text()
                if clipboard_text:
                    st.session_state.input_text = clipboard_text
        
        text_area = st.text_area("Or paste text manually:", 
                                value=st.session_state.input_text,
                                height=300)
        st.session_state.input_text = text_area
    
    # Screenshot input
    with input_tab2:
        st.subheader("Extract Text from Screenshot")
        st.write("Copy an image to clipboard and click the button below to extract text from it.")
        
        if st.button("Extract Text from Clipboard Image"):
            with st.spinner("Extracting text from image..."):
                image_text = get_text_from_image()
                if image_text:
                    st.session_state.input_text = image_text
                    st.success("Text extracted successfully!")
                else:
                    st.error("Failed to extract text from image. Make sure you have an image copied to clipboard.")
    
    # URL input
    with input_tab3:
        st.subheader("Extract Text from URL")
        url = st.text_input("Enter URL:")
        
        if st.button("Extract Text from URL"):
            if url:
                with st.spinner("Extracting text from URL..."):
                    url_text = get_text_from_url(url)
                    if url_text:
                        st.session_state.input_text = url_text
                        st.success("Text extracted successfully!")
                    else:
                        st.error("Failed to extract text from URL.")
            else:
                st.warning("Please enter a URL.")
    
    # Display the current text
    st.subheader("Current Text")
    if st.session_state.input_text:
        st.write(f"Text length: {len(st.session_state.input_text)} characters")
        with st.expander("Show Text"):
            st.text(st.session_state.input_text)
    else:
        st.info("No text has been provided yet.")
    
    # Place extraction
    st.subheader("Extract Places")
    col1, col2 = st.columns(2)
    
    with col1:
        use_spacy = st.checkbox("Use spaCy for basic extraction", value=True)
    
    with col2:
        use_gemini = st.checkbox("Use Google Gemini for enhanced extraction", value=True)
    
    if st.button("Extract Places"):
        if st.session_state.input_text:
            with st.spinner("Extracting places..."):
                # Get places using spaCy
                spacy_places = []
                if use_spacy:
                    spacy_places = extract_places_with_spacy(st.session_state.input_text)
                
                # Get places using Gemini
                gemini_places = []
                if use_gemini:
                    gemini_places = extract_places_with_gemini(st.session_state.input_text)
                
                # Combine results
                combined_places = combine_place_extractions(spacy_places, gemini_places)
                
                # Store in session state
                st.session_state.places = combined_places
                
                # Show results
                st.success(f"Extracted {len(combined_places)} places.")
                
                # Geocode places
                if combined_places:
                    st.session_state.geocoded_places = geocode_places(combined_places)
                    st.success(f"Successfully geocoded {len(st.session_state.geocoded_places)} places.")
        else:
            st.warning("Please provide some text first.")
    
    # Display extracted places
    if st.session_state.places:
        st.subheader("Extracted Places")
        
        # Create a DataFrame for better display
        places_df = pd.DataFrame([
            {
                "Name": p["name"],
                "Type": p.get("type", "Unknown"),
                "Sentiment": p.get("sentiment", "neutral").capitalize(),
                "Mentions": p.get("mentions", 1)
            }
            for p in st.session_state.places
        ])
        
        st.dataframe(places_df)

def map_view_section():
    """Section for map visualization and saving/loading maps"""
    st.subheader("Map View")
    
    # Map operations
    col1, col2 = st.columns(2)
    
    with col1:
        # Save map
        if st.session_state.geocoded_places:
            map_name = st.text_input("Map name:", key="save_map_name")
            if st.button("Save Map") and map_name:
                if save_map_data(st.session_state.geocoded_places, map_name):
                    st.success(f"Map '{map_name}' saved successfully!")
                else:
                    st.error("Failed to save map.")
    
    with col2:
        # Load map
        saved_maps = get_saved_maps()
        if saved_maps:
            selected_map = st.selectbox("Select a map to load:", saved_maps)
            if st.button("Load Map") and selected_map:
                loaded_places = load_map_data(selected_map)
                if loaded_places:
                    st.session_state.geocoded_places = loaded_places
                    st.success(f"Map '{selected_map}' loaded successfully!")
                else:
                    st.error("Failed to load map.")
        else:
            st.info("No saved maps found.")
    
    # Place annotations
    if st.session_state.geocoded_places:
        st.subheader("Place Annotations")
        
        # Create a select box for choosing a place to annotate
        place_names = [p["name"] for p in st.session_state.geocoded_places]
        selected_place_index = st.selectbox("Select a place to annotate:", 
                                           range(len(place_names)), 
                                           format_func=lambda i: place_names[i])
        
        selected_place = st.session_state.geocoded_places[selected_place_index]
        
        # Note and sentiment for the selected place
        note = st.text_area("Notes:", value=selected_place.get("notes", ""))
        sentiment = st.radio("Sentiment:", 
                            ["positive", "neutral", "negative"],
                            index=["positive", "neutral", "negative"].index(selected_place.get("sentiment", "neutral")))
        
        if st.button("Update Place Information"):
            update_place_note(selected_place_index, note, sentiment)
            st.success("Place information updated!")
    
    # Display the map
    st.subheader("Map")
    if st.session_state.geocoded_places:
        # Create and display the map
        m = create_folium_map(st.session_state.geocoded_places, 
                             st.session_state.selected_places,
                             st.session_state.route_data)
        folium_static(m)
        
        # Add download link for the map
        st.download_button(
            label="Download Map as HTML",
            data=m.get_root().render(),
            file_name="map.html",
            mime="text/html"
        )
    else:
        st.info("Extract places from text to display them on the map.")

def route_planning_section():
    """Section for route planning between selected places"""
    st.subheader("Route Planning")
    
    if not st.session_state.geocoded_places:
        st.info("Extract places from text to plan routes between them.")
        return
    
    # Place selection for route
    place_names = [p["name"] for p in st.session_state.geocoded_places]
    
    # Origin and destination
    st.subheader("Select Route Points")
    
    col1, col2 = st.columns(2)
    
    with col1:
        origin_index = st.selectbox("Starting Point:", 
                                   range(len(place_names)), 
                                   format_func=lambda i: place_names[i],
                                   key="origin")
    
    with col2:
        destination_index = st.selectbox("Destination:", 
                                        range(len(place_names)), 
                                        format_func=lambda i: place_names[i],
                                        key="destination")
    
    # Waypoints (optional)
    st.subheader("Waypoints (Optional)")
    
    # Get all indices except origin and destination
    available_waypoints = [i for i in range(len(place_names)) 
                          if i != origin_index and i != destination_index]
    
    selected_waypoints = []
    if available_waypoints:
        options = [place_names[i] for i in available_waypoints]
        indices = [i for i in available_waypoints]
        selected = st.multiselect("Select Waypoints:", options=options)
        
        # Convert selected names to indices
        selected_waypoints = [indices[options.index(name)] for name in selected if name in options]
    
    # Route options
    st.subheader("Route Options")
    travel_mode = st.radio("Travel Mode:", 
                          ["driving", "walking", "transit", "bicycling"],
                          horizontal=True)
    
    # Calculate route
    if st.button("Calculate Route"):
        if origin_index == destination_index:
            st.error("Origin and destination cannot be the same.")
        else:
            with st.spinner("Calculating route..."):
                # Get places for origin, destination, and waypoints
                origin = st.session_state.geocoded_places[origin_index]
                destination = st.session_state.geocoded_places[destination_index]
                
                waypoints = []
                if selected_waypoints:
                    waypoints = [st.session_state.geocoded_places[i] for i in selected_waypoints]
                
                # Get route
                route_data = get_route(origin, destination, waypoints, travel_mode)
                
                if route_data:
                    st.session_state.route_data = route_data
                    
                    # Store selected places for highlighting on the map
                    selected_indices = [origin_index, destination_index] + selected_waypoints
                    st.session_state.selected_places = [place_names[i] for i in selected_indices]
                    
                    # Show route information
                    st.subheader("Route Information")
                    st.write(f"**Distance:** {route_data['distance']}")
                    st.write(f"**Duration:** {route_data['duration']}")
                    st.write(f"**From:** {route_data['start_address']}")
                    st.write(f"**To:** {route_data['end_address']}")
                    
                    # Show directions
                    with st.expander("Step-by-Step Directions"):
                        for i, step in enumerate(route_data['steps']):
                            st.markdown(f"**Step {i+1}:** {step['instruction']} ({step['distance']}, {step['duration']})")
                    
                    # Create a new map with the route
                    st.subheader("Route Map")
                    m = create_folium_map(st.session_state.geocoded_places, 
                                         st.session_state.selected_places,
                                         st.session_state.route_data)
                    folium_static(m)
                else:
                    st.error("Failed to calculate route. Please try different places or travel mode.")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Story2Map",
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main() 