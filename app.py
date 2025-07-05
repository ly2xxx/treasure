import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import os
from math import isnan
import json


# Configuration for point sizes based on likelihood
LIKELIHOOD_RADIUS_CONFIG = {
    "high": 10000,    # For likelihood >= 80%
    "medium": 7000,   # For likelihood between 60% and 80%
    "low": 4000       # For likelihood < 60%
}

# Set page title and configuration
st.set_page_config(
    page_title="Treasure Map Explorer",
    page_icon="🗺️",
    layout="wide"
)

def parse_coordinates(coord_str):
    """Parse coordinates from various string formats to latitude and longitude."""
    if pd.isna(coord_str) or coord_str == "":
        return None, None
    
    # Convert to string if not already
    coord_str = str(coord_str)
    
    try:
        # Try to extract coordinates in format like "12.345, -67.890"
        pattern = r"(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)"
        match = re.search(pattern, coord_str)
        
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            # Basic validation for lat/lon ranges
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
            else:
                # If values are swapped, try to correct them
                if -90 <= lon <= 90 and -180 <= lat <= 180:
                    return lon, lat
        
        # Try to extract coordinates in DMS format like "53°21'N, 4°14'W"
        dms_pattern = r"(\d+)°(\d+)'([NS])[,\s]+(\d+)°(\d+)'([EW])"
        dms_match = re.search(dms_pattern, coord_str)
        
        if dms_match:
            lat_deg = int(dms_match.group(1))
            lat_min = int(dms_match.group(2))
            lat_dir = dms_match.group(3)
            
            lon_deg = int(dms_match.group(4))
            lon_min = int(dms_match.group(5))
            lon_dir = dms_match.group(6)
            
            # Convert to decimal degrees
            lat = lat_deg + (lat_min / 60)
            if lat_dir == 'S':
                lat = -lat
                
            lon = lon_deg + (lon_min / 60)
            if lon_dir == 'W':
                lon = -lon
                
            return lat, lon
        
        # Try to extract coordinates in decimal degrees with direction like "55.2415° N, 6.5167° W"
        decimal_dir_pattern = r"(\d+\.?\d*)°\s*([NS])[,\s]+(\d+\.?\d*)°\s*([EW])"
        decimal_dir_match = re.search(decimal_dir_pattern, coord_str)
        
        if decimal_dir_match:
            lat = float(decimal_dir_match.group(1))
            lat_dir = decimal_dir_match.group(2)
            lon = float(decimal_dir_match.group(3))
            lon_dir = decimal_dir_match.group(4)
            
            if lat_dir == 'S':
                lat = -lat
            if lon_dir == 'W':
                lon = -lon
                
            return lat, lon
        
        # Try to extract coordinates in DMS format with seconds like "54° 16' 25\" N, 5° 40' 36\" W"
        dms_sec_pattern = r"(\d+)°\s*(\d+)'\s*(\d+)\"?\s*([NS])[,\s]+(\d+)°\s*(\d+)'\s*(\d+)\"?\s*([EW])"
        dms_sec_match = re.search(dms_sec_pattern, coord_str)
        
        if dms_sec_match:
            lat_deg = int(dms_sec_match.group(1))
            lat_min = int(dms_sec_match.group(2))
            lat_sec = int(dms_sec_match.group(3))
            lat_dir = dms_sec_match.group(4)
            
            lon_deg = int(dms_sec_match.group(5))
            lon_min = int(dms_sec_match.group(6))
            lon_sec = int(dms_sec_match.group(7))
            lon_dir = dms_sec_match.group(8)
            
            # Convert to decimal degrees
            lat = lat_deg + (lat_min / 60) + (lat_sec / 3600)
            if lat_dir == 'S':
                lat = -lat
                
            lon = lon_deg + (lon_min / 60) + (lon_sec / 3600)
            if lon_dir == 'W':
                lon = -lon
                
            return lat, lon
        
        # Try to extract coordinates in format like "54.32° N, 5.72° W"
        simple_decimal_pattern = r"(\d+\.\d+)°\s*([NS])[,\s]+(\d+\.\d+)°\s*([EW])"
        simple_decimal_match = re.search(simple_decimal_pattern, coord_str)
        
        if simple_decimal_match:
            lat = float(simple_decimal_match.group(1))
            lat_dir = simple_decimal_match.group(2)
            lon = float(simple_decimal_match.group(3))
            lon_dir = simple_decimal_match.group(4)
            
            if lat_dir == 'S':
                lat = -lat
            if lon_dir == 'W':
                lon = -lon
                
            return lat, lon
        
    except (ValueError, IndexError):
        pass
    
    return None, None


