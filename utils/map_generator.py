import os
import logging
import json
import folium
from folium.plugins import MarkerCluster
from typing import List, Dict, Any, Optional
import pandas as pd
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MapGenerator:
    """Class to generate maps from location data."""
    
    def __init__(self, map_type: str = "folium", google_maps_api_key: str = None):
        """
        Initialize the MapGenerator.
        
        Args:
            map_type: Type of map to generate ("folium" or "google")
            google_maps_api_key: Google Maps API key (required for "google" map type)
        """
        self.map_type = map_type
        self.google_maps_api_key = google_maps_api_key
        self.data_dir = os.path.join(os.getcwd(), "data")
        
        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Created data directory: {self.data_dir}")
            
        # Color map for different tags
        self.tag_colors = {
            "landmark": "red",
            "accommodation": "blue",
            "eating": "orange",
            "drinking": "purple",
            "snacks": "pink",
            "groceries": "darkgreen",
            "restaurant": "orange",
            "bar": "purple",
            "cafe": "beige",
            "nightlife": "darkpurple",
            "attraction": "darkred",
            "viewpoint": "lightred",
            "concert": "cadetblue",
            "shopping": "lightblue",
            "transportation": "gray",
            "natural": "green",
            "cultural": "darkblue"
        }
    
    def create_map(self, locations: List[Dict[str, Any]], map_name: str) -> str:
        """
        Create a map with the given locations.
        
        Args:
            locations: List of location dictionaries with latitude, longitude, and tags
            map_name: Name of the map to create
            
        Returns:
            Path to the generated map HTML file
        """
        if self.map_type == "folium":
            return self._create_folium_map(locations, map_name)
        elif self.map_type == "google":
            return self._create_google_map(locations, map_name)
        else:
            logger.error(f"Unsupported map type: {self.map_type}")
            return ""
    
    def _create_folium_map(self, locations: List[Dict[str, Any]], map_name: str) -> str:
        """
        Create a Folium map with the given locations.
        
        Args:
            locations: List of location dictionaries
            map_name: Name of the map
            
        Returns:
            Path to the generated map HTML file
        """
        try:
            # Calculate center of map
            if not locations:
                # Default to a central location if no locations
                center = [0, 0]
                zoom = 2
            else:
                lats = [loc.get('latitude', 0) for loc in locations if loc.get('latitude')]
                lngs = [loc.get('longitude', 0) for loc in locations if loc.get('longitude')]
                
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
            
            # Create map
            m = folium.Map(location=center, zoom_start=zoom)
            
            # Add marker cluster
            marker_cluster = MarkerCluster().add_to(m)
            
            # Add markers for each location
            for loc in locations:
                if 'latitude' in loc and 'longitude' in loc:
                    # Get color based on first tag
                    color = "blue"  # Default color
                    if 'tags' in loc and loc['tags']:
                        primary_tag = loc['tags'][0].lower()
                        color = self.tag_colors.get(primary_tag, "blue")
                    
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
            
            # Save map to file
            file_path = os.path.join(self.data_dir, f"{map_name}.html")
            m.save(file_path)
            logger.info(f"Saved Folium map to {file_path}")
            
            # Save the location data alongside the map
            data_path = os.path.join(self.data_dir, f"{map_name}.json")
            with open(data_path, 'w') as f:
                json.dump(locations, f)
                
            return file_path
            
        except Exception as e:
            logger.error(f"Error creating Folium map: {e}")
            return ""
    
    def _create_google_map(self, locations: List[Dict[str, Any]], map_name: str) -> str:
        """
        Create a Google Map with the given locations.
        
        Args:
            locations: List of location dictionaries
            map_name: Name of the map
            
        Returns:
            URL to the Google Map
        """
        if not self.google_maps_api_key:
            logger.error("Google Maps API key is required for Google Maps")
            return ""
            
        try:
            # Create a temp HTML file with Google Maps JavaScript API
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{map_name}</title>
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
                            const locations = {json.dumps(locations)};
                            
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
                    <script src="https://maps.googleapis.com/maps/api/js?key={self.google_maps_api_key}&callback=initMap" async defer></script>
                </body>
                </html>
                """
                f.write(html_content)
                temp_file = f.name
            
            # Copy the temp file to the data directory
            file_path = os.path.join(self.data_dir, f"{map_name}_google.html")
            
            # Read the temp file and write to the target file
            with open(temp_file, 'r') as src, open(file_path, 'w') as dst:
                dst.write(src.read())
            
            # Remove the temp file
            os.unlink(temp_file)
            
            # Save the location data
            data_path = os.path.join(self.data_dir, f"{map_name}.json")
            with open(data_path, 'w') as f:
                json.dump(locations, f)
                
            logger.info(f"Saved Google Map to {file_path}")
            
            # Create a sharable Google Maps link
            # Format: https://www.google.com/maps/dir/?api=1&destination=lat,lng&waypoints=lat,lng|lat,lng
            if locations:
                first_loc = locations[0]
                if 'latitude' in first_loc and 'longitude' in first_loc:
                    destination = f"{first_loc['latitude']},{first_loc['longitude']}"
                    waypoints = "|".join([
                        f"{loc['latitude']},{loc['longitude']}"
                        for loc in locations[1:10]  # Limit to 9 additional waypoints
                        if 'latitude' in loc and 'longitude' in loc
                    ])
                    
                    shareable_url = f"https://www.google.com/maps/dir/?api=1&destination={destination}"
                    if waypoints:
                        shareable_url += f"&waypoints={waypoints}"
                        
                    # Save the URL to a text file
                    url_path = os.path.join(self.data_dir, f"{map_name}_url.txt")
                    with open(url_path, 'w') as f:
                        f.write(shareable_url)
                        
                    logger.info(f"Saved shareable Google Maps URL to {url_path}")
                    
                    return shareable_url
            
            return file_path
                
        except Exception as e:
            logger.error(f"Error creating Google Map: {e}")
            return ""
    
    def get_saved_maps(self) -> List[str]:
        """
        Get a list of saved maps.
        
        Returns:
            List of map names
        """
        try:
            # Look for JSON files in the data directory
            map_files = [
                os.path.splitext(f)[0] for f in os.listdir(self.data_dir)
                if f.endswith('.json')
            ]
            return sorted(map_files)
        except Exception as e:
            logger.error(f"Error getting saved maps: {e}")
            return []
    
    def load_map(self, map_name: str) -> List[Dict[str, Any]]:
        """
        Load the location data for a saved map.
        
        Args:
            map_name: Name of the map to load
            
        Returns:
            List of location dictionaries
        """
        try:
            # Load the JSON data
            data_path = os.path.join(self.data_dir, f"{map_name}.json")
            if not os.path.exists(data_path):
                logger.error(f"Map data file not found: {data_path}")
                return []
                
            with open(data_path, 'r') as f:
                locations = json.load(f)
                
            logger.info(f"Loaded {len(locations)} locations from {data_path}")
            return locations
        except Exception as e:
            logger.error(f"Error loading map {map_name}: {e}")
            return []
    
    def get_map_path(self, map_name: str) -> str:
        """
        Get the path to a saved map.
        
        Args:
            map_name: Name of the map
            
        Returns:
            Path to the map HTML file
        """
        if self.map_type == "folium":
            map_path = os.path.join(self.data_dir, f"{map_name}.html")
        else:
            map_path = os.path.join(self.data_dir, f"{map_name}_google.html")
            
        if not os.path.exists(map_path):
            logger.error(f"Map file not found: {map_path}")
            return ""
            
        return map_path
    
    def get_shareable_url(self, map_name: str) -> str:
        """
        Get the shareable URL for a Google Maps map.
        
        Args:
            map_name: Name of the map
            
        Returns:
            Shareable URL
        """
        url_path = os.path.join(self.data_dir, f"{map_name}_url.txt")
        if not os.path.exists(url_path):
            logger.error(f"URL file not found: {url_path}")
            return ""
            
        with open(url_path, 'r') as f:
            url = f.read().strip()
            
        return url 