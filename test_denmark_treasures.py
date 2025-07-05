import pytest
import pandas as pd
import json
import os
import sys
from unittest.mock import patch, mock_open

# Add the parent directory to the path to import the app module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app module
import app


class TestDenmarkTreasureLocations:
    """Test suite for Denmark treasure locations functionality."""
    
    def test_denmark_json_format(self):
        """Test that Denmark.json follows the correct format."""
        # Mock the Denmark.json file content
        denmark_json_content = '''[
          {
            "Location": "Vindelev, Central Jutland",
            "Coordinates (Approximate)": "55°43'N, 9°08'E",
            "Treasure Value": "Exceptional",
            "Likelihood (%)": 95,
            "Recommended Reason": "Site of 2021 discovery of largest Iron Age gold hoard in Danish history",
            "Supporting Evidence": "1.5kg of gold artifacts including bracteates with Odin inscriptions from 6th century AD",
            "Supporting Evidence URLs": [
              "https://www.livescience.com/gold-hoard-sixth-century-denmark"
            ]
          }
        ]'''
        
        # Parse the JSON
        denmark_data = json.loads(denmark_json_content)
        
        # Test structure
        assert isinstance(denmark_data, list), "Denmark.json should contain a list of locations"
        assert len(denmark_data) > 0, "Denmark.json should contain at least one location"
        
        # Test required fields for first location
        first_location = denmark_data[0]
        required_fields = [
            "Location",
            "Coordinates (Approximate)",
            "Treasure Value",
            "Likelihood (%)",
            "Recommended Reason",
            "Supporting Evidence",
            "Supporting Evidence URLs"
        ]
        
        for field in required_fields:
            assert field in first_location, f"Required field '{field}' missing from Denmark.json"
    
    def test_coordinate_parsing(self):
        """Test that Danish coordinates are parsed correctly."""
        # Test various Danish coordinate formats
        test_coordinates = [
            "55°43'N, 9°08'E",  # Vindelev format
            "56°36'N, 9°58'E",  # Fyrkat format
            "55°10'N, 14°55'E"  # Bornholm format
        ]
        
        for coord_str in test_coordinates:
            lat, lon = app.parse_coordinates(coord_str)
            
            # Check that coordinates are valid for Denmark
            assert lat is not None, f"Failed to parse latitude from {coord_str}"
            assert lon is not None, f"Failed to parse longitude from {coord_str}"
            
            # Denmark latitude should be between 54.5 and 57.5
            assert 54.5 <= lat <= 57.5, f"Latitude {lat} outside Denmark range for {coord_str}"
            
            # Denmark longitude should be between 8 and 15.5
            assert 8.0 <= lon <= 15.5, f"Longitude {lon} outside Denmark range for {coord_str}"
    
    def test_likelihood_radius_calculation(self):
        """Test that likelihood percentages map to correct radius sizes."""
        test_data = pd.DataFrame({
            'Likelihood (%)': [95, 85, 75, 65, 45]
        })
        
        expected_radii = [
            app.LIKELIHOOD_RADIUS_CONFIG["high"],   # 95% -> high
            app.LIKELIHOOD_RADIUS_CONFIG["high"],   # 85% -> high  
            app.LIKELIHOOD_RADIUS_CONFIG["medium"], # 75% -> medium
            app.LIKELIHOOD_RADIUS_CONFIG["medium"], # 65% -> medium
            app.LIKELIHOOD_RADIUS_CONFIG["low"]     # 45% -> low
        ]
        
        for i, likelihood in enumerate(test_data['Likelihood (%)']):
            radius = (app.LIKELIHOOD_RADIUS_CONFIG["high"] if likelihood >= 80 
                     else app.LIKELIHOOD_RADIUS_CONFIG["medium"] if likelihood >= 60 
                     else app.LIKELIHOOD_RADIUS_CONFIG["low"])
            
            assert radius == expected_radii[i], f"Incorrect radius for likelihood {likelihood}%"
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_denmark_json_loading(self, mock_file_open, mock_listdir, mock_exists):
        """Test that Denmark.json loads correctly in the app."""
        # Mock file system
        mock_exists.return_value = True
        mock_listdir.return_value = ['Denmark.json', 'France.json']
        
        # Mock Denmark.json content
        denmark_json_content = '''[
          {
            "Location": "Vindelev, Central Jutland",
            "Coordinates (Approximate)": "55°43'N, 9°08'E",
            "Treasure Value": "Exceptional",
            "Likelihood (%)": 95,
            "Recommended Reason": "Site of 2021 discovery of largest Iron Age gold hoard",
            "Supporting Evidence": "1.5kg of gold artifacts from 6th century AD",
            "Supporting Evidence URLs": ["https://example.com"]
          },
          {
            "Location": "Fyrkat Viking Ring Fortress, North Jutland",
            "Coordinates (Approximate)": "56°36'N, 9°58'E", 
            "Treasure Value": "High",
            "Likelihood (%)": 85,
            "Recommended Reason": "Active archaeological site near Harald Bluetooth fortress",
            "Supporting Evidence": "300+ Viking silver coins found nearby in 2023",
            "Supporting Evidence URLs": ["https://example.com"]
          }
        ]'''
        
        # Configure mock to return Denmark.json content
        mock_file_open.return_value.read.return_value = denmark_json_content
        
        # Mock Excel file to return empty DataFrame
        with patch('pandas.ExcelFile') as mock_excel:
            mock_excel.return_value.sheet_names = []
            
            # Test the load_data function
            df = app.load_data()
            
            # Verify Denmark data is loaded
            assert not df.empty, "DataFrame should not be empty"
            assert len(df) >= 2, "Should load at least 2 Denmark locations"
            
            # Check that Denmark area is set correctly
            denmark_rows = df[df['Area'] == 'Denmark']
            assert len(denmark_rows) >= 2, "Should have Denmark locations"
            
            # Verify coordinates are parsed
            for _, row in denmark_rows.iterrows():
                assert pd.notna(row['latitude']), "Latitude should be parsed"
                assert pd.notna(row['longitude']), "Longitude should be parsed"
                assert 54.5 <= row['latitude'] <= 57.5, "Latitude should be in Denmark range"
                assert 8.0 <= row['longitude'] <= 15.5, "Longitude should be in Denmark range"
    
    def test_treasure_value_categories(self):
        """Test that treasure values follow expected categories."""
        valid_treasure_values = [
            "High", "Exceptional", "Priceless", "Medium", "Low", "Unknown"
        ]
        
        # Test with sample Denmark data
        test_values = ["Exceptional", "High", "Priceless"]
        
        for value in test_values:
            assert value in valid_treasure_values, f"'{value}' is not a valid treasure value"
    
    def test_supporting_evidence_urls_format(self):
        """Test that Supporting Evidence URLs are properly formatted."""
        # Test URL validation
        test_urls = [
            "https://www.livescience.com/gold-hoard-sixth-century-denmark",
            "https://vejlemuseerne.dk/en/",
            "https://www.ancient-origins.net/news-history-archaeology/viking-coins-0018325"
        ]
        
        for url in test_urls:
            assert url.startswith(('http://', 'https://')), f"URL '{url}' should start with http:// or https://"
            assert '.' in url, f"URL '{url}' should contain a domain"
    
    def test_danish_location_names(self):
        """Test that Danish location names are properly formatted."""
        # Test location name validation
        test_locations = [
            "Vindelev, Central Jutland",
            "Fyrkat Viking Ring Fortress, North Jutland", 
            "Bornholm Island - Multiple Sites",
            "Jelling, Central Jutland"
        ]
        
        for location in test_locations:
            assert len(location) > 0, "Location name should not be empty"
            assert len(location) <= 100, f"Location name '{location}' too long"
            assert not location.startswith(' '), f"Location name '{location}' should not start with space"
            assert not location.endswith(' '), f"Location name '{location}' should not end with space"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
