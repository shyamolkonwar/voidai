
import os
import logging
from dotenv import load_dotenv
from src.etl_pipeline import ARGOETLPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_etl():
    """
    Initializes and runs the full ETL pipeline.
    """
    load_dotenv()
    DB_URL = os.getenv("DATABASE_URL")
    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
    NETCDF_DIRECTORY = "./data/netcdf"

    if not DB_URL:
        logger.error("DATABASE_URL not found in environment. Please check your .env file.")
        return

    logger.info("Starting ETL pipeline...")
    logger.info(f"Source NetCDF directory: {NETCDF_DIRECTORY}")

    try:
        pipeline = ARGOETLPipeline(
            db_url=DB_URL,
            chroma_host=CHROMA_HOST,
            chroma_port=CHROMA_PORT
        )
        
        results = pipeline.run_etl_pipeline(NETCDF_DIRECTORY)
        logger.info(f"ETL run completed. Results: {results}")

    except Exception as e:
        logger.error(f"An error occurred during the ETL pipeline run: {e}")

if __name__ == "__main__":
    run_etl()
