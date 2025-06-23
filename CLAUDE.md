# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the application
- `streamlit run app.py` - Start the main Streamlit treasure mapping application
- `streamlit run app2.py` - Start the simple demo version with sample data
- `streamlit run app_poc.py` - Start the proof-of-concept version
- `streamlit run app_poc.py --server.port 8505` - Run POC version on specific port

### Dependencies
- Install dependencies: `pip install -r requirements.txt`
- Main dependencies: streamlit, pandas, pydeck, openpyxl

### Debugging
- VS Code debug configurations exist in `.vscode/launch.json` for:
  - Debugging individual Python files
  - Launching Streamlit app with debugger
  - Running POC version on port 8505

## Architecture Overview

This is a **Streamlit-based treasure hunt mapping application** that visualizes treasure locations on interactive maps using pydeck for 3D mapping.

### Core Application Files

**Main Application (`app.py`)**:
- Production Streamlit app with comprehensive treasure mapping features
- Uses pydeck's ScatterplotLayer for rendering treasure locations
- Two-column layout: interactive map (left) + treasure details panel (right)
- Supports both Excel (.xlsx) and JSON data sources
- Advanced coordinate parsing supporting multiple formats (decimal degrees, DMS)
- Dynamic quick-select buttons based on current map viewport
- Session state management for map position and treasure selection

**Demo/Test Versions**:
- `app2.py` - Simple pydeck demo with sample San Francisco data
- `app_poc.py` - Proof-of-concept version (appears to be similar to main app)

### Data Processing Architecture

**Multi-source Data Loading**:
- Primary data from `treasure.xlsx` (Excel workbook with multiple sheets)
- Secondary data from JSON files in `raw/` directory (France.json, Germany.json, etc.)
- Each data source adds "Area" column based on sheet name or filename

**Coordinate Parsing System** (`parse_coordinates()` function):
- Handles multiple coordinate formats:
  - Decimal degrees: "12.345, -67.890"
  - DMS with minutes: "53°21'N, 4°14'W"
  - DMS with seconds: "54° 16' 25" N, 5° 40' 36" W"
  - Decimal with directions: "55.2415° N, 6.5167° W"
- Validates lat/lon ranges and handles coordinate swapping
- Filters invalid coordinates from display

**Likelihood-based Visualization**:
- Point sizes determined by likelihood percentages via `LIKELIHOOD_RADIUS_CONFIG`
- High likelihood (≥80%): 10000 radius
- Medium likelihood (60-80%): 7000 radius  
- Low likelihood (<60%): 4000 radius

### Interactive Features

**Map Interaction**:
- Click/hover tooltips with location details
- Dynamic color coding (blue for selected, orange for unselected)
- Session state tracking for map center, zoom level, and selection
- Automatic centering and zooming when treasure is selected

**Smart Quick Selection**:
- Context-aware buttons showing nearby locations based on current map view
- Distance calculation using Haversine formula
- Button count and labeling adapts to zoom level
- Distance display when zoomed in (≥zoom level 6)

**Data Management**:
- Expandable full dataset table view
- Comprehensive treasure detail display for selected items
- Handles various data types including URL lists and metadata

### Key Technical Components

- **Mapping**: pydeck with Mapbox satellite/road tiles
- **Data Processing**: pandas with openpyxl for Excel support
- **State Management**: Streamlit session state for UI persistence
- **Coordinate Systems**: Robust regex-based parsing with validation
- **Layout**: Streamlit columns for responsive design (7:3 ratio)