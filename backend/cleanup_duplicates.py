"""
Cleanup script for FloatChat database duplicate profile records.
This script helps remove duplicate profile records that were causing unique constraint violations.
"""

import os
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_duplicate_profiles(database_url: str):
    """
    Clean up duplicate profile records from the database.
    
    Args:
        database_url: PostgreSQL connection URL
    """
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Start a transaction
            with connection.begin():
                logger.info("Starting cleanup of duplicate profile records...")
                
                # Count duplicates before cleanup
                count_query = text("""
                    SELECT profile_id, COUNT(*) as duplicate_count
                    FROM profiles 
                    GROUP BY profile_id 
                    HAVING COUNT(*) > 1
                """)
                duplicates = connection.execute(count_query).fetchall()
                
                if duplicates:
                    logger.warning(f"Found {len(duplicates)} profile IDs with duplicates")
                    for dup in duplicates:
                        logger.warning(f"Profile ID {dup[0]} has {dup[1]} duplicates")
                    
                    # Remove duplicates, keeping the most recent record based on some criteria
                    # For simplicity, we'll keep the first record and delete others
                    cleanup_query = text("""
                        DELETE FROM profiles 
                        WHERE ctid NOT IN (
                            SELECT MIN(ctid) 
                            FROM profiles 
                            GROUP BY profile_id
                        )
                    """)
                    
                    result = connection.execute(cleanup_query)
                    logger.info(f"Removed {result.rowcount} duplicate profile records")
                else:
                    logger.info("No duplicate profile records found")
                
                # Also clean up any profiles with 'unknown_' prefix that might be problematic
                unknown_cleanup_query = text("""
                    DELETE FROM profiles 
                    WHERE profile_id LIKE 'unknown_%'
                """)
                
                unknown_result = connection.execute(unknown_cleanup_query)
                if unknown_result.rowcount > 0:
                    logger.info(f"Removed {unknown_result.rowcount} profiles with 'unknown_' prefix")
                
                logger.info("Cleanup completed successfully")
                
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise

def main():
    """
    Main function to run the cleanup.
    """
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable not set. Please create a .env file.")
        return
    
    print("WARNING: This script will remove duplicate profile records from the database.")
    print("Make sure you have a backup before proceeding.")
    confirmation = input("Do you want to continue? (yes/no): ")
    
    if confirmation.lower() == 'yes':
        cleanup_duplicate_profiles(DATABASE_URL)
    else:
        logger.info("Cleanup cancelled by user.")

if __name__ == "__main__":
    main()