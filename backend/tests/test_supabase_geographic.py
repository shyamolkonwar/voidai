#!/usr/bin/env python3
"""
Test script to verify geographic queries work with Supabase PostgreSQL
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add src to path for imports
sys.path.append('/Users/shyamolkonwar/Documents/VOID/VOID_1/backend/src')
from geocoding_service import GeographicService

def test_supabase_connection():
    """Test connection to Supabase and run sample geographic queries"""
    load_dotenv()
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not found in environment")
        return
    
    try:
        # Create engine and test connection
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("✓ Successfully connected to Supabase PostgreSQL")
            
            # Test basic table existence
            result = conn.execute(text("SELECT COUNT(*) FROM cycles"))
            cycle_count = result.scalar()
            print(f"✓ Found {cycle_count} cycles in database")
            
            # Test coordinate ranges
            result = conn.execute(text("""
                SELECT MIN(latitude) as min_lat, MAX(latitude) as max_lat,
                       MIN(longitude) as min_lon, MAX(longitude) as max_lon
                FROM cycles
            """))
            ranges = result.fetchone()
            print(f"✓ Coordinate ranges: Lat {ranges.min_lat:.2f} to {ranges.max_lat:.2f}, "
                  f"Lon {ranges.min_lon:.2f} to {ranges.max_lon:.2f}")
            
            # Test Mumbai query
            geo_service = GeographicService()
            mumbai_query = "Show me temperature measurements near Mumbai"
            
            _, location_context = geo_service.enhance_query_with_location(mumbai_query)
            if location_context:
                print("\n✓ Location context generated for Mumbai")
                
                # Extract the SQL from context
                import re
                sql_match = re.search(r'SELECT.*?;', location_context, re.DOTALL)
                if sql_match:
                    sql_query = sql_match.group(0)
                    
                    # Execute the query
                    result = conn.execute(text(sql_query))
                    rows = result.fetchall()
                    print(f"✓ Mumbai query returned {len(rows)} rows")
                    
                    if rows:
                        print("Sample results:")
                        for i, row in enumerate(rows[:3]):
                            print(f"  {i+1}: Temp {row.temperature}°C, "
                                  f"Lat {row.latitude:.2f}, Lon {row.longitude:.2f}, "
                                  f"Distance {row.distance_km:.1f}km")
                    else:
                        print("  No results found - checking broader area...")
                        
                        # Try broader query
                        broader_query = """
                        SELECT p.temperature, c.latitude, c.longitude, c.profile_date,
                               (
                                   6371 * acos(
                                       cos(radians(19.076)) * cos(radians(c.latitude)) *
                                       cos(radians(c.longitude) - radians(72.8777)) +
                                       sin(radians(19.076)) * sin(radians(c.latitude))
                                   )
                               ) AS distance_km
                        FROM profiles p
                        JOIN cycles c ON p.cycle_id = c.cycle_id
                        WHERE p.temperature IS NOT NULL
                        AND p.quality_flag IN (1, 2)
                        ORDER BY distance_km ASC
                        LIMIT 5
                        """
                        result = conn.execute(text(broader_query))
                        rows = result.fetchall()
                        print(f"  Broader query returned {len(rows)} rows")
                        
            else:
                print("✗ No location context generated")
                
    except Exception as e:
        print(f"✗ Error testing Supabase: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing Supabase PostgreSQL geographic queries...")
    test_supabase_connection()