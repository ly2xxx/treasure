import json
import re
import urllib.parse
from typing import Dict, List, Optional, Tuple, Any


class TreasureDataValidator:
    """Security-focused validator for treasure location data."""
    
    # Denmark coordinate boundaries for validation
    DENMARK_LAT_MIN = 54.5
    DENMARK_LAT_MAX = 57.5  
    DENMARK_LON_MIN = 8.0
    DENMARK_LON_MAX = 15.5
    
    # Maximum lengths for text fields to prevent DoS
    MAX_LOCATION_LENGTH = 200
    MAX_REASON_LENGTH = 1000
    MAX_EVIDENCE_LENGTH = 2000
    MAX_URL_LENGTH = 500
    MAX_URLS_PER_LOCATION = 10
    
    # Allowed URL schemes for security
    ALLOWED_URL_SCHEMES = {'https', 'http'}
    
    # Trusted domains for treasure-related URLs
    TRUSTED_DOMAINS = {
        'livescience.com',
        'ancient-origins.net', 
        'archaeology.org',
        'vejlemuseerne.dk',
        'bornholmarch.eu',
        'bornholmsmuseum.dk',
        'scientificamerican.com',
        'thevikingherald.com',
        'en.wikipedia.org',
        'unesco.org',
        'nationalmuseum.dk'
    }
    
    @staticmethod
    def sanitize_text(text: str, max_length: int) -> str:
        """Sanitize text input to prevent XSS and limit length."""
        if not isinstance(text, str):
            text = str(text)
        
        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\']', '', text)
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length] + '...'
        
        # Strip whitespace
        return text.strip()
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """Validate URL for security and format."""
        if not isinstance(url, str):
            return False, "URL must be a string"
        
        if len(url) > TreasureDataValidator.MAX_URL_LENGTH:
            return False, f"URL too long (max {TreasureDataValidator.MAX_URL_LENGTH} chars)"
        
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Check scheme
            if parsed.scheme not in TreasureDataValidator.ALLOWED_URL_SCHEMES:
                return False, f"Invalid URL scheme: {parsed.scheme}"
            
            # Check domain exists
            if not parsed.netloc:
                return False, "Missing domain in URL"
            
            # Check for potentially malicious patterns
            if any(pattern in url.lower() for pattern in ['javascript:', 'data:', 'vbscript:', 'file:']):
                return False, "Potentially malicious URL scheme detected"
            
            # Warn about untrusted domains (but don't reject)
            domain = parsed.netloc.lower()
            if not any(trusted in domain for trusted in TreasureDataValidator.TRUSTED_DOMAINS):
                return True, f"Warning: Untrusted domain {domain}"
            
            return True, "Valid URL"
            
        except Exception as e:
            return False, f"URL parsing error: {str(e)}"
    
    @staticmethod
    def validate_coordinates(coord_str: str) -> Tuple[bool, Optional[float], Optional[float], str]:
        """Validate and parse coordinates with Denmark-specific checks."""
        try:
            # Use the existing coordinate parsing logic
            from app import parse_coordinates
            lat, lon = parse_coordinates(coord_str)
            
            if lat is None or lon is None:
                return False, None, None, "Failed to parse coordinates"
            
            # Check if coordinates are within Denmark boundaries
            if not (TreasureDataValidator.DENMARK_LAT_MIN <= lat <= TreasureDataValidator.DENMARK_LAT_MAX):
                return False, lat, lon, f"Latitude {lat} outside Denmark bounds"
            
            if not (TreasureDataValidator.DENMARK_LON_MIN <= lon <= TreasureDataValidator.DENMARK_LON_MAX):
                return False, lat, lon, f"Longitude {lon} outside Denmark bounds"
            
            return True, lat, lon, "Valid coordinates"
            
        except Exception as e:
            return False, None, None, f"Coordinate validation error: {str(e)}"
    
    @staticmethod
    def validate_treasure_entry(entry: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
        """Validate and sanitize a complete treasure entry."""
        errors = []
        sanitized_entry = {}
        
        # Required fields
        required_fields = [
            "Location",
            "Coordinates (Approximate)",
            "Treasure Value", 
            "Likelihood (%)",
            "Recommended Reason",
            "Supporting Evidence",
            "Supporting Evidence URLs"
        ]
        
        # Check for required fields
        for field in required_fields:
            if field not in entry:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, {}, errors
        
        # Validate and sanitize Location
        location = TreasureDataValidator.sanitize_text(
            entry["Location"], 
            TreasureDataValidator.MAX_LOCATION_LENGTH
        )
        if not location:
            errors.append("Location cannot be empty")
        sanitized_entry["Location"] = location
        
        # Validate coordinates
        coord_valid, lat, lon, coord_msg = TreasureDataValidator.validate_coordinates(
            entry["Coordinates (Approximate)"]
        )
        if not coord_valid:
            errors.append(f"Invalid coordinates: {coord_msg}")
        sanitized_entry["Coordinates (Approximate)"] = entry["Coordinates (Approximate)"]
        
        # Validate Treasure Value
        valid_treasure_values = {"High", "Exceptional", "Priceless", "Medium", "Low", "Unknown"}
        treasure_value = str(entry["Treasure Value"]).strip()
        if treasure_value not in valid_treasure_values:
            errors.append(f"Invalid treasure value: {treasure_value}")
        sanitized_entry["Treasure Value"] = treasure_value
        
        # Validate Likelihood percentage
        try:
            likelihood = entry["Likelihood (%)"]
            if isinstance(likelihood, str):
                likelihood = float(likelihood.strip('%'))
            likelihood = float(likelihood)
            if not (0 <= likelihood <= 100):
                errors.append("Likelihood must be between 0 and 100")
            sanitized_entry["Likelihood (%)"] = likelihood
        except (ValueError, TypeError):
            errors.append("Invalid likelihood percentage format")
        
        # Sanitize text fields
        sanitized_entry["Recommended Reason"] = TreasureDataValidator.sanitize_text(
            entry["Recommended Reason"],
            TreasureDataValidator.MAX_REASON_LENGTH
        )
        
        sanitized_entry["Supporting Evidence"] = TreasureDataValidator.sanitize_text(
            entry["Supporting Evidence"],
            TreasureDataValidator.MAX_EVIDENCE_LENGTH
        )
        
        # Validate URLs
        urls = entry.get("Supporting Evidence URLs", [])
        if not isinstance(urls, list):
            errors.append("Supporting Evidence URLs must be a list")
        elif len(urls) > TreasureDataValidator.MAX_URLS_PER_LOCATION:
            errors.append(f"Too many URLs (max {TreasureDataValidator.MAX_URLS_PER_LOCATION})")
        else:
            validated_urls = []
            for url in urls:
                url_valid, url_msg = TreasureDataValidator.validate_url(url)
                if url_valid:
                    validated_urls.append(url)
                    if "Warning" in url_msg:
                        errors.append(url_msg)  # Add warning but don't fail
                else:
                    errors.append(f"Invalid URL '{url}': {url_msg}")
            
            sanitized_entry["Supporting Evidence URLs"] = validated_urls
        
        # Return success if no critical errors
        is_valid = len([e for e in errors if not e.startswith("Warning")]) == 0
        return is_valid, sanitized_entry, errors
    
    @staticmethod
    def validate_json_file(file_path: str) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
        """Validate an entire JSON file containing treasure locations."""
        errors = []
        validated_entries = []
        
        try:
            # Secure file path validation
            if '..' in file_path or file_path.startswith('/'):
                errors.append("Invalid file path detected")
                return False, [], errors
            
            with open(file_path, 'r', encoding='utf-8') as f:
                # Limit file size to prevent DoS
                content = f.read(1024 * 1024)  # 1MB limit
                if len(f.read(1)) > 0:  # Check if there's more content
                    errors.append("File too large (max 1MB)")
                    return False, [], errors
                
                f.seek(0)
                data = json.load(f)
        
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {str(e)}")
            return False, [], errors
        except FileNotFoundError:
            errors.append(f"File not found: {file_path}")
            return False, [], errors
        except Exception as e:
            errors.append(f"File reading error: {str(e)}")
            return False, [], errors
        
        # Validate data structure
        if not isinstance(data, list):
            errors.append("JSON root must be an array of treasure locations")
            return False, [], errors
        
        if len(data) == 0:
            errors.append("JSON file contains no treasure locations")
            return False, [], errors
        
        if len(data) > 50:  # Reasonable limit
            errors.append("Too many treasure locations in file (max 50)")
            return False, [], errors
        
        # Validate each entry
        for i, entry in enumerate(data):
            if not isinstance(entry, dict):
                errors.append(f"Entry {i} must be an object")
                continue
            
            entry_valid, sanitized_entry, entry_errors = TreasureDataValidator.validate_treasure_entry(entry)
            
            if entry_valid:
                validated_entries.append(sanitized_entry)
            
            # Add entry-specific errors with context
            for error in entry_errors:
                errors.append(f"Entry {i} ({entry.get('Location', 'Unknown')}): {error}")
        
        # Consider file valid if at least one entry is valid
        is_valid = len(validated_entries) > 0
        return is_valid, validated_entries, errors


def secure_load_treasure_data(file_path: str):
    """Securely load and validate treasure data from JSON file."""
    validator = TreasureDataValidator()
    is_valid, validated_data, errors = validator.validate_json_file(file_path)
    
    # Log errors/warnings
    for error in errors:
        if error.startswith("Warning"):
            print(f"WARNING: {error}")
        else:
            print(f"ERROR: {error}")
    
    if not is_valid:
        raise ValueError(f"Invalid treasure data file: {file_path}")
    
    return validated_data
