#!/usr/bin/env python3
"""
Sync data from local Supabase database to online Supabase.
Handles big data with batch processing and error recovery.
"""

import os
import sys
import time
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
from supabase import create_client, Client
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_supabase.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BigDataSupabaseSync:
    def __init__(self, 
                 local_db_url: str,
                 online_supabase_url: str,
                 online_service_role_key: str,
                 batch_size: int = 1000):
        """
        Initialize the sync service.
        
        Args:
            local_db_url: Local PostgreSQL database URL
            online_supabase_url: Online Supabase project URL
            online_service_role_key: Service role key for online Supabase
            batch_size: Number of records to process in each batch
        """
        self.local_db_url = local_db_url
        self.online_supabase_url = online_supabase_url
        self.online_service_role_key = online_service_role_key
        self.batch_size = batch_size
        
        # Initialize connections
        self.local_engine = create_engine(local_db_url)
        self.supabase: Client = create_client(online_supabase_url, online_service_role_key)
        
        # Sync statistics
        self.sync_stats = {
            'tables_processed': 0,
            'total_records': 0,
            'success_count': 0,
            'error_count': 0,
            'start_time': None,
            'end_time': None
        }
        
    def get_local_tables(self) -> List[str]:
        """Get list of all tables in local database."""
        try:
            with self.local_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """))
                tables = [row[0] for row in result.fetchall()]
                return tables
        except Exception as e:
            logger.error(f"Error getting local tables: {e}")
            return []
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get total row count for a table."""
        try:
            with self.local_engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting row count for {table_name}: {e}")
            return 0
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table."""
        try:
            with self.local_engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """))
                
                columns = []
                for row in result.fetchall():
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'nullable': row[2] == 'YES',
                        'default': row[3]
                    })
                return columns
        except Exception as e:
            logger.error(f"Error getting columns for {table_name}: {e}")
            return []
    
    def get_table_primary_keys(self, table_name: str) -> List[str]:
        """Get primary key columns for a table."""
        try:
            with self.local_engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_name = '{table_name}'
                    AND tc.constraint_type = 'PRIMARY KEY';
                """))
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error getting primary keys for {table_name}: {e}")
            return []
    
    def fetch_batch(self, table_name: str, offset: int, limit: int) -> List[Dict[str, Any]]:
        """Fetch a batch of records from local database."""
        try:
            query = f"SELECT * FROM {table_name} ORDER BY 1 LIMIT {limit} OFFSET {offset}"
            df = pd.read_sql(query, self.local_engine)
            
            # Convert DataFrame to list of dictionaries
            records = df.to_dict('records')
            
            # Handle JSON columns and datetime serialization
            for record in records:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, (pd.Timestamp, datetime)):
                        record[key] = value.isoformat()
                    elif isinstance(value, dict):
                        record[key] = json.dumps(value)
            
            return records
        except Exception as e:
            logger.error(f"Error fetching batch from {table_name}: {e}")
            return []
    
    def clear_online_table(self, table_name: str) -> bool:
        """Clear all data from online table."""
        try:
            self.supabase.table(table_name).delete().neq('id', '').execute()
            logger.info(f"Cleared online table: {table_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing online table {table_name}: {e}")
            return False
    
    def batch_insert_online(self, table_name: str, records: List[Dict[str, Any]]) -> bool:
        """Insert batch of records into online Supabase."""
        try:
            if not records:
                return True
            
            # Use upsert to handle potential conflicts
            self.supabase.table(table_name).upsert(records).execute()
            return True
        except Exception as e:
            logger.error(f"Error inserting batch into {table_name}: {e}")
            return False
    
    def sync_table(self, table_name: str) -> bool:
        """Sync a single table from local to online."""
        try:
            logger.info(f"Starting sync for table: {table_name}")
            
            # Get table info
            total_rows = self.get_table_row_count(table_name)
            if total_rows == 0:
                logger.info(f"Table {table_name} is empty, skipping")
                return True
            
            columns = self.get_table_columns(table_name)
            primary_keys = self.get_table_primary_keys(table_name)
            
            logger.info(f"Table {table_name}: {total_rows} total rows, {len(columns)} columns")
            
            # Skip clearing for very large tables to avoid timeout issues
            if total_rows > 100000:
                logger.info(f"Large table detected ({total_rows} rows), skipping clear operation")
            else:
                if not self.clear_online_table(table_name):
                    logger.warning(f"Could not clear table {table_name}, continuing anyway")
            
            # Process in batches with progress tracking
            processed = 0
            offset = 0
            start_time = time.time()
            
            while processed < total_rows:
                batch = self.fetch_batch(table_name, offset, self.batch_size)
                if not batch:
                    break
                
                retry_count = 0
                while retry_count < 3:
                    if self.batch_insert_online(table_name, batch):
                        processed += len(batch)
                        elapsed = time.time() - start_time
                        rate = processed / elapsed if elapsed > 0 else 0
                        
                        if processed % (self.batch_size * 10) == 0 or processed == total_rows:
                            logger.info(f"Table {table_name}: {processed}/{total_rows} rows ({processed/total_rows*100:.1f}%) - {rate:.0f} rows/sec")
                        break
                    else:
                        retry_count += 1
                        logger.warning(f"Batch insert failed for {table_name}, retry {retry_count}/3")
                        time.sleep(2 ** retry_count)  # Exponential backoff
                
                if retry_count >= 3:
                    logger.error(f"Failed to insert batch after 3 retries for {table_name}")
                    return False
                
                offset += self.batch_size
                time.sleep(self.delay_between_batches)
            
            elapsed = time.time() - start_time
            self.sync_stats['tables_processed'] += 1
            self.sync_stats['total_records'] += total_rows
            logger.info(f"✅ Successfully synced {table_name}: {total_rows} records in {elapsed:.1f}s")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing table {table_name}: {e}")
            self.sync_stats['error_count'] += 1
            return False
    
    def sync_all_tables(self, exclude_tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """Sync all tables from local to online."""
        self.sync_stats['start_time'] = datetime.now()
        
        try:
            tables = self.get_local_tables()
            if not tables:
                logger.error("No tables found in local database")
                return self.sync_stats
            
            # Exclude specific tables if provided
            if exclude_tables:
                tables = [t for t in tables if t not in exclude_tables]
            
            logger.info(f"Found {len(tables)} tables to sync: {tables}")
            
            for table_name in tables:
                if self.sync_table(table_name):
                    self.sync_stats['success_count'] += 1
                else:
                    self.sync_stats['error_count'] += 1
            
            self.sync_stats['end_time'] = datetime.now()
            
            # Calculate duration
            duration = self.sync_stats['end_time'] - self.sync_stats['start_time']
            logger.info(f"Sync completed in {duration}")
            
            return self.sync_stats
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            self.sync_stats['end_time'] = datetime.now()
            return self.sync_stats
    
    def generate_sync_report(self) -> str:
        """Generate a detailed sync report."""
        report = f"""
