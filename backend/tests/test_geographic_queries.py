#!/usr/bin/env python3
"""
Debug script to test geographic queries against ARGO database
"""

import sqlite3
import math
from typing import List, Tuple

def test_coordinate_ranges():
    """Test what coordinate ranges exist in the database"""
    conn = sqlite3.connect('/Users/shyamolkonwar/Documents/VOID/VOID_1/backend/data/argo_data.db')
    cursor = conn.cursor()
    
    # Get min/max coordinates
    cursor.execute("SELECT MIN(latitude), MAX(latitude), MIN(longitude), MAX(longitude) FROM cycles")
    lat_min, lat_max, lon_min, lon_max = cursor.fetchone()
    
    print(f"Database coordinate ranges:")
    print(f"Latitude: {lat_min:.2f} to {lat_max:.2f}")
    print(f"Longitude: {lon_min:.2f} to {lon_max:.2f}")
    
    # Test specific locations
    test_locations = [
        ("Mumbai", 19.0760, 72.8777),
        ("Indian Ocean", -10.0, 90.0),
        ("Tropical Pacific", 5.0, -170.0),
        ("North Atlantic", 45.0, -35.0),
    ]
    
    for name, lat, lon in test_locations:
        print(f"\nTesting {name} ({lat}, {lon}):")
        
        # Test with 500km radius
        radius_km = 500
        lat_range = radius_km / 111.32
        lon_range = radius_km / (111.32 * abs(math.cos(math.radians(lat))))
        
        query = """
        SELECT COUNT(*) as count, 
               MIN(c.latitude) as min_lat, MAX(c.latitude) as max_lat,
               MIN(c.longitude) as min_lon, MAX(c.longitude) as max_lon
        FROM cycles c
        WHERE c.latitude BETWEEN ? AND ?
        AND c.longitude BETWEEN ? AND ?
        """
        
        cursor.execute(query, [
            lat - lat_range, lat + lat_range,
            lon - lon_range, lon + lon_range
        ])
        
        count, min_lat, max_lat, min_lon, max_lon = cursor.fetchone()
        print(f"  Count: {count}")
        print(f"  Lat range: {min_lat:.2f} to {max_lat:.2f}")
        print(f"  Lon range: {min_lon:.2f} to {max_lon:.2f}")
        
        # Test Haversine formula
        haversine_query = """
        SELECT COUNT(*) as count,
               MIN((6371 * acos(cos(radians(?)) * cos(radians(c.latitude)) * 
                    cos(radians(c.longitude) - radians(?)) + 
                    sin(radians(?)) * sin(radians(c.latitude))))) as min_distance
        FROM cycles c
        WHERE (6371 * acos(cos(radians(?)) * cos(radians(c.latitude)) * 
               cos(radians(c.longitude) - radians(?)) + 
               sin(radians(?)) * sin(radians(c.latitude)))) <= ?
        """
        
        cursor.execute(haversine_query, [lat, lon, lat, lat, lon, lat, radius_km])
        h_count, h_min_distance = cursor.fetchone()
        print(f"  Haversine count: {h_count}")
        if h_count > 0:
            print(f"  Min distance: {h_min_distance:.2f} km")
    
    conn.close()

def test_sample_data():
    """Show sample data from the database"""
    conn = sqlite3.connect('/Users/shyamolkonwar/Documents/VOID/VOID_1/backend/data/argo_data.db')
    cursor = conn.cursor()
    
    print("\nSample data:")
    cursor.execute("""
    SELECT c.latitude, c.longitude, c.profile_date, p.temperature, p.depth
    FROM cycles c
    JOIN profiles p ON c.cycle_id = p.cycle_id
    WHERE p.temperature IS NOT NULL
    LIMIT 10
    """)
    
    for lat, lon, date, temp, depth in cursor.fetchall():
        print(f"  Lat: {lat:.2f}, Lon: {lon:.2f}, Temp: {temp:.2f}°C, Depth: {depth}m, Date: {date}")
    
    conn.close()

if __name__ == "__main__":
    print("Testing geographic queries against ARGO database...")
    test_coordinate_ranges()
    test_sample_data()