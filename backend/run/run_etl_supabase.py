import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.etl_pipeline import ARGOETLPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_etl_supabase():
    """
    Initializes and runs the full ETL pipeline using Supabase online.
    """
    load_dotenv()
    
    # Use Supabase online configuration from environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
        return
    
    # Construct PostgreSQL connection URL from Supabase credentials
    # Parse the Supabase URL to get the correct connection details
    # Extract host from SUPABASE_URL: https://[project-ref].supabase.co -> [project-ref].supabase.co
    supabase_host = supabase_url.replace('https://', '').rstrip('/')
    SUPABASE_DATABASE_URL = f"postgresql://postgres:{supabase_key}@db.{supabase_host}:5432/postgres"

    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
    NETCDF_DIRECTORY = "../data/netcdf"
    
    # Create directory if it doesn't exist
    os.makedirs(NETCDF_DIRECTORY, exist_ok=True)
    
    # Check if directory has any NetCDF files
    if not os.path.exists(NETCDF_DIRECTORY):
        logger.error(f"Directory {NETCDF_DIRECTORY} does not exist")
        return
    
    netcdf_files = []
    for root, dirs, files in os.walk(NETCDF_DIRECTORY):
        for file in files:
            if file.endswith('.nc'):
                netcdf_files.append(os.path.join(root, file))
    
    if not netcdf_files:
        logger.warning(f"No NetCDF (.nc) files found in {NETCDF_DIRECTORY}")
        logger.info("Please add NetCDF files to the ./data/netcdf directory to process data")
        return

    logger.info("Starting ETL pipeline for Supabase online...")
    logger.info(f"Target Supabase database: {supabase_url}")
    logger.info(f"Source NetCDF directory: {NETCDF_DIRECTORY}")

    try:
        pipeline = ARGOETLPipeline(
            db_url=SUPABASE_DATABASE_URL,
            chroma_host=CHROMA_HOST,
            chroma_port=CHROMA_PORT
        )
        
        results = pipeline.run_etl_pipeline(NETCDF_DIRECTORY)
        logger.info(f"ETL run completed for Supabase online. Results: {results}")

    except Exception as e:
        logger.error(f"An error occurred during the ETL pipeline run on Supabase: {e}")

if __name__ == "__main__":
    run_etl_supabase()