
import os
import logging
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, DateTime, ForeignKey
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_schema(database_url: str):
    """
    Creates the database schema for FloatChat.
    """
    try:
        engine = create_engine(database_url)
        metadata = MetaData()

        # Define floats table
        Table('floats', metadata,
              Column('float_id', String, primary_key=True),
              Column('wmo_id', String),
              Column('project_name', String),
              Column('pi_name', String),
              Column('platform_type', String),
              Column('deployment_date', DateTime),
              Column('last_update', DateTime)
        )

        # Define cycles table
        Table('cycles', metadata,
              Column('cycle_id', String, primary_key=True),
              Column('float_id', String, ForeignKey('floats.float_id')),
              Column('cycle_number', Integer),
              Column('profile_date', DateTime),
              Column('latitude', Float),
              Column('longitude', Float),
              Column('profile_type', String)
        )

        # Define profiles table
        Table('profiles', metadata,
              Column('profile_id', String, primary_key=True),
              Column('cycle_id', String, ForeignKey('cycles.cycle_id')),
              Column('pressure', Float),
              Column('temperature', Float),
              Column('salinity', Float),
              Column('depth', Float),
              Column('quality_flag', Integer)
        )

        with engine.connect() as connection:
            logger.info("Creating database tables...")
            metadata.create_all(engine)
            logger.info("Tables created successfully (if they didn't exist).")

    except Exception as e:
        logger.error(f"Failed to create database schema: {e}")
        raise

def main():
    """
    Main function to set up the database.
    """
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable not set. Please create a .env file.")
        return

    create_schema(DATABASE_URL)

if __name__ == "__main__":
    main()
