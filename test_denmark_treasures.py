import pytest
import pandas as pd
import json
import os
import sys
from unittest.mock import patch, mock_open

# Add the parent directory to the path to import the app module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app module and security module
import app
from treasure_security import TreasureDataValidator, secure_load_treasure_data


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


class TestTreasureSecurityValidation:
    """Security-focused test suite for treasure location data validation."""
    
    def test_text_sanitization(self):
        """Test that malicious text inputs are properly sanitized."""
        # Test XSS prevention
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "Normal text with <script> tags",
            "Text with 'quotes' and \"double quotes\"",
            "Text with > and < symbols"
        ]
        
        for malicious_text in malicious_inputs:
            sanitized = TreasureDataValidator.sanitize_text(malicious_text, 100)
            assert '<' not in sanitized, f"Failed to sanitize: {malicious_text}"
            assert '>' not in sanitized, f"Failed to sanitize: {malicious_text}"
            assert '"' not in sanitized, f"Failed to sanitize: {malicious_text}"
            assert "'" not in sanitized, f"Failed to sanitize: {malicious_text}"
    
    def test_url_validation_security(self):
        """Test URL validation against malicious URLs."""
        # Test malicious URL schemes
        malicious_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd",
            "vbscript:msgbox('test')",
            "ftp://malicious.com/file.txt"
        ]
        
        for url in malicious_urls:
            is_valid, message = TreasureDataValidator.validate_url(url)
            assert not is_valid, f"Should reject malicious URL: {url}"
            assert "malicious" in message.lower() or "invalid" in message.lower()
    
    def test_url_validation_legitimate(self):
        """Test that legitimate URLs pass validation."""
        legitimate_urls = [
            "https://www.livescience.com/gold-hoard-sixth-century-denmark",
            "https://vejlemuseerne.dk/en/",
            "http://archaeology.org/news/2023/04/21/230424-denmark-viking-hoard/",
            "https://en.wikipedia.org/wiki/Rispebjerg"
        ]
        
        for url in legitimate_urls:
            is_valid, message = TreasureDataValidator.validate_url(url)
            assert is_valid, f"Should accept legitimate URL: {url} - {message}"
    
    def test_coordinate_boundary_validation(self):
        """Test that coordinates outside Denmark are rejected."""
        # Test coordinates outside Denmark
        invalid_coordinates = [
            "60°00'N, 10°00'E",  # Norway
            "52°00'N, 5°00'E",   # Netherlands  
            "50°00'N, 14°00'E",  # Czech Republic
            "45°00'N, 2°00'E"    # France
        ]
        
        for coord in invalid_coordinates:
            is_valid, lat, lon, message = TreasureDataValidator.validate_coordinates(coord)
            assert not is_valid, f"Should reject coordinates outside Denmark: {coord}"
            assert "outside Denmark" in message
    
    def test_coordinate_boundary_validation_valid(self):
        """Test that valid Danish coordinates pass validation."""
        valid_coordinates = [
            "55°43'N, 9°08'E",   # Vindelev
            "56°36'N, 9°58'E",   # Fyrkat
            "55°10'N, 14°55'E",  # Bornholm
            "55°45'N, 9°25'E"    # Jelling
        ]
        
        for coord in valid_coordinates:
            is_valid, lat, lon, message = TreasureDataValidator.validate_coordinates(coord)
            assert is_valid, f"Should accept valid Danish coordinates: {coord}"
            assert lat is not None and lon is not None
    
    def test_treasure_entry_validation(self):
        """Test validation of complete treasure entries."""
        # Valid entry
        valid_entry = {
            "Location": "Test Location, Denmark",
            "Coordinates (Approximate)": "55°43'N, 9°08'E",
            "Treasure Value": "High",
            "Likelihood (%)": 85,
            "Recommended Reason": "Test reason for treasure location",
            "Supporting Evidence": "Test evidence description",
            "Supporting Evidence URLs": ["https://www.livescience.com/test"]
        }
        
        is_valid, sanitized, errors = TreasureDataValidator.validate_treasure_entry(valid_entry)
        assert is_valid, f"Valid entry should pass validation. Errors: {errors}"
        assert len(sanitized) == len(valid_entry), "All fields should be present in sanitized entry"
    
    def test_treasure_entry_validation_missing_fields(self):
        """Test that entries with missing required fields are rejected."""
        incomplete_entry = {
            "Location": "Test Location",
            "Treasure Value": "High"
            # Missing other required fields
        }
        
        is_valid, sanitized, errors = TreasureDataValidator.validate_treasure_entry(incomplete_entry)
        assert not is_valid, "Entry with missing fields should fail validation"
        assert len(errors) > 0, "Should report missing field errors"
        
        # Check that all missing fields are reported
        missing_fields = [
            "Coordinates (Approximate)",
            "Likelihood (%)", 
            "Recommended Reason",
            "Supporting Evidence",
            "Supporting Evidence URLs"
        ]
        
        error_text = " ".join(errors)
        for field in missing_fields:
            assert field in error_text, f"Should report missing field: {field}"
    
    def test_treasure_value_validation(self):
        """Test validation of treasure value categories."""
        valid_values = ["High", "Exceptional", "Priceless", "Medium", "Low", "Unknown"]
        invalid_values = ["Super High", "AMAZING", "treasure", ""]
        
        base_entry = {
            "Location": "Test Location",
            "Coordinates (Approximate)": "55°43'N, 9°08'E",
            "Likelihood (%)": 85,
            "Recommended Reason": "Test reason",
            "Supporting Evidence": "Test evidence",
            "Supporting Evidence URLs": []
        }
        
        # Test valid values
        for value in valid_values:
            entry = base_entry.copy()
            entry["Treasure Value"] = value
            is_valid, sanitized, errors = TreasureDataValidator.validate_treasure_entry(entry)
            assert is_valid, f"Should accept valid treasure value: {value}"
        
        # Test invalid values
        for value in invalid_values:
            entry = base_entry.copy()
            entry["Treasure Value"] = value
            is_valid, sanitized, errors = TreasureDataValidator.validate_treasure_entry(entry)
            assert not is_valid, f"Should reject invalid treasure value: {value}"
    
    def test_likelihood_percentage_validation(self):
        """Test validation of likelihood percentages."""
        base_entry = {
            "Location": "Test Location",
            "Coordinates (Approximate)": "55°43'N, 9°08'E",
            "Treasure Value": "High",
            "Recommended Reason": "Test reason",
            "Supporting Evidence": "Test evidence",
            "Supporting Evidence URLs": []
        }
        
        # Test valid percentages
        valid_percentages = [0, 50, 85, 100, "75", "90%"]
        for pct in valid_percentages:
            entry = base_entry.copy()
            entry["Likelihood (%)"] = pct
            is_valid, sanitized, errors = TreasureDataValidator.validate_treasure_entry(entry)
            assert is_valid, f"Should accept valid likelihood: {pct}"
        
        # Test invalid percentages
        invalid_percentages = [-5, 150, "invalid", "", None]
        for pct in invalid_percentages:
            entry = base_entry.copy()
            entry["Likelihood (%)"] = pct
            is_valid, sanitized, errors = TreasureDataValidator.validate_treasure_entry(entry)
            assert not is_valid, f"Should reject invalid likelihood: {pct}"
    
    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\drivers\\etc\\hosts"
        ]
        
        for path in malicious_paths:
            is_valid, data, errors = TreasureDataValidator.validate_json_file(path)
            assert not is_valid, f"Should reject malicious path: {path}"
            assert any("Invalid file path" in error for error in errors)
    
    def test_large_content_protection(self):
        """Test protection against DoS via large content."""
        # Test text length limits
        very_long_text = "A" * 5000  # Exceeds max lengths
        
        sanitized = TreasureDataValidator.sanitize_text(very_long_text, 100)
        assert len(sanitized) <= 103, "Should truncate long text (100 + '...')"
        assert sanitized.endswith("..."), "Should add ellipsis for truncated text"
    
    def test_too_many_urls_protection(self):
        """Test protection against DoS via too many URLs."""
        base_entry = {
            "Location": "Test Location",
            "Coordinates (Approximate)": "55°43'N, 9°08'E",
            "Treasure Value": "High",
            "Likelihood (%)": 85,
            "Recommended Reason": "Test reason",
            "Supporting Evidence": "Test evidence",
            "Supporting Evidence URLs": ["https://example.com"] * 20  # Too many URLs
        }
        
        is_valid, sanitized, errors = TreasureDataValidator.validate_treasure_entry(base_entry)
        assert not is_valid, "Should reject entry with too many URLs"
        assert any("Too many URLs" in error for error in errors)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
