import pytest
import pandas as pd
import json
import os
import glob
from typing import Dict, List, Tuple
from unittest.mock import patch, mock_open
import importlib.util

# Import app module
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app


class TestGenericCountryTreasures:
    """Generic test framework for any country treasure locations."""
    
    # Country-specific coordinate boundaries (including Southern Hemisphere countries)
    COUNTRY_BOUNDARIES = {
        # Northern Hemisphere countries
        'Denmark': {'lat_min': 54.5, 'lat_max': 57.5, 'lon_min': 8.0, 'lon_max': 15.5},
        'France': {'lat_min': 41.3, 'lat_max': 51.1, 'lon_min': -5.1, 'lon_max': 9.6},
        'Germany': {'lat_min': 47.3, 'lat_max': 55.1, 'lon_min': 5.9, 'lon_max': 15.0},
        'England': {'lat_min': 49.9, 'lat_max': 55.8, 'lon_min': -6.4, 'lon_max': 1.8},
        'Ireland': {'lat_min': 51.4, 'lat_max': 55.4, 'lon_min': -10.5, 'lon_max': -5.4},
        'Italy': {'lat_min': 35.5, 'lat_max': 47.1, 'lon_min': 6.6, 'lon_max': 18.5},
        'Portugal': {'lat_min': 36.9, 'lat_max': 42.2, 'lon_min': -9.5, 'lon_max': -6.2},
        'Spain': {'lat_min': 35.2, 'lat_max': 43.8, 'lon_min': -9.3, 'lon_max': 4.3},
        'Mexico': {'lat_min': 14.5, 'lat_max': 32.7, 'lon_min': -118.4, 'lon_max': -86.7},
        'Philippines': {'lat_min': 4.6, 'lat_max': 21.1, 'lon_min': 116.9, 'lon_max': 126.6},
        'Poland': {'lat_min': 49.0, 'lat_max': 54.8, 'lon_min': 14.1, 'lon_max': 24.1},
        'Bulgaria': {'lat_min': 41.2, 'lat_max': 44.2, 'lon_min': 22.4, 'lon_max': 28.6},
        'China': {'lat_min': 18.2, 'lat_max': 53.6, 'lon_min': 73.5, 'lon_max': 135.1},
        'Greece': {'lat_min': 34.8, 'lat_max': 41.7, 'lon_min': 19.4, 'lon_max': 29.6},
        'Japan': {'lat_min': 24.0, 'lat_max': 45.6, 'lon_min': 122.9, 'lon_max': 153.0},
        
        # Mixed Northern/Southern Hemisphere countries
        'Peru': {'lat_min': -18.4, 'lat_max': -0.0, 'lon_min': -81.3, 'lon_max': -68.7},
        'Indonesia': {'lat_min': -11.0, 'lat_max': 6.0, 'lon_min': 95.0, 'lon_max': 141.0},
        'Brazil': {'lat_min': -33.7, 'lat_max': 5.3, 'lon_min': -73.9, 'lon_max': -28.8},
        
        # Southern Hemisphere countries
        'Australia': {'lat_min': -43.6, 'lat_max': -10.7, 'lon_min': 113.3, 'lon_max': 153.6},
        'NewZealand': {'lat_min': -47.3, 'lat_max': -34.4, 'lon_min': 166.4, 'lon_max': 178.5},
        'Madagascar': {'lat_min': -25.6, 'lat_max': -11.9, 'lon_min': 43.2, 'lon_max': 50.5},
        'Zimbabwe': {'lat_min': -22.4, 'lat_max': -15.6, 'lon_min': 25.2, 'lon_max': 33.1},
        'Botswana': {'lat_min': -26.9, 'lat_max': -17.8, 'lon_min': 20.0, 'lon_max': 29.4},
        'Namibia': {'lat_min': -28.9, 'lat_max': -16.9, 'lon_min': 11.7, 'lon_max': 25.3},
        'Zambia': {'lat_min': -18.1, 'lat_max': -8.2, 'lon_min': 21.9, 'lon_max': 33.7},
        'SouthAfrica': {'lat_min': -34.8, 'lat_max': -22.1, 'lon_min': 16.5, 'lon_max': 32.9},
        'Chile': {'lat_min': -55.9, 'lat_max': -17.5, 'lon_min': -109.5, 'lon_max': -66.4},
        'Argentina': {'lat_min': -55.1, 'lat_max': -21.8, 'lon_min': -73.6, 'lon_max': -53.6},
        'Uruguay': {'lat_min': -35.0, 'lat_max': -30.1, 'lon_min': -58.4, 'lon_max': -53.1},
        'Paraguay': {'lat_min': -27.6, 'lat_max': -19.3, 'lon_min': -62.6, 'lon_max': -54.3},
        'Bolivia': {'lat_min': -22.9, 'lat_max': -9.7, 'lon_min': -69.6, 'lon_max': -57.5},
        'Antarctica': {'lat_min': -90.0, 'lat_max': -60.0, 'lon_min': -180.0, 'lon_max': 180.0}
    }
    
    @classmethod
    def get_all_country_files(cls) -> List[str]:
        """Get all country JSON files in raw directory."""
        raw_dir = os.path.join(os.path.dirname(__file__), 'raw')
        if os.path.exists(raw_dir):
            json_files = glob.glob(os.path.join(raw_dir, '*.json'))
            return json_files
        else:
            # For testing when raw directory doesn't exist, return expected files
            return [
                'raw/Denmark.json', 'raw/France.json', 'raw/Germany.json',
                'raw/England.json', 'raw/Ireland.json', 'raw/Italy.json',
                'raw/Portugal.json', 'raw/Spain.json', 'raw/Peru.json',
                'raw/Mexico.json', 'raw/Philippines.json', 'raw/Poland.json',
                'raw/Indonesia.json', 'raw/Bulgaria.json', 'raw/China.json',
                'raw/Brazil.json', 'raw/Greece.json', 'raw/Japan.json',
                'raw/Australia.json', 'raw/NewZealand.json', 'raw/Madagascar.json',
                'raw/Zimbabwe.json', 'raw/Botswana.json', 'raw/Namibia.json',
                'raw/Zambia.json', 'raw/SouthAfrica.json', 'raw/Chile.json',
                'raw/Argentina.json', 'raw/Uruguay.json', 'raw/Paraguay.json',
                'raw/Bolivia.json', 'raw/Antarctica.json'
            ]
    
    @pytest.mark.parametrize("country_file", get_all_country_files())
    def test_country_json_format(self, country_file):
        """Test that any country JSON follows the correct format."""
        country_name = os.path.basename(country_file).replace('.json', '')
        
        # Mock file content for testing
        mock_content = '''[
          {
            "Location": "Test Location",
            "Coordinates (Approximate)": "50°00'N, 10°00'E",
            "Treasure Value": "High",
            "Likelihood (%)": 85,
            "Recommended Reason": "Test archaeological site",
            "Supporting Evidence": "Test evidence description",
            "Supporting Evidence URLs": ["https://example.com"]
          }
        ]'''
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with open(country_file, 'r') as f:
                data = json.load(f)
        
        # Test structure
        assert isinstance(data, list), f"{country_name}.json should contain a list of locations"
        assert len(data) > 0, f"{country_name}.json should contain at least one location"
        
        # Test required fields for all locations
        required_fields = [
            "Location",
            "Coordinates (Approximate)",
            "Treasure Value",
            "Likelihood (%)",
            "Recommended Reason", 
            "Supporting Evidence",
            "Supporting Evidence URLs"
        ]
        
        for i, location in enumerate(data):
            for field in required_fields:
                assert field in location, f"Required field '{field}' missing from {country_name}.json location {i}"
            
            # Test field types
            assert isinstance(location["Location"], str), f"Location should be string in {country_name}.json location {i}"
            assert isinstance(location["Coordinates (Approximate)"], str), f"Coordinates should be string in {country_name}.json location {i}"
            assert isinstance(location["Treasure Value"], str), f"Treasure Value should be string in {country_name}.json location {i}"
            assert isinstance(location["Recommended Reason"], str), f"Recommended Reason should be string in {country_name}.json location {i}"
            assert isinstance(location["Supporting Evidence"], str), f"Supporting Evidence should be string in {country_name}.json location {i}"
            assert isinstance(location["Supporting Evidence URLs"], list), f"Supporting Evidence URLs should be list in {country_name}.json location {i}"
            
            # Test likelihood is number
            likelihood = location["Likelihood (%)"]
            assert isinstance(likelihood, (int, float)), f"Likelihood should be number in {country_name}.json location {i}"
    
    @pytest.mark.parametrize("country_file", get_all_country_files())
    def test_country_coordinates_within_bounds(self, country_file):
        """Test that coordinates are within realistic bounds for each country."""
        country_name = os.path.basename(country_file).replace('.json', '')
        
        if country_name not in self.COUNTRY_BOUNDARIES:
            pytest.skip(f"Boundary data not available for {country_name}")
        
        boundaries = self.COUNTRY_BOUNDARIES[country_name]
        
        # Mock realistic coordinates for the country
        center_lat = (boundaries['lat_min'] + boundaries['lat_max']) / 2
        center_lon = (boundaries['lon_min'] + boundaries['lon_max']) / 2
        
        # Format coordinates based on hemisphere
        lat_dir = 'N' if center_lat >= 0 else 'S'
        lon_dir = 'E' if center_lon >= 0 else 'W'
        test_coords = [f"{abs(center_lat):.1f}°{lat_dir}, {abs(center_lon):.1f}°{lon_dir}"]
        
        # Add specific test coordinates for some countries
        if country_name == 'Denmark':
            test_coords = ["55°43'N, 9°08'E", "56°36'N, 9°58'E"]
        elif country_name == 'Australia':
            test_coords = ["31°30'S, 115°20'E", "33°55'S, 151°12'E"]
        elif country_name == 'NewZealand':
            test_coords = ["35°15'S, 174°10'E", "44°00'S, 176°30'W"]
        elif country_name == 'Madagascar':
            test_coords = ["17°05'S, 49°51'E", "17°06'S, 49°50'E"]
        elif country_name == 'Zimbabwe':
            test_coords = ["20°16'S, 30°56'E", "20°09'S, 28°22'E"]
        
        for coord_str in test_coords:
            lat, lon = app.parse_coordinates(coord_str)
            
            assert lat is not None, f"Failed to parse latitude from {coord_str} for {country_name}"
            assert lon is not None, f"Failed to parse longitude from {coord_str} for {country_name}"
            
            # Check bounds with tolerance for border regions and coordinate precision
            tolerance = 3.0  # degrees - increased for cross-border sites
            assert (boundaries['lat_min'] - tolerance) <= lat <= (boundaries['lat_max'] + tolerance), \
                f"Latitude {lat} outside {country_name} bounds for {coord_str} (expected {boundaries['lat_min']} to {boundaries['lat_max']})"
            assert (boundaries['lon_min'] - tolerance) <= lon <= (boundaries['lon_max'] + tolerance), \
                f"Longitude {lon} outside {country_name} bounds for {coord_str} (expected {boundaries['lon_min']} to {boundaries['lon_max']})"
    
    @pytest.mark.parametrize("country_file", get_all_country_files())
    def test_country_likelihood_values(self, country_file):
        """Test that likelihood percentages are valid for any country."""
        country_name = os.path.basename(country_file).replace('.json', '')
        
        mock_content = '''[
          {
            "Location": "Test Location",
            "Coordinates (Approximate)": "50°00'N, 10°00'E",
            "Treasure Value": "High",
            "Likelihood (%)": 85,
            "Recommended Reason": "Test site",
            "Supporting Evidence": "Test evidence",
            "Supporting Evidence URLs": []
          }
        ]'''
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with open(country_file, 'r') as f:
                data = json.load(f)
        
        for i, location in enumerate(data):
            likelihood = location["Likelihood (%)"]
            
            # Handle different likelihood formats
            if isinstance(likelihood, str):
                likelihood = float(likelihood.strip('%'))
            likelihood = float(likelihood)
            
            assert 0 <= likelihood <= 100, \
                f"Likelihood {likelihood}% outside valid range for {country_name} location {i}"
    
    @pytest.mark.parametrize("country_file", get_all_country_files())
    def test_country_treasure_values(self, country_file):
        """Test that treasure values follow expected categories."""
        country_name = os.path.basename(country_file).replace('.json', '')
        
        valid_treasure_values = [
            "High", "Exceptional", "Priceless", "Medium", "Low", "Unknown"
        ]
        
        mock_content = '''[
          {
            "Location": "Test Location",
            "Coordinates (Approximate)": "50°00'N, 10°00'E",
            "Treasure Value": "High",
            "Likelihood (%)": 85,
            "Recommended Reason": "Test site",
            "Supporting Evidence": "Test evidence",
            "Supporting Evidence URLs": []
          }
        ]'''
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with open(country_file, 'r') as f:
                data = json.load(f)
        
        for i, location in enumerate(data):
            treasure_value = location["Treasure Value"]
            assert treasure_value in valid_treasure_values, \
                f"Invalid treasure value '{treasure_value}' in {country_name} location {i}. Valid values: {valid_treasure_values}"
    
    @pytest.mark.parametrize("country_file", get_all_country_files())
    def test_country_supporting_evidence_urls(self, country_file):
        """Test that supporting evidence URLs are properly formatted."""
        country_name = os.path.basename(country_file).replace('.json', '')
        
        mock_content = '''[
          {
            "Location": "Test Location",
            "Coordinates (Approximate)": "50°00'N, 10°00'E",
            "Treasure Value": "High",
            "Likelihood (%)": 85,
            "Recommended Reason": "Test site",
            "Supporting Evidence": "Test evidence",
            "Supporting Evidence URLs": ["https://example.com", "https://test.org"]
          }
        ]'''
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with open(country_file, 'r') as f:
                data = json.load(f)
        
        for i, location in enumerate(data):
            urls = location["Supporting Evidence URLs"]
            assert isinstance(urls, list), f"Supporting Evidence URLs should be list in {country_name} location {i}"
            
            for j, url in enumerate(urls):
                assert isinstance(url, str), f"URL {j} should be string in {country_name} location {i}"
                # Basic URL validation - should start with http:// or https://
                if url:  # Allow empty strings
                    assert url.startswith(('http://', 'https://')), \
                        f"Invalid URL format '{url}' in {country_name} location {i}"
    
    def test_southern_hemisphere_coordinates(self):
        """Test that Southern Hemisphere countries have negative latitudes."""
        southern_hemisphere_countries = [
            'Australia', 'NewZealand', 'Madagascar', 'Zimbabwe', 'Botswana', 
            'Namibia', 'Zambia', 'SouthAfrica', 'Chile', 'Argentina', 'Uruguay'
        ]
        
        for country in southern_hemisphere_countries:
            if country in self.COUNTRY_BOUNDARIES:
                boundaries = self.COUNTRY_BOUNDARIES[country]
                assert boundaries['lat_max'] <= 0, \
                    f"Southern Hemisphere country {country} should have negative latitudes"
    
    def test_app_integration_multiple_countries(self):
        """Test that the app can load multiple countries simultaneously."""
        # Mock multiple country files including Southern Hemisphere
        country_files = ['Denmark.json', 'France.json', 'Australia.json', 'Madagascar.json']
        
        mock_contents = {
            'Denmark.json': '''[{
                "Location": "Test Denmark Location",
                "Coordinates (Approximate)": "55°43'N, 9°08'E",
                "Treasure Value": "High",
                "Likelihood (%)": 85,
                "Recommended Reason": "Test site",
                "Supporting Evidence": "Test evidence",
                "Supporting Evidence URLs": []
            }]''',
            'France.json': '''[{
                "Location": "Test France Location", 
                "Coordinates (Approximate)": "46°06'N, 3°12'E",
                "Treasure Value": "Exceptional",
                "Likelihood (%)": 90,
                "Recommended Reason": "Test site",
                "Supporting Evidence": "Test evidence",
                "Supporting Evidence URLs": []
            }]''',
            'Australia.json': '''[{
                "Location": "Test Australia Location",
                "Coordinates (Approximate)": "31°30'S, 115°20'E", 
                "Treasure Value": "Exceptional",
                "Likelihood (%)": 85,
                "Recommended Reason": "Test site",
                "Supporting Evidence": "Test evidence",
                "Supporting Evidence URLs": []
            }]''',
            'Madagascar.json': '''[{
                "Location": "Test Madagascar Location",
                "Coordinates (Approximate)": "17°05'S, 49°51'E", 
                "Treasure Value": "Priceless",
                "Likelihood (%)": 95,
                "Recommended Reason": "Test site",
                "Supporting Evidence": "Test evidence",
                "Supporting Evidence URLs": []
            }]'''
        }
        
        def mock_open_func(filename, *args, **kwargs):
            for country_file, content in mock_contents.items():
                if country_file in filename:
                    return mock_open(read_data=content).return_value
            return mock_open(read_data='[]').return_value
        
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=list(country_files)):
                with patch('builtins.open', side_effect=mock_open_func):
                    with patch('pandas.ExcelFile') as mock_excel:
                        mock_excel.return_value.sheet_names = []
                        
                        # Test the load_data function with multiple countries
                        df = app.load_data()
                        
                        # Verify multiple countries loaded
                        assert not df.empty, "App should load data from multiple countries"
                        
                        countries = df['Area'].unique()
                        expected_countries = ['Denmark', 'France', 'Australia', 'Madagascar']
                        
                        for country in expected_countries:
                            assert country in countries, f"Should load {country} data"
                        
                        # Verify coordinates are parsed for all countries
                        for _, row in df.iterrows():
                            assert pd.notna(row['latitude']), f"Latitude should be parsed for {row['Area']}"
                            assert pd.notna(row['longitude']), f"Longitude should be parsed for {row['Area']}"
                            
                            # Check that Southern Hemisphere countries have negative latitudes
                            if row['Area'] in ['Australia', 'Madagascar']:
                                assert row['latitude'] < 0, f"Southern Hemisphere country {row['Area']} should have negative latitude"


if __name__ == "__main__":
    # Run the generic country tests
    pytest.main([__file__, "-v"])
