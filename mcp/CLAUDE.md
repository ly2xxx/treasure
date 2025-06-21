# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the application
- `streamlit run app.py` - Start the Streamlit web application
- Debug configuration exists in `.vscode/launch.json` for running with debugger

### Dependencies
- Install dependencies: `pip install -r requirements.txt`
- Main dependencies: streamlit, pandas, pydeck, openpyxl

## Architecture Overview

This is a **Streamlit-based treasure hunt mapping application** that visualizes treasure locations on an interactive map using pydeck for 3D mapping.

### Core Components

**Main Application (`app.py`)**:
- Single-file Streamlit app with map visualization
- Uses pydeck's ScatterplotLayer for rendering treasure locations on satellite maps
- Two-column layout: map view (left) + treasure details (right)

**Data Processing**:
- Reads treasure data from `treasure.xlsx` using pandas/openpyxl
- `parse_coordinates()` function handles multiple coordinate formats:
  - Decimal degrees: "12.345, -67.890"
  - DMS format: "53°21'N, 4°14'W"
- Filters out invalid coordinates and validates lat/lon ranges

**Interactive Features**:
- Map click/hover tooltips showing location details
- Sidebar treasure selection with automatic map centering/zooming
- Session state management for map position and selected treasure
- Expandable data table view

### Key Technical Details

- Map uses Mapbox satellite tiles via pydeck
- Coordinate parsing handles various string formats with regex
- Session state tracks selected treasure and map viewport
- Tooltip system shows location info on hover
- Dynamic zoom levels: global view (zoom=2) vs focused view (zoom=8)

### Data Structure
The Excel file should contain:
- "Location" column (primary identifier)
- "Coordinates (Approximate)" column (various coordinate formats)
- Additional metadata columns displayed in treasure details