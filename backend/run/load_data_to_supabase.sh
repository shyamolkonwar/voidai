#!/bin/bash

# Profiles data loading script for Supabase online
# This script loads only the profiles CSV data into Supabase using PostgreSQL COPY command

echo "Starting profiles data loading to Supabase online..."
echo "Host: db.neglevcqccbwbzwdkxxf.supabase.co"
echo "Database: postgres"

# Check if required files exist
EXPORTED_DIR="./exported_data"
if [ ! -d "$EXPORTED_DIR" ]; then
    echo "Error: exported_data directory not found"
    exit 1
fi

# Check if profiles CSV file exists
PROFILES_FILE=$(ls -t "$EXPORTED_DIR"/profiles_*.csv 2>/dev/null | head -n 1)
if [ -z "$PROFILES_FILE" ]; then
    echo "Error: No profiles CSV file found in exported_data directory"
    exit 1
fi

echo "Found profiles file: $PROFILES_FILE"
echo "File size: $(stat -f%z "$PROFILES_FILE" | awk '{print $1/1024/1024 " MB"}')"

# Check Python dependencies
if ! python3 -c "import psycopg2" 2>/dev/null; then
    echo "Installing psycopg2..."
    pip3 install psycopg2-binary
fi

# Run the profiles loading script
echo "Running profiles data loader..."
python3 load_profiles_to_supabase.py

echo "Profiles data loading completed!"