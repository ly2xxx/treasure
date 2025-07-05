import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock
import pandas as pd
import time

# Import modules for testing
from treasure_security import TreasureDataValidator, secure_load_treasure_data


class TestComprehensiveDenmarkTreasures:
    """Comprehensive test suite for Denmark treasure locations feature."""
    
    def test_integration_full_app_loading(self):
        """Integration test for full app loading with Denmark.json."""
        # Mock complete Denmark.json content
        complete_denmark_data = '''[
          {
            "Location": "Vindelev, Central Jutland",
            "Coordinates (Approximate)": "55°43'N, 9°08'E",
            "Treasure Value": "Exceptional",
            "Likelihood (%)": 95,
            "Recommended Reason": "Site of 2021 discovery of largest Iron Age gold hoard in Danish history",
            "Supporting Evidence": "1.5kg of gold artifacts including bracteates with Odin inscriptions from 6th century AD",
            "Supporting Evidence URLs": [
              "https://www.livescience.com/gold-hoard-sixth-century-denmark",
              "https://vejlemuseerne.dk/en/"
            ]
          },
          {
            "Location": "Fyrkat Viking Ring Fortress, North Jutland",
            "Coordinates (Approximate)": "56°36'N, 9°58'E",
            "Treasure Value": "High",
            "Likelihood (%)": 85,
            "Recommended Reason": "Active archaeological site near Harald Bluetooth's fortress",
            "Supporting Evidence": "300+ Viking silver coins and jewelry found nearby in 2023",
            "Supporting Evidence URLs": [
              "https://www.ancient-origins.net/news-history-archaeology/viking-coins-0018325"
            ]
          },
          {
            "Location": "Bornholm Island - Multiple Sites",
            "Coordinates (Approximate)": "55°10'N, 14°55'E",
            "Treasure Value": "High",
            "Likelihood (%)": 90,
            "Recommended Reason": "Island with highest concentration of Viking silver hoards in Denmark",
            "Supporting Evidence": "130+ treasures found, representing half of all Danish Viking age silver discoveries",
            "Supporting Evidence URLs": [
              "https://bornholmarch.eu/about/history-ab/"
            ]
          }
        ]'''
        
        with patch('builtins.open', mock_open(read_data=complete_denmark_data)):
            with patch('os.path.exists', return_value=True):
                with patch('os.listdir', return_value=['Denmark.json']):
                    with patch('pandas.ExcelFile') as mock_excel:
                        mock_excel.return_value.sheet_names = []
                        
                        # Import and test app loading
                        import app
                        df = app.load_data()
                        
                        # Verify integration
                        assert not df.empty, "App should load Denmark data"
                        denmark_data = df[df['Area'] == 'Denmark']
                        assert len(denmark_data) == 3, "Should load all 3 Denmark locations"
                        
                        # Verify all required columns exist
                        required_columns = ['Location', 'latitude', 'longitude', 'radius', 'Area']
                        for col in required_columns:
                            assert col in df.columns, f"Missing required column: {col}"
    
    def test_performance_multiple_json_files(self):
        """Performance test for loading multiple large JSON files."""
        # Create large mock data
        large_location_data = []
        for i in range(50):  # Maximum allowed locations per file
            large_location_data.append({
                "Location": f"Test Location {i}, Denmark",
                "Coordinates (Approximate)": "55°43'N, 9°08'E",
                "Treasure Value": "High",
                "Likelihood (%)": 80,
                "Recommended Reason": f"Test reason {i}",
                "Supporting Evidence": f"Test evidence {i}",
                "Supporting Evidence URLs": ["https://example.com"]
            })
        
        large_json_content = json.dumps(large_location_data)
        
        # Test performance
        start_time = time.time()
        
        with patch('builtins.open', mock_open(read_data=large_json_content)):
            is_valid, validated_data, errors = TreasureDataValidator.validate_json_file('test.json')
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 5.0, f"Processing took too long: {processing_time}s"
        assert is_valid, "Large valid file should be processed successfully"
        assert len(validated_data) == 50, "Should validate all entries"
    
    def test_edge_case_coordinate_formats(self):
        """Test edge cases for various coordinate formats."""
        edge_case_coordinates = [
            # Valid edge cases
            ("55°00'N, 15°30'E", True),   # Maximum longitude boundary
            ("57°30'N, 8°00'E", True),    # Maximum latitude boundary
            ("54°30'N, 14°00'E", True),   # Near minimum latitude
            
            # Invalid edge cases
            ("54°29'N, 9°00'E", False),   # Below minimum latitude
            ("57°31'N, 9°00'E", False),   # Above maximum latitude
            ("55°00'N, 7°59'E", False),   # Below minimum longitude
            ("55°00'N, 15°31'E", False),  # Above maximum longitude
            
            # Malformed formats
            ("invalid coordinates", False),
            ("55°N, 9°E", False),         # Missing minutes
            ("55.5°N, 9.1°E", True),      # Decimal degrees format
            ("", False),                  # Empty string
            (None, False),                # None value
            ("55°43'S, 9°08'E", False),   # Wrong hemisphere
            ("55°43'N, 9°08'W", False),   # Wrong hemisphere
        ]
        
        for coord_str, should_be_valid in edge_case_coordinates:
            is_valid, lat, lon, message = TreasureDataValidator.validate_coordinates(str(coord_str) if coord_str is not None else "")
            if should_be_valid:
                assert is_valid, f"Should accept valid coordinates: {coord_str} - {message}"
                assert lat is not None and lon is not None, f"Should parse coordinates: {coord_str}"
            else:
                assert not is_valid, f"Should reject invalid coordinates: {coord_str}"
    
    def test_boundary_value_danish_limits(self):
        """Test boundary values for Danish geographic limits."""
        # Exact boundary coordinates
        boundary_tests = [
            # Exact boundaries (should pass)
            (TreasureDataValidator.DENMARK_LAT_MIN, TreasureDataValidator.DENMARK_LON_MIN, True),
            (TreasureDataValidator.DENMARK_LAT_MAX, TreasureDataValidator.DENMARK_LON_MAX, True),
            (TreasureDataValidator.DENMARK_LAT_MIN, TreasureDataValidator.DENMARK_LON_MAX, True),
            (TreasureDataValidator.DENMARK_LAT_MAX, TreasureDataValidator.DENMARK_LON_MIN, True),
            
            # Just outside boundaries (should fail)
            (TreasureDataValidator.DENMARK_LAT_MIN - 0.1, TreasureDataValidator.DENMARK_LON_MIN, False),
            (TreasureDataValidator.DENMARK_LAT_MAX + 0.1, TreasureDataValidator.DENMARK_LON_MAX, False),
            (TreasureDataValidator.DENMARK_LAT_MIN, TreasureDataValidator.DENMARK_LON_MIN - 0.1, False),
            (TreasureDataValidator.DENMARK_LAT_MAX, TreasureDataValidator.DENMARK_LON_MAX + 0.1, False),
        ]
        
        for lat, lon, should_be_valid in boundary_tests:
            # Create coordinate string
            lat_dir = 'N' if lat >= 0 else 'S'
            lon_dir = 'E' if lon >= 0 else 'W'
            coord_str = f"{abs(lat):.1f}°N, {abs(lon):.1f}°E" if lat >= 0 and lon >= 0 else f"{abs(lat):.1f}°{lat_dir}, {abs(lon):.1f}°{lon_dir}"
            
            is_valid, parsed_lat, parsed_lon, message = TreasureDataValidator.validate_coordinates(coord_str)
            
            if should_be_valid:
                assert is_valid, f"Boundary coordinate should be valid: {coord_str} - {message}"
            else:
                assert not is_valid, f"Out-of-bounds coordinate should be invalid: {coord_str}"
    
    def test_security_penetration_tests(self):
        """Security penetration tests for various attack vectors."""
        
        # Test 1: Script injection in text fields
        script_injection_tests = [
            "<script>alert('xss')</script>",
            "javascript:alert('test')",
            "onload=alert('xss')",
            "{{7*7}}",  # Template injection
            "${7*7}",   # Expression injection
            "'; DROP TABLE treasures; --",  # SQL injection (even though not applicable)
        ]
        
        for malicious_input in script_injection_tests:
            sanitized = TreasureDataValidator.sanitize_text(malicious_input, 100)
            assert '<' not in sanitized, f"Failed to sanitize script tags: {malicious_input}"
            assert 'script' not in sanitized.lower(), f"Failed to remove script content: {malicious_input}"
        
        # Test 2: URL injection attacks
        malicious_urls = [
            "javascript:void(0)",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('test')",
            "file:///etc/passwd",
            "ftp://malicious.com/payload.exe",
            "mailto:test@test.com?subject=<script>alert('xss')</script>",
        ]
        
        for malicious_url in malicious_urls:
            is_valid, message = TreasureDataValidator.validate_url(malicious_url)
            assert not is_valid, f"Should reject malicious URL: {malicious_url}"
        
        # Test 3: File path traversal
        path_traversal_tests = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "file:///../../../etc/passwd",
        ]
        
        for malicious_path in path_traversal_tests:
            is_valid, data, errors = TreasureDataValidator.validate_json_file(malicious_path)
            assert not is_valid, f"Should reject path traversal: {malicious_path}"
            assert any("Invalid file path" in error for error in errors)
    
    def test_error_handling_corrupted_json(self):
        """Test error handling for various types of corrupted JSON files."""
        
        corrupted_json_tests = [
            # Invalid JSON syntax
            ('{"Location": "Test"', "Invalid JSON format"),
            ('[{"Location": "Test",}]', "Invalid JSON format"),  # Trailing comma
            ('{"Location": "Test" "Value": "High"}', "Invalid JSON format"),  # Missing comma
            
            # Wrong data structure
            ('{"not_an_array": "value"}', "JSON root must be an array"),
            ('[]', "JSON file contains no treasure locations"),
            ('"just a string"', "JSON root must be an array"),
            ('123', "JSON root must be an array"),
            
            # Missing required fields
            ('[{"Location": "Test"}]', "Missing required field"),
            ('[{"Coordinates": "55°N, 9°E"}]', "Missing required field"),
        ]
        
        for corrupted_content, expected_error_type in corrupted_json_tests:
            with patch('builtins.open', mock_open(read_data=corrupted_content)):
                is_valid, data, errors = TreasureDataValidator.validate_json_file('test.json')
                
                assert not is_valid, f"Should reject corrupted JSON: {corrupted_content[:50]}..."
                assert len(errors) > 0, "Should report errors for corrupted JSON"
                assert any(expected_error_type in error for error in errors), f"Should report specific error type: {expected_error_type}"
    
    def test_mock_external_url_validation(self):
        """Test URL validation with mocked external checks."""
        
        # Test trusted domains
        trusted_urls = [
            "https://www.livescience.com/article",
            "https://vejlemuseerne.dk/exhibition",
            "https://bornholmarch.eu/research",
            "https://en.wikipedia.org/wiki/Denmark",
        ]
        
        for url in trusted_urls:
            is_valid, message = TreasureDataValidator.validate_url(url)
            assert is_valid, f"Should accept trusted domain URL: {url}"
            assert "Valid URL" in message or "Warning" in message
        
        # Test untrusted but valid domains
        untrusted_urls = [
            "https://unknown-site.com/article",
            "http://some-blog.net/post",
        ]
        
        for url in untrusted_urls:
            is_valid, message = TreasureDataValidator.validate_url(url)
            assert is_valid, f"Should accept valid but untrusted URL: {url}"
            assert "Warning" in message, f"Should warn about untrusted domain: {url}"
    
    def test_concurrent_access_simulation(self):
        """Simulate concurrent access to treasure data validation."""
        import threading
        import queue
        
        def validate_entry_worker(entry_data, result_queue):
            """Worker function for concurrent validation."""
            try:
                is_valid, sanitized, errors = TreasureDataValidator.validate_treasure_entry(entry_data)
                result_queue.put(('success', is_valid, len(errors)))
            except Exception as e:
                result_queue.put(('error', str(e), None))
        
        # Create test data
        test_entry = {
            "Location": "Concurrent Test Location",
            "Coordinates (Approximate)": "55°43'N, 9°08'E",
            "Treasure Value": "High",
            "Likelihood (%)": 85,
            "Recommended Reason": "Test concurrent access",
            "Supporting Evidence": "Test evidence",
            "Supporting Evidence URLs": ["https://example.com"]
        }
        
        # Run concurrent validations
        result_queue = queue.Queue()
        threads = []
        
        for i in range(10):  # Simulate 10 concurrent requests
            thread = threading.Thread(target=validate_entry_worker, args=(test_entry.copy(), result_queue))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        assert len(results) == 10, "Should have 10 results from concurrent access"
        
        # All should succeed
        for status, is_valid, error_count in results:
            assert status == 'success', "All concurrent validations should succeed"
            assert is_valid, "All entries should be valid"
    
    def test_memory_usage_large_datasets(self):
        """Test memory usage with large datasets."""
        import sys
        
        # Create a large dataset
        large_dataset = []
        for i in range(1000):  # Large but manageable dataset
            large_dataset.append({
                "Location": f"Location {i}, Denmark",
                "Coordinates (Approximate)": "55°43'N, 9°08'E",
                "Treasure Value": "High",
                "Likelihood (%)": 85,
                "Recommended Reason": "A" * 100,  # Moderate size
                "Supporting Evidence": "B" * 200,  # Moderate size
                "Supporting Evidence URLs": ["https://example.com"]
            })
        
        # Measure memory before processing
        import tracemalloc
        tracemalloc.start()
        
        # Process the large dataset
        valid_entries = []
        for entry in large_dataset:
            is_valid, sanitized, errors = TreasureDataValidator.validate_treasure_entry(entry)
            if is_valid:
                valid_entries.append(sanitized)
        
        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory should be reasonable (less than 100MB for this test)
        assert peak < 100 * 1024 * 1024, f"Memory usage too high: {peak / 1024 / 1024:.2f} MB"
        assert len(valid_entries) == 1000, "Should process all valid entries"
    
    def test_unicode_and_encoding_handling(self):
        """Test handling of Unicode characters and various encodings."""
        
        unicode_test_data = [
            # Danish characters
            "Rødby, Lolland-Falster",
            "Køge Bugt, Sjælland",
            "Århus, Jylland",
            
            # Other Unicode characters
            "Location with émojis 🏴‍☠️⚓",
            "Location with çhäracters",
            "Ñice locatioñ",
            
            # Mixed scripts (should be sanitized appropriately)
            "Location 位置",
            "Место находки",
        ]
        
        for unicode_text in unicode_test_data:
            # Test text sanitization
            sanitized = TreasureDataValidator.sanitize_text(unicode_text, 100)
            assert isinstance(sanitized, str), "Sanitized text should be string"
            assert len(sanitized) <= 100, "Should respect length limits"
            
            # Test in complete entry
            test_entry = {
                "Location": unicode_text,
                "Coordinates (Approximate)": "55°43'N, 9°08'E",
                "Treasure Value": "High",
                "Likelihood (%)": 85,
                "Recommended Reason": "Test Unicode handling",
                "Supporting Evidence": "Test evidence",
                "Supporting Evidence URLs": ["https://example.com"]
            }
            
            is_valid, sanitized_entry, errors = TreasureDataValidator.validate_treasure_entry(test_entry)
            assert is_valid, f"Should handle Unicode text: {unicode_text}"
    
    def test_regression_prevention(self):
        """Test cases to prevent regression of known issues."""
        
        # Test case 1: Ensure coordinate parsing doesn't break with edge whitespace
        whitespace_coordinates = [
            "  55°43'N,   9°08'E  ",
            "\t55°43'N, 9°08'E\n",
            "55°43'N,\t9°08'E",
        ]
        
        for coord in whitespace_coordinates:
            is_valid, lat, lon, message = TreasureDataValidator.validate_coordinates(coord)
            assert is_valid, f"Should handle whitespace in coordinates: '{coord}'"
            assert lat is not None and lon is not None
        
        # Test case 2: Ensure URL validation handles edge cases
        edge_case_urls = [
            "https://example.com/",  # Trailing slash
            "https://example.com",   # No trailing slash
            "https://sub.domain.example.com/path?param=value#fragment",  # Complex URL
        ]
        
        for url in edge_case_urls:
            is_valid, message = TreasureDataValidator.validate_url(url)
            # Should either be valid or have a clear reason for rejection
            assert is_valid or "Warning" in message or len(message) > 0
        
        # Test case 3: Ensure percentage handling is robust
        percentage_formats = [
            85,      # Integer
            85.5,    # Float
            "85",    # String integer
            "85.5",  # String float
            "85%",   # String with percentage
            "85.5%", # String float with percentage
        ]
        
        for pct in percentage_formats:
            test_entry = {
                "Location": "Test Location",
                "Coordinates (Approximate)": "55°43'N, 9°08'E",
                "Treasure Value": "High",
                "Likelihood (%)": pct,
                "Recommended Reason": "Test percentage handling",
                "Supporting Evidence": "Test evidence",
                "Supporting Evidence URLs": []
            }
            
            is_valid, sanitized, errors = TreasureDataValidator.validate_treasure_entry(test_entry)
            assert is_valid, f"Should handle percentage format: {pct} ({type(pct).__name__})"


if __name__ == "__main__":
    # Run the comprehensive tests
    pytest.main([__file__, "-v", "-x"])  # Stop on first failure for debugging
