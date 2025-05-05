import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import os
from math import isnan

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
        
        # Try to extract coordinates in DMS format with seconds like "54° 16' 25" N, 5° 40' 36" W"
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



def load_data():
    """Load and process the treasure data from Excel."""
    # file_path = os.path.join("./", "treasure.xlsx")
    # Get the directory where the current script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Join with the filename to create an absolute path
    file_path = os.path.join(current_dir, "treasure.xlsx")
    # # URL to the raw content of the Excel file on GitHub
    # github_url = "https://github.com/ly2xxx/treasure/raw/main/treasure.xlsx"
    
    try:
        
        
        # Read all sheets from the Excel file
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        # Create an empty DataFrame to store combined data
        combined_df = pd.DataFrame()
        
        # Process each sheet
        for sheet_name in sheet_names:
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
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

        # Create two layers with enhanced interaction
        all_points_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df[df[id_column] != st.session_state.selected_treasure] if st.session_state.selected_treasure else df,
            get_position=["longitude", "latitude"],
            get_color=[255, 165, 0, 200],
            get_radius="radius",
            pickable=True,
            auto_highlight=True,
            highlight_color=[255, 200, 0, 255]  # Brighter highlight on hover
        )

        selected_layers = []
        if st.session_state.selected_treasure:
            selected_point = df[df[id_column] == st.session_state.selected_treasure]
            selected_layer = pdk.Layer(
                "ScatterplotLayer",
                data=selected_point,
                get_position=["longitude", "latitude"],
                get_color=[30, 144, 255, 230],
                get_radius="radius",
                pickable=True,
                auto_highlight=True,
                highlight_color=[100, 200, 255, 255]  # Brighter highlight on hover
            )
            selected_layers = [selected_layer]

        # Render the map
        map_chart = pdk.Deck(
            layers=[all_points_layer] + selected_layers,
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/satellite-v9",
            tooltip=tooltip,
            height=600
        )

        # Show the map and handle clicks through a container
        map_container = st.pydeck_chart(map_chart)
        
        # Add easy-to-understand instructions
        st.caption("Click on any marker to select it, or use the dropdown menu on the right. Use mouse wheel to zoom in/out.")
        
        # If the container was clicked, update the selection
        if map_container:
            # The map was interacted with - update the selection if needed
            new_selection = st.session_state.get('treasure_selector')
            if new_selection != st.session_state.selected_treasure:
                st.session_state.selected_treasure = new_selection
                # Update map center and zoom
                if new_selection:
                    treasure_data = df[df[id_column] == new_selection].iloc[0]
                    st.session_state.map_center = (treasure_data["latitude"], treasure_data["longitude"])
                    st.session_state.zoom_level = 8
                    st.experimental_rerun()
    
    with col2:
        # Display treasure details
        st.subheader("Treasure Details")
        
        # Allow user to select a specific treasure
        id_column = "Location" if "Location" in df.columns else df.columns[0]
        
        # Function to update map when selection changes
        def on_treasure_select():
            selected = st.session_state.treasure_selector
            if selected:
                treasure_data = df[df[id_column] == selected].iloc[0]
                st.session_state.selected_treasure = selected
                st.session_state.map_center = (treasure_data["latitude"], treasure_data["longitude"])
                st.session_state.zoom_level = 8  # Zoom level when focused on a location
        
        # Create the selectbox with the callback
        selected_treasure = st.selectbox(
            "Select a treasure location:",
            options=df[id_column].tolist(),
            key="treasure_selector",
            on_change=on_treasure_select
        )
        
        # Display details for the selected treasure
        if selected_treasure:
            treasure_data = df[df[id_column] == selected_treasure].iloc[0]
            
            st.markdown(f"### {selected_treasure}")
            
            # Display all available fields
            for column in df.columns:
                if column not in ["latitude", "longitude", "radius", id_column] and not pd.isna(treasure_data[column]):
                    st.markdown(f"**{column}:** {treasure_data[column]}")

    # Display the full dataset as a table (expandable)
    with st.expander("View All Data"):
        st.dataframe(df.drop(columns=["latitude", "longitude", "radius"]))

if __name__ == "__main__":
    main()