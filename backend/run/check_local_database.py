#!/usr/bin/env python3
"""
Analyze local Supabase database to show table information and row counts.
This script provides a quick overview of your local database contents.
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseAnalyzer:
    def __init__(self, database_url: str):
        """Initialize database analyzer with connection URL."""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        
    def get_all_tables(self) -> list:
        """Get list of all tables in the database."""
        try:
            with self.engine.connect() as conn:
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
            logger.error(f"Error getting table list: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> dict:
        """Get detailed information about a table."""
        try:
            with self.engine.connect() as conn:
                # Get row count
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.fetchone()[0]
                
                # Get column information
                columns_result = conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """))
                
                columns = []
                for row in columns_result.fetchall():
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'nullable': row[2],
                        'default': row[3]
                    })
                
                # Get table size (approximate)
                try:
                    size_result = conn.execute(text(f"""
                        SELECT pg_size_pretty(pg_total_relation_size('{table_name}'));
                    """))
                    table_size = size_result.fetchone()[0]
                except:
                    table_size = "Unknown"
                
                return {
                    'table_name': table_name,
                    'row_count': row_count,
                    'column_count': len(columns),
                    'columns': columns,
                    'table_size': table_size
                }
        except Exception as e:
            logger.error(f"Error getting info for {table_name}: {e}")
            return None
    
    def get_database_summary(self) -> dict:
        """Get comprehensive database summary."""
        tables = self.get_all_tables()
        if not tables:
            return {'error': 'No tables found'}
        
        summary = {
            'total_tables': len(tables),
            'tables': [],
            'total_rows': 0,
            'total_size': 0
        }
        
        for table_name in tables:
            info = self.get_table_info(table_name)
            if info:
                summary['tables'].append(info)
                summary['total_rows'] += info['row_count']
        
        return summary
    
    def print_database_report(self):
        """Print a formatted database report."""
        summary = self.get_database_summary()
        
        if 'error' in summary:
            print(f"❌ Error: {summary['error']}")
            return
        
        print("\n" + "="*60)
        print("LOCAL DATABASE ANALYSIS REPORT")
        print("="*60)
        print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Tables: {summary['total_tables']}")
        print(f"Total Rows: {summary['total_rows']:,}")
        print()
        
        print("TABLE BREAKDOWN:")
        print("-" * 60)
        
        for table_info in summary['tables']:
            print(f"📊 {table_info['table_name'].upper()}")
            print(f"   Rows: {table_info['row_count']:,}")
            print(f"   Columns: {table_info['column_count']}")
            print(f"   Size: {table_info['table_size']}")
            print(f"   Columns: {[col['name'] for col in table_info['columns'][:5]]}{'...' if len(table_info['columns']) > 5 else ''}")
            print()
        
        # Memory estimation for sync
        estimated_memory_mb = summary['total_rows'] * 0.001  # Rough estimate
        print("SYNC ESTIMATES:")
        print("-" * 60)
        print(f"Estimated memory needed: {estimated_memory_mb:.1f} MB")
        print(f"Recommended batch size: {min(1000, max(100, summary['total_rows'] // 100))}")
        print(f"Estimated sync time: {summary['total_rows'] // 1000} minutes (approx)")
        
        print("\n" + "="*60)

def main():
    """Main function to analyze local database."""
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set.")
        print("Please create a .env file with your local database URL.")
        print("Example: DATABASE_URL=postgresql://postgres:password@localhost:54322/postgres")
        return
    
    try:
        analyzer = DatabaseAnalyzer(database_url)
        analyzer.print_database_report()
        
        # Save report to file
        summary = analyzer.get_database_summary()
        with open('database_analysis.txt', 'w') as f:
            f.write(f"Local Database Analysis - {datetime.now()}\n")
            f.write("=" * 50 + "\n")
            for table_info in summary['tables']:
                f.write(f"{table_info['table_name']}: {table_info['row_count']} rows\n")
        
        print("✅ Analysis complete! Report saved to database_analysis.txt")
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")

if __name__ == "__main__":
    main()