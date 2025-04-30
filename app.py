import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import os
from math import isnan

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
    
    # Try to extract coordinates in format like "12.345, -67.890"
    pattern = r"(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)"
    match = re.search(pattern, coord_str)
    
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            # Basic validation for lat/lon ranges
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
            else:
                # If values are swapped, try to correct them
                if -90 <= lon <= 90 and -180 <= lat <= 180:
                    return lon, lat
        except ValueError:
            pass
    
    # Try to extract coordinates in DMS format like "53°21'N, 4°14'W"
    dms_pattern = r"(\d+)°(\d+)'([NS])[,\s]+(\d+)°(\d+)'([EW])"
    dms_match = re.search(dms_pattern, coord_str)
    
    if dms_match:
        try:
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
    
    try:
        df = pd.read_excel(file_path)
        
        # Process coordinates
        coords = []
        for coord_str in df["Coordinates (Approximate)"]:
            lat, lon = parse_coordinates(coord_str)
            coords.append((lat, lon))
        
        df["latitude"], df["longitude"] = zip(*coords)
        
        # Filter out rows with invalid coordinates
        df = df.dropna(subset=["latitude", "longitude"])
        
        return df
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
    
    # Create two columns for layout
    col1, col2 = st.columns([7, 3])
    
    with col1:
        # Create map view
        st.subheader("Treasure Locations")
        
        # Get map center (average of all coordinates)
        center_lat = df["latitude"].mean()
        center_lon = df["longitude"].mean()
        
        # Create tooltip for hover information
        id_column = "Location" if "Location" in df.columns else df.columns[0]
        tooltip = {
            "html": f"<b>{{{id_column}}}</b><br/>{{Coordinates (Approximate)}}",
            "style": {
                "backgroundColor": "steelblue",
                "color": "white"
            }
        }

        
        # Create the map with markers
        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=2,
            pitch=0
        )
        
        # # Create a layer with all points
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position=["longitude", "latitude"],
            get_color=[255, 165, 0, 200],  # Orange with some transparency
            get_radius=10000,  # Size of the points
            pickable=True,
            auto_highlight=True
        )

        # # Create a layer with flag icons instead of points
        # layer = pdk.Layer(
        #     "IconLayer",
        #     data=df,
        #     get_position=["longitude", "latitude"],
        #     get_icon={
        #         "url": "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0/svgs/solid/flag.svg",
        #         "width": 128,
        #         "height": 128,
        #         "anchorY": 128
        #     },
        #     get_size=8,
        #     get_color=[255, 0, 0],  # Orange color for the flags
        #     pickable=True,
        #     auto_highlight=True,
        #     size_scale=15,
        #     size_min_pixels=150,
        #     size_max_pixels=400
        # )


        
        # Render the map
        map_chart = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/satellite-v9",
            tooltip=tooltip
        )
        
        st.pydeck_chart(map_chart)
        
        st.caption("Click on a marker to see details. Use mouse wheel to zoom in/out.")
    
    with col2:
        # Display treasure details
        st.subheader("Treasure Details")
        
        # Check if "Location" column exists, otherwise use the first column as identifier
        id_column = "Location" if "Location" in df.columns else df.columns[0]
        
        # Allow user to select a specific treasure
        selected_treasure = st.selectbox(
            "Select a treasure location:",
            options=df[id_column].tolist()
        )
        
        # Display details for the selected treasure
        if selected_treasure:
            treasure_data = df[df[id_column] == selected_treasure].iloc[0]
            
            st.markdown(f"### {selected_treasure}")
            
            # Display all available fields
            for column in df.columns:
                if column not in ["latitude", "longitude", id_column] and not pd.isna(treasure_data[column]):
                    st.markdown(f"**{column}:** {treasure_data[column]}")

    # Display the full dataset as a table (expandable)
    with st.expander("View All Data"):
        st.dataframe(df.drop(columns=["latitude", "longitude"]))

if __name__ == "__main__":
    main()