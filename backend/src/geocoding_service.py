"""
Geographic Intelligence Service for FloatChat
Handles location name to coordinate conversion and proximity queries
"""

import requests
import logging
from typing import Dict, Optional, Tuple
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LocationInfo:
    name: str
    latitude: float
    longitude: float
    country: str = None

class GeographicService:
    """
    Service to convert location names to coordinates and generate proximity queries
    """
    
    # Major oceanographic locations (pre-populated for common queries)
    # Coordinates based on actual ARGO float deployment areas
    OCEANOGRAPHIC_LOCATIONS = {
        'mumbai': LocationInfo('Mumbai', 19.0760, 72.8777, 'India'),
        'pacific': LocationInfo('Pacific Ocean', 15.0, -150.0, None),
        'atlantic': LocationInfo('Atlantic Ocean', 25.0, -40.0, None),
        'indian ocean': LocationInfo('Indian Ocean', -10.0, 90.0, None),
        'bay of bengal': LocationInfo('Bay of Bengal', 12.0, 88.0, 'India'),
        'arabian sea': LocationInfo('Arabian Sea', 14.0, 65.0, None),
        'gulf of mexico': LocationInfo('Gulf of Mexico', 26.0, -90.0, None),
        'mediterranean': LocationInfo('Mediterranean Sea', 35.0, 20.0, None),
        'north sea': LocationInfo('North Sea', 55.0, 3.0, None),
        'california': LocationInfo('California Coast', 35.0, -125.0, 'USA'),
        'alaska': LocationInfo('Alaska', 58.0, -150.0, 'USA'),
        'japan': LocationInfo('Japan', 35.0, 140.0, 'Japan'),
        'australia': LocationInfo('Australia', -20.0, 130.0, 'Australia'),
        'antarctica': LocationInfo('Antarctica', -65.0, 0.0, None),
        'greenland': LocationInfo('Greenland', 70.0, -40.0, 'Denmark'),
        # Additional ARGO deployment areas
        'hawaii': LocationInfo('Hawaii', 21.0, -157.0, 'USA'),
        'tropical pacific': LocationInfo('Tropical Pacific', 5.0, -170.0, None),
        'north atlantic': LocationInfo('North Atlantic', 45.0, -35.0, None),
        'south atlantic': LocationInfo('South Atlantic', -25.0, -15.0, None),
        'tropical indian': LocationInfo('Tropical Indian Ocean', -5.0, 80.0, None),
        'south pacific': LocationInfo('South Pacific', -25.0, -170.0, None),
    }
    
    def __init__(self, use_external_geocoding=True):
        self.use_external_geocoding = use_external_geocoding
    
    def get_location_coordinates(self, location_name: str) -> Optional[LocationInfo]:
        """
        Convert location name to coordinates
        """
        location_lower = location_name.lower().strip()
        
        # Check pre-populated locations first
        if location_lower in self.OCEANOGRAPHIC_LOCATIONS:
            return self.OCEANOGRAPHIC_LOCATIONS[location_lower]
        
        # Try external geocoding service (OpenStreetMap Nominatim - free)
        if self.use_external_geocoding:
            return self._geocode_external(location_name)
        
        return None
    
    def _geocode_external(self, location_name: str) -> Optional[LocationInfo]:
        """
        Use external geocoding service (Nominatim - free)
        """
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': location_name,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            headers = {
                'User-Agent': 'FloatChat/1.0 (oceanographic research)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                results = response.json()
                if results:
                    result = results[0]
                    return LocationInfo(
                        name=result.get('display_name', location_name),
                        latitude=float(result['lat']),
                        longitude=float(result['lon']),
                        country=result.get('address', {}).get('country')
                    )
        except Exception as e:
            logger.warning(f"External geocoding failed for '{location_name}': {e}")
        
        return None
    
    def generate_proximity_sql_condition(self, location: LocationInfo,
                                       radius_km: float = 500) -> str:
        """
        Generate SQL WHERE condition for proximity search
        Uses Haversine formula for distance calculation (PostgreSQL compatible)
        """
        sql_condition = f"""
        (
            6371 * acos(
                cos(radians({location.latitude})) *
                cos(radians(cycles.latitude)) *
                cos(radians(cycles.longitude) - radians({location.longitude})) +
                sin(radians({location.latitude})) *
                sin(radians(cycles.latitude))
            )
        ) <= {radius_km}
        """
        
        return sql_condition.strip()
    
    def enhance_query_with_location(self, user_query: str) -> Tuple[str, Optional[str]]:
        """
        Analyze user query for location references and return enhanced context
        """
        # Common location patterns
        location_patterns = [
            'near', 'around', 'close to', 'in', 'off', 'by', 'at'
        ]

        enhanced_context = None
        query_lower = user_query.lower()

        # Look for location references in query
        for location_name, location_info in self.OCEANOGRAPHIC_LOCATIONS.items():
            if location_name in query_lower:
                proximity_condition = self.generate_proximity_sql_condition(location_info)
                
                # Calculate bounding box for debugging
                lat_range = 500 / 111.32  # 1 degree latitude ≈ 111.32 km
                lon_range = 500 / (111.32 * abs(math.cos(math.radians(location_info.latitude))))
                
                enhanced_context = f"""
LOCATION CONTEXT DETECTED:
User mentioned: {location_name}
Coordinates: {location_info.latitude}°N, {location_info.longitude}°E
SQL proximity condition for within 500km:
{proximity_condition}

Bounding box for debugging:
Latitude range: {location_info.latitude - lat_range:.2f} to {location_info.latitude + lat_range:.2f}
Longitude range: {location_info.longitude - lon_range:.2f} to {location_info.longitude + lon_range:.2f}

Example location-aware query (PostgreSQL):
SELECT p.temperature, p.salinity, p.depth, c.latitude, c.longitude, c.profile_date,
       (
           6371 * acos(
               cos(radians({location_info.latitude})) * cos(radians(c.latitude)) *
               cos(radians(c.longitude) - radians({location_info.longitude})) +
               sin(radians({location_info.latitude})) * sin(radians(c.latitude))
           )
       ) AS distance_km
FROM profiles p
JOIN cycles c ON p.cycle_id = c.cycle_id
WHERE (
    6371 * acos(
        cos(radians({location_info.latitude})) * cos(radians(c.latitude)) *
        cos(radians(c.longitude) - radians({location_info.longitude})) +
        sin(radians({location_info.latitude})) * sin(radians(c.latitude))
    )
) <= 500
AND p.temperature IS NOT NULL
AND p.quality_flag IN (1, 2)
ORDER BY distance_km ASC
LIMIT 20;
"""
                break

        return user_query, enhanced_context