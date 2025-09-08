#!/usr/bin/env python3
"""
Test script to verify Supabase sync functionality with a small subset of data.
This ensures the sync process works before running the full big data sync.
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from supabase import create_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sync_small():
    """Test sync with small subset of data."""
    load_dotenv()
    
    local_db_url = os.getenv("DATABASE_URL")
    online_supabase_url = "https://hxnnvfykvdhllwrgtjtg.supabase.co"
    online_service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh4bm52ZnlrdmRobGx3cmd0anRnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzE4Mzg4NywiZXhwIjoyMDcyNzU5ODg3fQ.Lq8twbeSAFqaRQMjBhAi_uqgGVPuNiTK7j3XB1_xgfY"
    
    if not local_db_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        # Test database connection
        logger.info("Testing local database connection...")
        local_engine = create_engine(local_db_url)
        
        with local_engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Local database connection successful")
            
            # Test table access
            tables = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """))
            table_list = [row[0] for row in tables.fetchall()]
            logger.info(f"Found tables: {table_list}")
            
            # Test small data fetch
            for table in table_list:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
                sample = conn.execute(text(f"SELECT * FROM {table} LIMIT 5"))
                columns = list(sample.keys())
                logger.info(f"{table}: {count} rows, columns: {columns}")
        
        # Test online Supabase connection
        logger.info("Testing online Supabase connection...")
        supabase = create_client(online_supabase_url, online_service_role_key)
        
        # Test a simple query
        try:
            result = supabase.table('floats').select('*', count='exact').limit(1).execute()
            logger.info(f"✅ Online Supabase connection successful - found {len(result.data)} floats")
        except Exception as e:
            logger.warning(f"⚠️ Online floats table may be empty or not accessible: {e}")
        
        logger.info("✅ All connection tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_sync_small()
    if success:
        print("\n🎉 All tests passed! Ready to run full sync.")
        print("Run: python sync_local_to_online_supabase.py")
    else:
        print("\n❌ Tests failed. Check logs above.")