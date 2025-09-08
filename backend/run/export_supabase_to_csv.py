#!/usr/bin/env python3
"""
Export all data from Supabase (local) database to CSV files.
This script fetches all rows from all tables and saves them as CSV files.
"""

import os
import csv
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseExporter:
    def __init__(self, database_url):
        """Initialize the exporter with database connection."""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.output_dir = "exported_data"
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_all_tables(self):
        """Get list of all tables in the database."""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """))
                tables = [row[0] for row in result.fetchall()]
                return tables
        except Exception as e:
            logger.error(f"Error getting table list: {e}")
            return []
    
    def export_table_to_csv(self, table_name):
        """Export a single table to CSV file."""
        try:
            logger.info(f"Exporting table: {table_name}")
            
            # Read all data from the table
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, self.engine)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_{timestamp}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            # Save to CSV
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            logger.info(f"Exported {len(df)} rows from {table_name} to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting table {table_name}: {e}")
            return None
    
    def export_all_tables(self):
        """Export all tables to CSV files."""
        tables = self.get_all_tables()
        
        if not tables:
            logger.warning("No tables found in database")
            return []
        
        exported_files = []
        
        for table in tables:
            filepath = self.export_table_to_csv(table)
            if filepath:
                exported_files.append(filepath)
        
        return exported_files
    
    def export_specific_tables(self, table_names):
        """Export specific tables to CSV files."""
        exported_files = []
        
        for table_name in table_names:
            filepath = self.export_table_to_csv(table_name)
            if filepath:
                exported_files.append(filepath)
        
        return exported_files
    
    def get_table_info(self, table_name):
        """Get information about a table including column names and types."""
        try:
            with self.engine.connect() as connection:
                # Get column information
                result = connection.execute(text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """))
                
                columns_info = []
                for row in result.fetchall():
                    columns_info.append({
                        'column_name': row[0],
                        'data_type': row[1],
                        'is_nullable': row[2],
                        'column_default': row[3]
                    })
                
                # Get row count
                count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.fetchone()[0]
                
                return {
                    'table_name': table_name,
                    'columns': columns_info,
                    'row_count': row_count
                }
                
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return None

def main():
    """Main function to run the export process."""
    load_dotenv()
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        logger.error("DATABASE_URL environment variable not set. Please create a .env file.")
        return
    
    try:
        # Initialize exporter
        exporter = SupabaseExporter(database_url)
        
        # Export all tables
        logger.info("Starting database export...")
        exported_files = exporter.export_all_tables()
        
        if exported_files:
            logger.info(f"Successfully exported {len(exported_files)} files:")
            for file in exported_files:
                logger.info(f"  - {file}")
        else:
            logger.warning("No files were exported")
            
        # Show table information
        tables = exporter.get_all_tables()
        logger.info("\nTable Information:")
        for table in tables:
            info = exporter.get_table_info(table)
            if info:
                logger.info(f"  {info['table_name']}: {info['row_count']} rows, {len(info['columns'])} columns")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")

if __name__ == "__main__":
    main()