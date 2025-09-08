"""
Configuration file for Supabase sync operations.
Customize these parameters based on your data size and requirements.
"""

import os
from typing import List, Optional

class SyncConfig:
    """Configuration class for Supabase sync operations."""
    
    def __init__(self):
        # Database connections
        self.local_db_url = os.getenv("DATABASE_URL", "")
        self.online_supabase_url = "https://hxnnvfykvdhllwrgtjtg.supabase.co"
        self.online_service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh4bm52ZnlrdmRobGx3cmd0anRnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzE4Mzg4NywiZXhwIjoyMDcyNzU5ODg3fQ.Lq8twbeSAFqaRQMjBhAi_uqgGVPuNiTK7j3XB1_xgfY"
        
        # Performance settings - optimized for big data (4M+ rows)
        self.batch_size = int(os.getenv("SYNC_BATCH_SIZE", "500"))  # Reduced for big data
        self.delay_between_batches = float(os.getenv("SYNC_DELAY", "0.5"))  # Increased delay
        self.max_retries = int(os.getenv("SYNC_MAX_RETRIES", "5"))  # More retries for reliability
        
        # Table selection
        self.include_tables: Optional[List[str]] = None  # None = all tables
        self.exclude_tables: List[str] = [
            # Add tables to exclude here
            # "spatial_ref_sys",  # PostGIS system table
            # "pg_stat_statements",  # PostgreSQL stats
        ]
        
        # Data filtering
        self.where_conditions: dict = {}  # Table-specific WHERE clauses
        # Example: {"profiles": "quality_flag = 1"}
        
        # Sync behavior
        self.clear_before_sync = True  # Clear online tables before sync
        self.verify_schema = True  # Verify schema compatibility
        self.generate_report = True  # Generate detailed sync report
        
        # Logging
        self.log_level = os.getenv("SYNC_LOG_LEVEL", "INFO")
        self.log_file = "sync_supabase.log"
        self.report_file = "sync_report.txt"
    
    def get_table_config(self, table_name: str) -> dict:
        """Get configuration for specific table."""
        return {
            'batch_size': self.batch_size,
            'clear_before_sync': self.clear_before_sync,
            'where_clause': self.where_conditions.get(table_name, None),
            'max_retries': self.max_retries
        }
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.local_db_url:
            errors.append("DATABASE_URL environment variable is required")
        
        if not self.online_supabase_url:
            errors.append("Online Supabase URL is required")
        
        if not self.online_service_role_key:
            errors.append("Online Supabase service role key is required")
        
        if self.batch_size <= 0:
            errors.append("Batch size must be positive")
        
        if self.batch_size > 10000:
            errors.append("Batch size too large (max 10000)")
        
        return errors
    
    def print_config(self):
        """Print current configuration."""
        print("Supabase Sync Configuration")
        print("=" * 40)
        print(f"Local DB URL: {self.local_db_url}")
        print(f"Online Supabase URL: {self.online_supabase_url}")
        print(f"Batch Size: {self.batch_size}")
        print(f"Delay Between Batches: {self.delay_between_batches}s")
        print(f"Max Retries: {self.max_retries}")
        print(f"Clear Before Sync: {self.clear_before_sync}")
        print(f"Verify Schema: {self.verify_schema}")
        print(f"Include Tables: {self.include_tables or 'All'}")
        print(f"Exclude Tables: {self.exclude_tables}")
        print(f"Log Level: {self.log_level}")
        print(f"Log File: {self.log_file}")

# Create default configuration instance
config = SyncConfig()

# Example usage:
if __name__ == "__main__":
    config.print_config()
    errors = config.validate_config()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")