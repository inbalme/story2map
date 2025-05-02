import streamlit as st
import os
import io
import json
import tempfile
import logging
import pandas as pd
from PIL import Image
from typing import List, Dict, Any
from streamlit_folium import folium_static
from dotenv import load_dotenv

# Import utility modules
from utils.text_extractor import TextExtractor
from utils.location_extractor import LocationExtractor
from utils.map_generator import MapGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("story2map.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="Story2Map - Extract Places from Text",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'locations' not in st.session_state:
    st.session_state.locations = []
if 'current_map_name' not in st.session_state:
    st.session_state.current_map_name = None
if 'map_generator' not in st.session_state:
    st.session_state.map_generator = MapGenerator()
if 'location_extractor' not in st.session_state:
    st.session_state.location_extractor = LocationExtractor()

def get_unique_tags(locations: List[Dict]) -> List[str]:
    """Get a unique list of all tags from the locations."""
    tags = set()
    for loc in locations:
        if 'tags' in loc and loc['tags']:
            for tag in loc['tags']:
                tags.add(tag.lower())
    return sorted(list(tags))

def filter_locations_by_tags(locations: List[Dict], selected_tags: List[str]) -> List[Dict]:
    """Filter locations to only those with at least one of the selected tags."""
    if not selected_tags:
        return locations
        
    filtered = []
    for loc in locations:
        if 'tags' in loc and loc['tags']:
            if any(tag.lower() in [t.lower() for t in selected_tags] for tag in loc['tags']):
                filtered.append(loc)
    return filtered

def main():
    """Main function to run the Streamlit app."""
    
    # Title
    st.title("🗺️ Story2Map")
    st.markdown("Extract locations from text and visualize them on a map.")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        
        # Map type selection
        map_type = st.radio(
            "Map Type",
            ["Folium", "Google Maps"],
            index=0
        )
        
        # Google Maps API key input if Google Maps selected
        google_maps_api_key = None
        if map_type == "Google Maps":
            google_maps_api_key = st.text_input(
                "Google Maps API Key",
                value=os.environ.get("GOOGLE_MAPS_API_KEY", ""),
                type="password"
            )
            if not google_maps_api_key:
                st.warning("Please enter a Google Maps API key to use Google Maps.")
        
        # Gemini API key input
        gemini_api_key = st.text_input(
            "Gemini API Key",
            value=os.environ.get("GEMINI_API_KEY", ""),
            type="password",
            help="Required for extracting locations from text"
        )
        
        # Update Gemini API key if changed
        if gemini_api_key and gemini_api_key != getattr(st.session_state.location_extractor, 'api_key', ''):
            st.session_state.location_extractor = LocationExtractor(api_key=gemini_api_key)
        
        # Update map generator if needed
        if (map_type == "Google Maps" and google_maps_api_key and 
            (st.session_state.map_generator.map_type != "google" or 
             st.session_state.map_generator.google_maps_api_key != google_maps_api_key)):
            st.session_state.map_generator = MapGenerator(
                map_type="google", 
                google_maps_api_key=google_maps_api_key
            )
        elif map_type == "Folium" and st.session_state.map_generator.map_type != "folium":
            st.session_state.map_generator = MapGenerator(map_type="folium")
        
        # Saved maps dropdown
        st.header("Saved Maps")
        saved_maps = st.session_state.map_generator.get_saved_maps()
        
        if saved_maps:
            selected_map = st.selectbox(
                "Load a saved map",
                [""] + saved_maps,
                index=0
            )
            
            if selected_map and st.button("Load Selected Map"):
                locations = st.session_state.map_generator.load_map(selected_map)
                if locations:
                    st.session_state.locations = locations
                    st.session_state.current_map_name = selected_map
                    st.success(f"Loaded map: {selected_map}")
                    st.rerun()
        else:
            st.info("No saved maps found.")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Extract Locations from Text")
        
        # Input tabs
        input_tab = st.tabs(["Clipboard Text", "Upload Image", "URL"])
        
        with input_tab[0]:  # Clipboard Text
            text_input = st.text_area(
                "Paste text from clipboard",
                height=300,
                placeholder="Paste your text here..."
            )
            
            if st.button("Extract from Text"):
                if not text_input:
                    st.error("Please paste some text.")
                elif not gemini_api_key:
                    st.error("Please enter a Gemini API key in the sidebar.")
                else:
                    with st.spinner("Extracting locations from text..."):
                        extracted_locations = st.session_state.location_extractor.extract_locations(text_input)
                        
                        if extracted_locations:
                            # If we already have a map loaded, ask what to do
                            if st.session_state.locations and st.session_state.current_map_name:
                                action = st.radio(
                                    "What would you like to do with these locations?",
                                    ["Add to current map", "Create a new map"]
                                )
                                
                                if action == "Add to current map":
                                    st.session_state.locations.extend(extracted_locations)
                                    st.success(f"Added {len(extracted_locations)} locations to current map.")
                                else:
                                    st.session_state.locations = extracted_locations
                                    st.session_state.current_map_name = None
                                    st.success(f"Created new map with {len(extracted_locations)} locations.")
                            else:
                                st.session_state.locations = extracted_locations
                                st.success(f"Extracted {len(extracted_locations)} locations.")
                            
                            st.rerun()
                        else:
                            st.warning("No locations found in the text.")
        
        with input_tab[1]:  # Upload Image
            uploaded_file = st.file_uploader(
                "Upload an image",
                type=["png", "jpg", "jpeg"]
            )
            
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)
                
                if st.button("Extract from Image"):
                    if not gemini_api_key:
                        st.error("Please enter a Gemini API key in the sidebar.")
                    else:
                        with st.spinner("Extracting text and locations from image..."):
                            # Extract text from image
                            text = TextExtractor.from_image(uploaded_file)
                            
                            if not text:
                                st.error("Could not extract text from the image.")
                            else:
                                st.write(f"Extracted {len(text)} characters from image")
                                
                                # Extract locations from the text
                                extracted_locations = st.session_state.location_extractor.extract_locations(text)
                                
                                if extracted_locations:
                                    # If we already have a map loaded, ask what to do
                                    if st.session_state.locations and st.session_state.current_map_name:
                                        action = st.radio(
                                            "What would you like to do with these locations?",
                                            ["Add to current map", "Create a new map"]
                                        )
                                        
                                        if action == "Add to current map":
                                            st.session_state.locations.extend(extracted_locations)
                                            st.success(f"Added {len(extracted_locations)} locations to current map.")
                                        else:
                                            st.session_state.locations = extracted_locations
                                            st.session_state.current_map_name = None
                                            st.success(f"Created new map with {len(extracted_locations)} locations.")
                                    else:
                                        st.session_state.locations = extracted_locations
                                        st.success(f"Extracted {len(extracted_locations)} locations.")
                                    
                                    st.rerun()
                                else:
                                    st.warning("No locations found in the text extracted from the image.")
        
        with input_tab[2]:  # URL
            url_input = st.text_input(
                "Enter a URL",
                placeholder="https://example.com/article"
            )
            
            if st.button("Extract from URL"):
                if not url_input:
                    st.error("Please enter a URL.")
                elif not gemini_api_key:
                    st.error("Please enter a Gemini API key in the sidebar.")
                else:
                    with st.spinner("Extracting text and locations from URL..."):
                        # Extract text from URL
                        text = TextExtractor.from_url(url_input)
                        
                        if not text:
                            st.error("Could not extract text from the URL.")
                        else:
                            st.write(f"Extracted {len(text)} characters from URL")
                            
                            # Extract locations from the text
                            extracted_locations = st.session_state.location_extractor.extract_locations(text)
                            
                            if extracted_locations:
                                # If we already have a map loaded, ask what to do
                                if st.session_state.locations and st.session_state.current_map_name:
                                    action = st.radio(
                                        "What would you like to do with these locations?",
                                        ["Add to current map", "Create a new map"]
                                    )
                                    
                                    if action == "Add to current map":
                                        st.session_state.locations.extend(extracted_locations)
                                        st.success(f"Added {len(extracted_locations)} locations to current map.")
                                    else:
                                        st.session_state.locations = extracted_locations
                                        st.session_state.current_map_name = None
                                        st.success(f"Created new map with {len(extracted_locations)} locations.")
                                else:
                                    st.session_state.locations = extracted_locations
                                    st.success(f"Extracted {len(extracted_locations)} locations.")
                                
                                st.rerun()
                            else:
                                st.warning("No locations found in the text from the URL.")
        
        # Display locations in a table if available
        if st.session_state.locations:
            st.header(f"Extracted Locations ({len(st.session_state.locations)})")
            
            # Create a DataFrame from the locations
            df = pd.DataFrame([
                {
                    "Name": loc.get("name", ""),
                    "Latitude": loc.get("latitude", ""),
                    "Longitude": loc.get("longitude", ""),
                    "Tags": ", ".join(loc.get("tags", [])),
                    "Description": loc.get("description", "")
                }
                for loc in st.session_state.locations
            ])
            
            st.dataframe(df, use_container_width=True)
    
    with col2:
        st.header("Map Visualization")
        
        if st.session_state.locations:
            # Get unique tags for filtering
            unique_tags = get_unique_tags(st.session_state.locations)
            
            # Tag filter if there are tags
            selected_tags = []
            if unique_tags:
                selected_tags = st.multiselect(
                    "Filter by tags",
                    unique_tags
                )
            
            # Filter locations by selected tags
            filtered_locations = filter_locations_by_tags(
                st.session_state.locations, 
                selected_tags
            )
            
            # Map save options
            map_name = st.text_input(
                "Map Name",
                value=st.session_state.current_map_name or "",
                placeholder="Enter a name for your map"
            )
            
            save_col, view_col = st.columns(2)
            
            with save_col:
                if st.button("Save Map"):
                    if not map_name:
                        st.error("Please enter a map name.")
                    else:
                        with st.spinner("Saving map..."):
                            path = st.session_state.map_generator.create_map(
                                filtered_locations, 
                                map_name
                            )
                            
                            if path:
                                st.session_state.current_map_name = map_name
                                st.success(f"Map saved as {map_name}")
                                
                                # If Google Maps, display shareable link
                                if st.session_state.map_generator.map_type == "google":
                                    shareable_url = st.session_state.map_generator.get_shareable_url(map_name)
                                    if shareable_url:
                                        st.markdown(f"[Open in Google Maps]({shareable_url})")
                            else:
                                st.error("Failed to save map.")
            
            # Always display the current map 
            if filtered_locations:
                if st.session_state.map_generator.map_type == "folium":
                    # Create a folium map for display
                    import folium
                    from folium.plugins import MarkerCluster
                    
                    # Calculate center of map
                    lats = [loc.get('latitude', 0) for loc in filtered_locations if loc.get('latitude')]
                    lngs = [loc.get('longitude', 0) for loc in filtered_locations if loc.get('longitude')]
                    
                    if lats and lngs:
                        center = [sum(lats) / len(lats), sum(lngs) / len(lngs)]
                        
                        # Determine zoom level based on the spread of locations
                        lat_range = max(lats) - min(lats)
                        lng_range = max(lngs) - min(lngs)
                        max_range = max(lat_range, lng_range)
                        
                        if max_range > 20:
                            zoom = 4
                        elif max_range > 10:
                            zoom = 6
                        elif max_range > 5:
                            zoom = 8
                        elif max_range > 1:
                            zoom = 10
                        else:
                            zoom = 12
                    else:
                        center = [0, 0]
                        zoom = 2
                    
                    m = folium.Map(location=center, zoom_start=zoom)
                    
                    # Add marker cluster
                    marker_cluster = MarkerCluster().add_to(m)
                    
                    # Color map for different tags
                    tag_colors = st.session_state.map_generator.tag_colors
                    
                    # Add markers for each location
                    for loc in filtered_locations:
                        if 'latitude' in loc and 'longitude' in loc:
                            # Get color based on first tag
                            color = "blue"  # Default color
                            if 'tags' in loc and loc['tags']:
                                primary_tag = loc['tags'][0].lower()
                                color = tag_colors.get(primary_tag, "blue")
                            
                            # Create popup with location info
                            popup_html = f"<b>{loc['name']}</b><br>"
                            
                            if 'description' in loc and loc['description']:
                                popup_html += f"{loc['description']}<br>"
                            
                            if 'tags' in loc and loc['tags']:
                                popup_html += f"Tags: {', '.join(loc['tags'])}<br>"
                            
                            # Add marker to cluster
                            folium.Marker(
                                location=[loc['latitude'], loc['longitude']],
                                popup=folium.Popup(popup_html, max_width=300),
                                icon=folium.Icon(color=color, icon="info-sign"),
                            ).add_to(marker_cluster)
                    
                    # Display the folium map
                    folium_static(m, width=700, height=500)
                else:
                    # Create a temporary HTML file for Google Maps
                    if google_maps_api_key:
                        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
                            html_content = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <title>Map Preview</title>
                                <meta charset="utf-8">
                                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                <style>
                                    #map {{
                                        height: 100%;
                                        width: 100%;
                                        position: absolute;
                                        top: 0;
                                        left: 0;
                                    }}
                                    html, body {{
                                        height: 100%;
                                        margin: 0;
                                        padding: 0;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div id="map"></div>
                                <script>
                                    function initMap() {{
                                        const locations = {json.dumps(filtered_locations)};
                                        
                                        // Default center if no locations
                                        let center = {{ lat: 0, lng: 0 }};
                                        let zoom = 2;
                                        
                                        if (locations.length > 0) {{
                                            // Calculate center
                                            const lats = locations.map(loc => loc.latitude).filter(Boolean);
                                            const lngs = locations.map(loc => loc.longitude).filter(Boolean);
                                            
                                            if (lats.length > 0 && lngs.length > 0) {{
                                                const avgLat = lats.reduce((a, b) => a + b, 0) / lats.length;
                                                const avgLng = lngs.reduce((a, b) => a + b, 0) / lngs.length;
                                                center = {{ lat: avgLat, lng: avgLng }};
                                                
                                                // Determine zoom level
                                                const latRange = Math.max(...lats) - Math.min(...lats);
                                                const lngRange = Math.max(...lngs) - Math.min(...lngs);
                                                const maxRange = Math.max(latRange, lngRange);
                                                
                                                if (maxRange > 20) zoom = 4;
                                                else if (maxRange > 10) zoom = 6;
                                                else if (maxRange > 5) zoom = 8;
                                                else if (maxRange > 1) zoom = 10;
                                                else zoom = 12;
                                            }}
                                        }}
                                        
                                        const map = new google.maps.Map(document.getElementById("map"), {{
                                            zoom: zoom,
                                            center: center,
                                        }});
                                        
                                        // Add markers
                                        locations.forEach(loc => {{
                                            if (loc.latitude && loc.longitude) {{
                                                const marker = new google.maps.Marker({{
                                                    position: {{ lat: loc.latitude, lng: loc.longitude }},
                                                    map: map,
                                                    title: loc.name
                                                }});
                                                
                                                // Create info window
                                                let content = `<div><h3>${{loc.name}}</h3>`;
                                                if (loc.description) content += `<p>${{loc.description}}</p>`;
                                                if (loc.tags && loc.tags.length) content += `<p>Tags: ${{loc.tags.join(', ')}}</p>`;
                                                content += `</div>`;
                                                
                                                const infowindow = new google.maps.InfoWindow({{
                                                    content: content
                                                }});
                                                
                                                marker.addListener("click", () => {{
                                                    infowindow.open({{
                                                        anchor: marker,
                                                        map,
                                                    }});
                                                }});
                                            }}
                                        }});
                                    }}
                                </script>
                                <script src="https://maps.googleapis.com/maps/api/js?key={google_maps_api_key}&callback=initMap" async defer></script>
                            </body>
                            </html>
                            """
                            f.write(html_content)
                            temp_file = f.name
                        
                        # Display the temporary Google Maps HTML
                        with open(temp_file, 'r') as f:
                            map_html = f.read()
                        st.components.v1.html(map_html, height=500)
                        
                        # Remove the temp file
                        os.unlink(temp_file)
                    else:
                        st.warning("Please enter a Google Maps API key in the sidebar to view the map.")
            else:
                st.info("No locations to display. Extract locations from text or load a saved map.")
        else:
            st.info("No locations to display. Extract locations from text or load a saved map.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Story2Map - Extract and visualize locations from text. "
    )

if __name__ == "__main__":
    main() 