def format_location_with_area(location, area):
    """Format location name with area in brackets."""
    if pd.isna(area) or area == "":
        return location
    return f"{location} ({area})"


def extract_location_from_display(display_text):
    """Extract the original location name from the display text with area."""
    if pd.isna(display_text) or display_text == "" or display_text == "Choose a location...":
        return None
    
    # Extract location name from format "Location (Area)"
    if " (" in display_text and display_text.endswith(")"):
        return display_text.split(" (")[0]
    return display_text


def load_data():
    """Load and process the treasure data from Excel and JSON files."""
    # Get the directory where the current script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize an empty DataFrame to store combined data
    combined_df = pd.DataFrame()
    
    try:
        # Load and process Excel data
        excel_path = os.path.join(current_dir, "treasure.xlsx")
        excel_file = pd.ExcelFile(excel_path)
        sheet_names = excel_file.sheet_names
        
        # Process each sheet from Excel
        for sheet_name in sheet_names:
            # Read the sheet
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            # Add the sheet name as "Area"
            df["Area"] = sheet_name
            
            # Process coordinates
            coords = []
            for coord_str in df["Coordinates (Approximate)"]:
                lat, lon = parse_coordinates(coord_str)
                coords.append((lat, lon))
            
            df["latitude"], df["longitude"] = zip(*coords)
            
            # Calculate radius based on likelihood
            df["radius"] = df["Likelihood (%)"].apply(
                lambda x: LIKELIHOOD_RADIUS_CONFIG["high"] if pd.notna(x) and (
                            (isinstance(x, str) and float(x.strip('%')) >= 80) or 
                            (isinstance(x, (int, float)) and x >= 0.8)
                        ) else (
                        LIKELIHOOD_RADIUS_CONFIG["medium"] if pd.notna(x) and (
                            (isinstance(x, str) and float(x.strip('%')) >= 60) or
                            (isinstance(x, (int, float)) and x >= 0.6)
                        ) else LIKELIHOOD_RADIUS_CONFIG["low"])
            )
            
            # Filter out rows with invalid coordinates
            df = df.dropna(subset=["latitude", "longitude"])
            
            # Append to the combined DataFrame
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        
        # Load and process JSON data from all files in raw directory
        raw_dir = os.path.join(current_dir, "raw")
        if os.path.exists(raw_dir):
            # List all JSON files in raw directory
            json_files = [f for f in os.listdir(raw_dir) if f.endswith('.json')]
            
            for json_file in json_files:
                json_path = os.path.join(raw_dir, json_file)
                try:
                    # Read JSON data
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)  # Use json.load instead of pd.read_json

                    # Check the format and extract data accordingly
                    if isinstance(json_data, dict) and 'tables' in json_data:
                        # Format 1: Italy.json style with tables.data structure
                        json_df = pd.DataFrame(json_data['tables'][0]['data'])
                    else:
                        # Format 2: Spain.json style with direct array
                        json_df = pd.read_json(json_path)

                    
                    # Add Area column based on JSON filename (without .json extension)
                    area_name = os.path.splitext(json_file)[0]
                    json_df["Area"] = area_name
                    
                    # Process coordinates from JSON
                    coords = []
                    for coord_str in json_df["Coordinates (Approximate)"]:
                        lat, lon = parse_coordinates(coord_str)
                        coords.append((lat, lon))
                    
                    json_df["latitude"], json_df["longitude"] = zip(*coords)
                    
                    # Calculate radius based on likelihood for JSON data
                    json_df["radius"] = json_df["Likelihood (%)"].apply(
                        lambda x: LIKELIHOOD_RADIUS_CONFIG["high"] if pd.notna(x) and (
                            (isinstance(x, str) and float(x.strip('%')) >= 80) or 
                            (isinstance(x, (int, float)) and x >= 80)
                        ) else (
                            LIKELIHOOD_RADIUS_CONFIG["medium"] if pd.notna(x) and (
                                (isinstance(x, str) and float(x.strip('%')) >= 60) or
                                (isinstance(x, (int, float)) and x >= 60)
                            ) else LIKELIHOOD_RADIUS_CONFIG["low"]
                        )
                    )
                    
                    # Filter out rows with invalid coordinates
                    json_df = json_df.dropna(subset=["latitude", "longitude"])
                    
                    # Append JSON data to combined DataFrame
                    combined_df = pd.concat([combined_df, json_df], ignore_index=True)
                except Exception as e:
                    st.warning(f"Error processing {json_file}: {e}")

        
        return combined_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def main():
    st.title("🗺️ Treasure Map Explorer")
    
    # Load data
    df = load_data()
    
    if df.empty:
        st.warning("No valid coordinate data found. Please check your Excel file.")
        return
    
    # Initialize session state for tracking selected treasure and map position
    if 'selected_treasure' not in st.session_state:
        st.session_state.selected_treasure = None
    if 'map_center' not in st.session_state:
        st.session_state.map_center = (df["latitude"].mean(), df["longitude"].mean())
        st.session_state.zoom_level = 2
    if 'map_click_location' not in st.session_state:
        st.session_state.map_click_location = None

    # Create two columns for layout
    col1, col2 = st.columns([7, 3])
    
    with col1:
        # Create map view
        st.subheader("Treasure Locations")
        
        # Get map center (average of all coordinates)
        center_lat = df["latitude"].mean()
        center_lon = df["longitude"].mean()
        
        # Create the view state
        view_state = pdk.ViewState(
            latitude=st.session_state.map_center[0],
            longitude=st.session_state.map_center[1],
            zoom=st.session_state.zoom_level,
            pitch=0
        )
        
        # Create tooltip for hover information
        id_column = "Location" if "Location" in df.columns else df.columns[0]
        tooltip = {
            "html": f"<b>{{{id_column}}}</b><br/>{{Coordinates (Approximate)}}<br/>Click to select",
            "style": {
                "backgroundColor": "steelblue",
                "color": "white",
                "cursor": "pointer"
            }
        }

        # Create a single layer with all points
        # Add color based on selection
        def get_color(row):
            if row[id_column] == st.session_state.selected_treasure:
                return [30, 144, 255, 230]  # Blue for selected
            else:
                return [255, 165, 0, 200]   # Orange for unselected
        
        df_display = df.copy()
        df_display['color'] = df_display.apply(get_color, axis=1)
        
        # Create the layer
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_display,
            get_position=["longitude", "latitude"],
            get_color="color",
            get_radius="radius",
            pickable=True,
            auto_highlight=True,
            highlight_color=[255, 255, 0, 255]
        )

        # Render the map with selection handling
        map_chart = pdk.Deck(
            layers=[scatter_layer],
            initial_view_state=view_state,
            # map_style="mapbox://styles/mapbox/satellite-v9",
            map_style='road',
            tooltip=tooltip,
            height=600
        )

        # Display the map
        st.pydeck_chart(map_chart, use_container_width=True)
        
        # Add dynamic quick select buttons based on current map view with wider layout
        st.write("**Quick Select Nearby Locations:**")
        
        # Calculate distances from current map center to find nearby locations
        import math
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            """Calculate the great circle distance between two points on Earth"""
            R = 6371  # Earth's radius in kilometers
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = (math.sin(dlat/2)**2 + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dlon/2)**2)
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        
        # Calculate distances from current map center
        current_center_lat, current_center_lon = st.session_state.map_center
        df_with_distance = df.copy()
        df_with_distance['distance_from_center'] = df_with_distance.apply(
            lambda row: haversine_distance(
                current_center_lat, current_center_lon,
                row['latitude'], row['longitude']
            ), axis=1
        )
        
        # Get the closest locations (adjust number based on zoom level)
        if st.session_state.zoom_level >= 6:
            # When zoomed in, show more nearby locations
            num_buttons = min(6, len(df))
        else:
            # When zoomed out, show fewer but more spread out locations
            num_buttons = min(4, len(df))
        
        # Sort by distance and get the closest ones
        nearby_locations = df_with_distance.nsmallest(num_buttons, 'distance_from_center')
        
        # Create buttons in rows of 2 for wider buttons to accommodate area names
        rows = (num_buttons + 1) // 2  # Ceiling division for 2 columns
        for row_idx in range(rows):
            cols = st.columns(2)
            start_idx = row_idx * 2
            end_idx = min(start_idx + 2, num_buttons)
            
            for col_idx, (idx, row) in enumerate(nearby_locations.iloc[start_idx:end_idx].iterrows()):
                location_name = row[id_column]
                area_name = row["Area"]
                distance = row['distance_from_center']
                
                # Format button text with area and distance info
                if distance < 1:
                    distance_text = f"{distance*1000:.0f}m"
                else:
                    distance_text = f"{distance:.1f}km"
                
                # Create more descriptive button text with area
                button_text = f"📍 {location_name}"
                if not pd.isna(area_name) and area_name != "":
                    button_text += f" ({area_name})"
                
                if st.session_state.zoom_level >= 6:  # Show distance when zoomed in
                    button_text += f" - {distance_text}"
                
                if cols[col_idx].button(button_text, key=f"btn_nearby_{idx}", use_container_width=True):
                    # Update selection - store the location name without area formatting for compatibility
                    st.session_state.treasure_selector = format_location_with_area(location_name, area_name)
                    st.session_state.selected_treasure = location_name
                    
                    # Update map center and zoom
                    st.session_state.map_center = (row["latitude"], row["longitude"])
                    st.session_state.zoom_level = 8
                    st.rerun()
        
        # Add instructions
        zoom_instruction = "zoomed in view" if st.session_state.zoom_level >= 6 else "current view"
        st.caption(f"Quick select buttons show locations nearest to your {zoom_instruction} with area information. Use the dropdown menu on the right for full selection.")

    
    with col2:
        # Display treasure details
        st.subheader("Treasure Details")
        
        # Allow user to select a specific treasure
        id_column = "Location" if "Location" in df.columns else df.columns[0]
        
        # Create options with area in brackets for the dropdown
        dropdown_options = [None]
        for _, row in df.iterrows():
            location_with_area = format_location_with_area(row[id_column], row["Area"])
            dropdown_options.append(location_with_area)
        
        # Function to update map when selection changes
        def on_treasure_select():
            selected_display = st.session_state.treasure_selector
            if selected_display:
                # Extract the actual location name from the display text
                actual_location = extract_location_from_display(selected_display)
                if actual_location:
                    treasure_data = df[df[id_column] == actual_location].iloc[0]
                    st.session_state.selected_treasure = actual_location
                    st.session_state.map_center = (treasure_data["latitude"], treasure_data["longitude"])
                    st.session_state.zoom_level = 8  # Zoom level when focused on a location
        
        # Create the selectbox with the callback and improved formatting
        selected_treasure_display = st.selectbox(
            "Select a treasure location:",
            options=dropdown_options,
            format_func=lambda x: "Choose a location..." if x is None else x,
            key="treasure_selector",
            on_change=on_treasure_select
        )
        
        # Display details for the selected treasure
        if selected_treasure_display:
            actual_location = extract_location_from_display(selected_treasure_display)
            if actual_location:
                treasure_data = df[df[id_column] == actual_location].iloc[0]
                
                st.markdown(f"### {actual_location}")
                
                # Display all available fields
                excluded_columns = ["latitude", "longitude", "radius", id_column]
                for column in df.columns:
                    if column not in excluded_columns:
                        value = treasure_data[column]
                        # Handle different types of values
                        if isinstance(value, (list, tuple)):
                            # For lists (like Supporting Evidence urls), check if not empty
                            if value:
                                if column.endswith('urls'):
                                    # Display URLs as clickable links
                                    st.markdown(f"**{column}:**")
                                    for url in value:
                                        st.markdown(f"- [{url}]({url})")
                                else:
                                    # Display other lists as bullet points
                                    st.markdown(f"**{column}:**")
                                    for item in value:
                                        st.markdown(f"- {item}")
                        else:
                            # For scalar values, use pd.isna
                            if not pd.isna(value):
                                st.markdown(f"**{column}:** {value}")

    # Display the full dataset as a table (expandable)
    with st.expander("View All Data"):
        st.dataframe(df.drop(columns=["latitude", "longitude", "radius"]))

if __name__ == "__main__":
    main()