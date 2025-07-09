#!/usr/bin/env python3
"""
Test South American Countries Treasure Data

This test suite validates the JSON files for all South American countries
to ensure they follow the correct format and contain valid treasure location data.
"""

import json
import os
import unittest
import re
from typing import Dict, List, Any


class TestSouthAmericanCountries(unittest.TestCase):
    """Test suite for South American country treasure data files."""
    
    # List of all South American countries that should have JSON files
    SOUTH_AMERICAN_COUNTRIES = [
        'Colombia', 'Brazil', 'Argentina', 'Bolivia', 'Ecuador', 
        'Venezuela', 'Chile', 'Uruguay', 'Paraguay', 'Guyana', 
        'Suriname', 'Peru'
    ]
    
    # Required fields for each treasure location entry
    REQUIRED_FIELDS = [
        'Location',
        'Coordinates (Approximate)',
        'Treasure Value',
        'Likelihood (%)',
        'Recommended Reason',
        'Supporting Evidence',
        'Supporting Evidence URLs'
    ]
    
    # Valid treasure value categories
    VALID_TREASURE_VALUES = [
        'Low', 'Medium', 'High', 'Exceptional', 'Priceless'
    ]

    def setUp(self):
        """Set up test environment."""
        self.raw_dir = os.path.join(os.path.dirname(__file__), 'raw')
        self.country_data = {}
        self.load_country_data()

    def load_country_data(self):
        """Load JSON data for all South American countries."""
        for country in self.SOUTH_AMERICAN_COUNTRIES:
            file_path = os.path.join(self.raw_dir, f'{country}.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        self.country_data[country] = data
                    except json.JSONDecodeError as e:
                        self.fail(f"Invalid JSON in {country}.json: {e}")
            else:
                self.fail(f"Missing file: {country}.json")

    def extract_treasure_data(self, data: Any) -> List[Dict[str, Any]]:
        """
        Extract treasure location data from JSON, handling both formats:
        1. Direct array format: [{"Location": "...", ...}, ...]
        2. Legacy table format: {"tables": [{"data": [{"Location": "...", ...}]}]}
        """
        if isinstance(data, list):
            # Direct array format
            return data
        elif isinstance(data, dict) and 'tables' in data:
            # Legacy table format
            if (isinstance(data['tables'], list) and 
                len(data['tables']) > 0 and 
                'data' in data['tables'][0]):
                return data['tables'][0]['data']
        
        self.fail(f"Unexpected JSON structure: {type(data)}")

    def validate_coordinates(self, coordinates: str) -> bool:
        """
        Validate coordinate format. Accepts various formats:
        - "55°43'N, 9°08'E" (Degree-Minute-Direction)
        - "54.32° N, 5.72° W" (Decimal degree with direction)
        - "12°15'S, 76°53'W" (Standard format)
        """
        # Pattern for coordinates with degrees, minutes, and direction
        pattern1 = r"^\d{1,2}°\d{1,2}'[NS],\s*\d{1,3}°\d{1,2}'[EW]$"
        # Pattern for decimal degrees with direction
        pattern2 = r"^\d{1,2}\.\d+°\s*[NS],\s*\d{1,3}\.\d+°\s*[EW]$"
        
        return bool(re.match(pattern1, coordinates) or re.match(pattern2, coordinates))

    def validate_url(self, url: str) -> bool:
        """Validate URL format."""
        url_pattern = r'^https?://.+\..+'
        return bool(re.match(url_pattern, url))

    def test_all_countries_have_files(self):
        """Test that all South American countries have JSON files."""
        for country in self.SOUTH_AMERICAN_COUNTRIES:
            with self.subTest(country=country):
                self.assertIn(country, self.country_data, 
                            f"Missing data for {country}")

    def test_json_structure_validity(self):
        """Test that all JSON files have valid structure."""
        for country, data in self.country_data.items():
            with self.subTest(country=country):
                # Should be either a list or a dict with tables
                self.assertTrue(
                    isinstance(data, list) or 
                    (isinstance(data, dict) and 'tables' in data),
                    f"{country}.json has invalid top-level structure"
                )

    def test_treasure_locations_exist(self):
        """Test that each country has at least one treasure location."""
        for country, data in self.country_data.items():
            with self.subTest(country=country):
                treasure_data = self.extract_treasure_data(data)
                self.assertGreater(len(treasure_data), 0, 
                                 f"{country} has no treasure locations")

    def test_required_fields_present(self):
        """Test that all required fields are present in each treasure location."""
        for country, data in self.country_data.items():
            with self.subTest(country=country):
                treasure_data = self.extract_treasure_data(data)
                
                for idx, location in enumerate(treasure_data):
                    with self.subTest(location_idx=idx):
                        for field in self.REQUIRED_FIELDS:
                            self.assertIn(field, location, 
                                        f"{country} location {idx} missing field: {field}")

    def test_field_data_types(self):
        """Test that fields have correct data types."""
        for country, data in self.country_data.items():
            with self.subTest(country=country):
                treasure_data = self.extract_treasure_data(data)
                
                for idx, location in enumerate(treasure_data):
                    with self.subTest(location_idx=idx):
                        # String fields
                        for field in ['Location', 'Coordinates (Approximate)', 
                                    'Treasure Value', 'Recommended Reason', 
                                    'Supporting Evidence']:
                            self.assertIsInstance(location[field], str,
                                                f"{country} location {idx} field {field} should be string")
                        
                        # Numeric field
                        likelihood = location['Likelihood (%)']
                        self.assertTrue(isinstance(likelihood, (int, float)),
                                      f"{country} location {idx} Likelihood should be numeric")
                        
                        # Array field
                        self.assertIsInstance(location['Supporting Evidence URLs'], list,
                                            f"{country} location {idx} Supporting Evidence URLs should be list")

    def test_coordinate_format(self):
        """Test that coordinates follow valid format."""
        for country, data in self.country_data.items():
            with self.subTest(country=country):
                treasure_data = self.extract_treasure_data(data)
                
                for idx, location in enumerate(treasure_data):
                    with self.subTest(location_idx=idx):
                        coordinates = location['Coordinates (Approximate)']
                        self.assertTrue(self.validate_coordinates(coordinates),
                                      f"{country} location {idx} has invalid coordinates: {coordinates}")

    def test_treasure_value_validity(self):
        """Test that treasure values are from valid categories."""
        for country, data in self.country_data.items():
            with self.subTest(country=country):
                treasure_data = self.extract_treasure_data(data)
                
                for idx, location in enumerate(treasure_data):
                    with self.subTest(location_idx=idx):
                        treasure_value = location['Treasure Value']
                        self.assertIn(treasure_value, self.VALID_TREASURE_VALUES,
                                    f"{country} location {idx} has invalid treasure value: {treasure_value}")

    def test_likelihood_range(self):
        """Test that likelihood percentages are within valid range (0-100)."""
        for country, data in self.country_data.items():
            with self.subTest(country=country):
                treasure_data = self.extract_treasure_data(data)
                
                for idx, location in enumerate(treasure_data):
                    with self.subTest(location_idx=idx):
                        likelihood = location['Likelihood (%)']
                        self.assertGreaterEqual(likelihood, 0,
                                              f"{country} location {idx} likelihood too low: {likelihood}")
                        self.assertLessEqual(likelihood, 100,
                                           f"{country} location {idx} likelihood too high: {likelihood}")

    def test_url_format(self):
        """Test that Supporting Evidence URLs are properly formatted."""
        for country, data in self.country_data.items():
            with self.subTest(country=country):
                treasure_data = self.extract_treasure_data(data)
                
                for idx, location in enumerate(treasure_data):
                    with self.subTest(location_idx=idx):
                        urls = location['Supporting Evidence URLs']
                        for url_idx, url in enumerate(urls):
                            if url:  # Skip empty URLs
                                self.assertTrue(self.validate_url(url),
                                              f"{country} location {idx} URL {url_idx} invalid: {url}")

    def test_content_quality(self):
        """Test basic content quality requirements."""
        for country, data in self.country_data.items():
            with self.subTest(country=country):
                treasure_data = self.extract_treasure_data(data)
                
                for idx, location in enumerate(treasure_data):
                    with self.subTest(location_idx=idx):
                        # Location should not be empty
                        self.assertGreater(len(location['Location'].strip()), 0,
                                         f"{country} location {idx} has empty location name")
                        
                        # Recommended Reason should have substantial content
                        self.assertGreater(len(location['Recommended Reason'].strip()), 10,
                                         f"{country} location {idx} has insufficient recommended reason")
                        
                        # Supporting Evidence should have substantial content
                        self.assertGreater(len(location['Supporting Evidence'].strip()), 10,
                                         f"{country} location {idx} has insufficient supporting evidence")

    def test_country_specific_validations(self):
        """Test country-specific validation rules."""
        # Test Peru specifically since it already existed
        if 'Peru' in self.country_data:
            peru_data = self.extract_treasure_data(self.country_data['Peru'])
            self.assertGreater(len(peru_data), 3, "Peru should have multiple treasure locations")
        
        # Test major countries have reasonable number of locations
        major_countries = ['Colombia', 'Brazil', 'Argentina', 'Bolivia']
        for country in major_countries:
            if country in self.country_data:
                with self.subTest(country=country):
                    country_data = self.extract_treasure_data(self.country_data[country])
                    self.assertGreaterEqual(len(country_data), 3,
                                          f"{country} should have at least 3 treasure locations")

    def test_south_american_geographic_validity(self):
        """Test that coordinates are within South American geographic bounds."""
        # Approximate bounds for South America
        # Latitude: 13°N to 55°S
        # Longitude: 35°W to 82°W
        
        for country, data in self.country_data.items():
            with self.subTest(country=country):
                treasure_data = self.extract_treasure_data(data)
                
                for idx, location in enumerate(treasure_data):
                    with self.subTest(location_idx=idx):
                        coordinates = location['Coordinates (Approximate)']
                        
                        # Extract latitude and longitude from coordinate string
                        # This is a basic check - could be more sophisticated
                        if 'S' in coordinates or 'N' in coordinates:
                            # Basic validation that it looks like South American coordinates
                            self.assertTrue('W' in coordinates,
                                          f"{country} location {idx} should have Western longitude")


def run_tests():
    """Run all tests and return results."""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_tests()
