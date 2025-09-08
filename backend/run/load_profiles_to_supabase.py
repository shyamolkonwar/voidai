#!/usr/bin/env python3
"""
Profiles data loading script for Supabase online
Loads only the profiles CSV data into Supabase using batch processing to avoid timeouts
"""

import os
import sys
import psycopg2
import logging
import glob
import csv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase connection details
SUPABASE_HOST = "db.neglevcqccbwbzwdkxxf.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DATABASE = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "Katala@123"

# Directory containing exported CSV files
EXPORTED_DATA_DIR = "./exported_data"
BATCH_SIZE = 50000  # Process 50k records at a time

def get_connection():
    """Create connection to Supabase PostgreSQL database with extended timeout."""
    try:
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            database=SUPABASE_DATABASE,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            connect_timeout=300,
            options='-c statement_timeout=0'
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

def load_profiles_data():
    """Load profiles data from exported CSV files into Supabase using batch processing."""
    
    # Get exported data directory
    exported_dir = os.path.join(os.path.dirname(__file__), "exported_data")
    
    if not os.path.exists(exported_dir):
        logger.error(f"Exported data directory not found: {exported_dir}")
        return
    
    # Find profiles CSV file
    profiles_files = glob.glob(os.path.join(exported_dir, "profiles_*.csv"))
    if not profiles_files:
        logger.error("No profiles CSV file found in exported_data directory")
        return
    
    profiles_file = profiles_files[0]
    logger.info(f"Loading profiles from: {profiles_file}")
    
    # Get file size for progress tracking
    file_size = os.path.getsize(profiles_file)
    logger.info(f"Profiles file size: {file_size:,} bytes")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Count total lines
        with open(profiles_file, 'r') as f:
            total_lines = sum(1 for line in f) - 1  # Subtract header
        logger.info(f"Total profiles records to load: {total_lines:,}")
        
        # Load data in batches using INSERT statements
        batch_count = 0
        total_loaded = 0
        
        with open(profiles_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            batch = []
            
            for row in reader:
                batch.append(row)
                
                if len(batch) >= BATCH_SIZE:
                    insert_batch(cursor, batch)
                    batch_count += 1
                    total_loaded += len(batch)
                    conn.commit()
                    logger.info(f"Loaded batch {batch_count}: {total_loaded:,} records")
                    batch = []
            
            # Insert remaining records
            if batch:
                insert_batch(cursor, batch)
                total_loaded += len(batch)
                conn.commit()
                logger.info(f"Loaded final batch: {total_loaded:,} records")
        
        # Get final count
        cursor.execute("SELECT COUNT(*) FROM profiles")
        final_count = cursor.fetchone()[0]
        logger.info(f"Final profiles records in database: {final_count:,}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading profiles data: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def insert_batch(cursor, batch):
    """Insert a batch of records into the profiles table."""
    
    insert_query = """
        INSERT INTO profiles (
            profile_id, cycle_id, pressure, temperature, salinity, depth, quality_flag
        )
        VALUES (
            %(profile_id)s, %(cycle_id)s, %(pressure)s, %(temperature)s, 
            %(salinity)s, %(depth)s, %(quality_flag)s
        )
        ON CONFLICT (profile_id) DO NOTHING
    """
    
    cursor.executemany(insert_query, batch)

def main():
    """Main function to load profiles data into Supabase."""
    logger.info("Starting profiles data loading to Supabase online...")
    
    try:
        load_profiles_data()
        logger.info("Profiles data successfully loaded to Supabase online!")
        
    except Exception as e:
        logger.error(f"Failed to load profiles data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()