Supabase Sync Report
===================
Start Time: {self.sync_stats['start_time']}
End Time: {self.sync_stats['end_time']}
Duration: {self.sync_stats['end_time'] - self.sync_stats['start_time'] if self.sync_stats['end_time'] else 'N/A'}

Summary:
- Tables Processed: {self.sync_stats['tables_processed']}
- Total Records: {self.sync_stats['total_records']}
- Successful Syncs: {self.sync_stats['success_count']}
- Failed Syncs: {self.sync_stats['error_count']}

Details:
- Success Rate: {(self.sync_stats['success_count'] / max(self.sync_stats['tables_processed'], 1)) * 100:.1f}%
- Average Records per Table: {self.sync_stats['total_records'] / max(self.sync_stats['tables_processed'], 1):.0f}
"""
        return report

def main():
    """Main function to run the sync process."""
    load_dotenv()
    
    # Get configuration from environment
    local_db_url = os.getenv("DATABASE_URL")
    online_supabase_url = "https://hxnnvfykvdhllwrgtjtg.supabase.co"
    online_service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh4bm52ZnlrdmRobGx3cmd0anRnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzE4Mzg4NywiZXhwIjoyMDcyNzU5ODg3fQ.Lq8twbeSAFqaRQMjBhAi_uqgGVPuNiTK7j3XB1_xgfY"
    
    if not local_db_url:
        logger.error("DATABASE_URL environment variable not set. Please create a .env file.")
        return
    
    try:
        # Initialize sync service
        sync_service = BigDataSupabaseSync(
            local_db_url=local_db_url,
            online_supabase_url=online_supabase_url,
            online_service_role_key=online_service_role_key,
            batch_size=1000  # Adjust based on your needs
        )
        
        # Run sync
        logger.info("Starting Supabase sync from local to online...")
        stats = sync_service.sync_all_tables()
        
        # Generate and display report
        report = sync_service.generate_sync_report()
        logger.info(report)
        
        # Save report to file
        with open('sync_report.txt', 'w') as f:
            f.write(report)
        
        logger.info("Sync process completed. Check sync_report.txt for details.")
        
    except Exception as e:
        logger.error(f"Sync process failed: {e}")

if __name__ == "__main__":
    main()