#!/usr/bin/env python3
"""
Setup Online Supabase Schema

This script creates the necessary tables in the online Supabase database
based on the schema defined in setup_database.py
"""

import os
import sys
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(Y-%m-%d %H:%M:%S) - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OnlineSchemaSetup:
    def __init__(self):
        """Initialize the schema setup with online Supabase client."""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def create_tables(self):
        """Create all necessary tables in the online database."""
        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS floats (
                float_id TEXT PRIMARY KEY,
                wmo_id TEXT,
                project_name TEXT,
                pi_name TEXT,
                platform_type TEXT,
                deployment_date TIMESTAMP,
                last_update TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS cycles (
                cycle_id TEXT PRIMARY KEY,
                float_id TEXT REFERENCES floats(float_id),
                cycle_number INTEGER,
                profile_date TIMESTAMP,
                latitude REAL,
                longitude REAL,
                profile_type TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS profiles (
                profile_id TEXT PRIMARY KEY,
                cycle_id TEXT REFERENCES cycles(cycle_id),
                pressure REAL,
                temperature REAL,
                salinity REAL,
                depth REAL,
                quality_flag INTEGER
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                session_id TEXT,
                turn_index INTEGER,
                role TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                metadata JSONB,
                full_response JSONB,
                PRIMARY KEY (session_id, turn_index)
            )
            """
        ]
        
        for sql in tables_sql:
            try:
                result = self.supabase.rpc('exec_sql', {'sql': sql}).execute()
                logger.info(f"Successfully created table")
            except Exception as e:
                # Try direct SQL execution if RPC fails
                try:
                    response = self.supabase.postgrest.schema('public').query(sql)
                    logger.info(f"Table created via direct SQL")
                except Exception as e2:
                    logger.error(f"Error creating table: {e2}")
                    return False
        
        return True
    
    def setup_with_sql_function(self):
        """Setup tables using SQL function approach."""
        # First, create a function to execute raw SQL
        create_function_sql = """
        CREATE OR REPLACE FUNCTION exec_sql(sql text) RETURNS void AS $$
        BEGIN
            EXECUTE sql;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        try:
            # Create the exec function
            self.supabase.rpc('exec_sql', {'sql': create_function_sql}).execute()
            logger.info("Created exec_sql function")
        except Exception as e:
            logger.warning(f"Could not create exec_sql function: {e}")
        
        # Now create tables
        return self.create_tables()
    
    def verify_tables(self):
        """Verify that all tables were created successfully."""
        table_names = ['floats', 'cycles', 'profiles', 'chat_history']
        
        try:
            # Check if tables exist
            check_sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = ANY($1)
            """
            
            result = self.supabase.rpc('exec_sql', {'sql': check_sql}).execute()
            logger.info("Tables verified successfully")
            return True
            
        except Exception as e:
            # Fallback to simple query
            try:
                for table in table_names:
                    result = self.supabase.table(table).select('*').limit(1).execute()
                    logger.info(f"Table {table} accessible")
                return True
            except Exception as e2:
                logger.error(f"Error verifying tables: {e2}")
                return False

def main():
    """Main function to setup online schema."""
    try:
        setup = OnlineSchemaSetup()
        
        logger.info("Setting up online Supabase schema...")
        
        # Try to setup tables
        if setup.setup_with_sql_function():
            logger.info("✅ Schema setup completed successfully")
            
            if setup.verify_tables():
                logger.info("✅ All tables verified and ready for sync")
            else:
                logger.warning("⚠️ Some tables may not be accessible")
        else:
            logger.error("❌ Schema setup failed")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error during schema setup: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())