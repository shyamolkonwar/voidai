
"""
FloatChat ETL Pipeline
=====================

Data ingestion pipeline for ARGO NetCDF files.
Extracts, transforms, and loads oceanographic float data into PostgreSQL and ChromaDB.

Author: FloatChat Backend System
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import xarray as xr
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime

# Import the enhanced ARGO data reader
try:
    from .argo_data_reader import ArgoDataReader
except ImportError:
    # Fallback for direct execution
    from argo_data_reader import ArgoDataReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ARGOETLPipeline:
    """
    Complete ETL pipeline for ARGO float data processing.
    Handles extraction from NetCDF files, transformation to PostgreSQL schema,
    and loading to both PostgreSQL and ChromaDB.
    """

    def __init__(self, db_url: str, chroma_host: str = "localhost", chroma_port: int = 8000):
        """
        Initialize the ETL pipeline with database connections.

        Args:
            db_url: PostgreSQL connection URL
            chroma_host: ChromaDB server host
            chroma_port: ChromaDB server port
        """
        self.db_url = db_url
        self.engine = create_engine(db_url, pool_size=20, max_overflow=0)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Initialize ARGO data reader
        self.argo_reader = ArgoDataReader()

        # Initialize ChromaDB client
        self.chroma_client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )

        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Get or create ChromaDB collection
        try:
            self.collection = self.chroma_client.get_collection(name="float_profiles")
        except:
            self.collection = self.chroma_client.create_collection(
                name="float_profiles",
                metadata={"description": "ARGO float profile summaries and metadata"}
            )

    def extract_netcdf_files(self, directory_path: str) -> List[str]:
        """
        Find and return paths to all ARGO NetCDF files in the specified directory.

        Args:
            directory_path: Path to directory containing NetCDF files

        Returns:
            List of file paths to NetCDF files
        """
        netcdf_files = []
        directory = Path(directory_path)

        if not directory.exists():
            logger.error(f"Directory {directory_path} does not exist")
            return netcdf_files

        # Search for .nc files recursively
        for file_path in directory.rglob("*.nc"):
            if file_path.is_file():
                netcdf_files.append(str(file_path))

        logger.info(f"Found {len(netcdf_files)} NetCDF files in {directory_path}")
        return netcdf_files

    def _get_variable(self, dataset: xr.Dataset, potential_names: List[str]) -> Optional[xr.DataArray]:
        """Safely get a variable from a dataset by checking a list of potential names."""
        for name in potential_names:
            if name in dataset.variables:
                return dataset[name]
        return None

    def _extract_platform_number(self, dataset: xr.Dataset) -> Optional[str]:
        """Extract and decode platform number from NetCDF dataset."""
        # First try to get from variables (PLATFORM_NUMBER)
        platform_var = self._get_variable(dataset, ['PLATFORM_NUMBER', 'platform_number'])
        if platform_var is not None:
            try:
                platform_data = platform_var.values
                # Handle byte array format like [[b'1' b'9' b'0' b'2' b'6' b'6' b'9' --]]
                if platform_data.ndim > 0:
                    # Flatten and decode
                    flat_data = platform_data.flatten()
                    # Filter out '--' and None values, then decode bytes to string
                    chars = []
                    for item in flat_data:
                        if item is not None and item != b'--' and item != '--':
                            if isinstance(item, bytes):
                                decoded = item.decode('utf-8')
                                if decoded != '-':
                                    chars.append(decoded)
                            elif isinstance(item, str) and item != '-':
                                chars.append(item)
                    
                    platform_str = ''.join(chars).strip()
                    if platform_str and platform_str.isdigit():
                        return platform_str
                    
            except Exception as e:
                logger.warning(f"Could not decode PLATFORM_NUMBER variable: {e}")
        
        # Fallback to attributes
        platform_number = dataset.attrs.get('platform_number')
        if platform_number:
            return str(platform_number)
            
        return None

    def transform_netcdf_to_schema(self, file_path: str) -> Dict[str, Any]:
        """
        Transform ARGO NetCDF data to match PostgreSQL star schema.
        Uses enhanced ArgoDataReader for proper attribute extraction.
        """
        try:
            # Extract database attributes using enhanced reader
            argo_attrs = self.argo_reader.extract_database_attributes(file_path)
            
            if not argo_attrs or 'error' in argo_attrs:
                logger.error(f"Failed to extract attributes from {file_path}: {argo_attrs.get('error', 'Unknown error')}")
                return None
                
            if not self.argo_reader.validate_attributes(argo_attrs):
                logger.error(f"Invalid attributes extracted from {file_path}: {argo_attrs}")
                return None

            # --- Float Metadata ---
            float_data = {
                'float_id': argo_attrs['float_id'],
                'wmo_id': argo_attrs['wmo_id'],
                'project_name': argo_attrs['project_name'] or 'ARGO',
                'pi_name': argo_attrs['pi_name'] or 'unknown',
                'platform_type': argo_attrs['platform_type'] or 'unknown',
                'deployment_date': argo_attrs['deployment_date'] or datetime.now(),
                'last_update': argo_attrs['last_update'] or datetime.now()
            }

            # --- Cycles and Profiles ---
            cycles_data = []
            profiles_data = []

            # Open dataset for measurement data extraction
            with xr.open_dataset(file_path) as dataset:
                # --- Variable Name Mappings ---
                var_map = {
                    'pres': self._get_variable(dataset, ['PRES', 'pres']),
                    'temp': self._get_variable(dataset, ['TEMP', 'temp']),
                    'psal': self._get_variable(dataset, ['PSAL', 'psal']),
                    'pres_qc': self._get_variable(dataset, ['PRES_QC', 'pres_qc']),
                }

                n_profiles = dataset.sizes.get('N_PROF', 1)

                for profile_idx in range(n_profiles):
                    # --- Cycle Data ---
                    cycle_id = argo_attrs['cycle_id']
                    cycle_number_val = argo_attrs['cycle_number']

                    cycle_data = {
                        'cycle_id': cycle_id,
                        'float_id': float_data['float_id'],
                        'cycle_number': cycle_number_val,
                        'profile_date': argo_attrs['deployment_date'] or datetime.now(),
                        'latitude': argo_attrs['latitude'] or 0.0,
                        'longitude': argo_attrs['longitude'] or 0.0,
                        'profile_type': argo_attrs['direction'] or 'A'
                    }
                    cycles_data.append(cycle_data)

                    # --- Profile Data ---
                    n_levels = dataset.sizes.get('N_LEVELS', 0)
                    
                    # Check if measurement variables exist before looping
                    if var_map['pres'] is None:
                        logger.warning(f"No pressure data found in {file_path}. Skipping profile measurements.")
                        continue

                    for level_idx in range(n_levels):
                        try:
                            # Ensure indices are valid for this profile
                            if profile_idx >= var_map['pres'].sizes['N_PROF'] or level_idx >= var_map['pres'].sizes['N_LEVELS']:
                                continue

                            pressure_val = float(var_map['pres'][profile_idx, level_idx].values)
                            if np.isnan(pressure_val): continue # Skip levels with no pressure data

                            temp_val = float(var_map['temp'][profile_idx, level_idx].values) if var_map['temp'] is not None else None
                            sal_val = float(var_map['psal'][profile_idx, level_idx].values) if var_map['psal'] is not None else None
                            qc_flag = int(var_map['pres_qc'][profile_idx, level_idx].values) if var_map['pres_qc'] is not None else 1

                            profile_data = {
                                'profile_id': f"{cycle_id}_{level_idx}",
                                'cycle_id': cycle_id,
                                'pressure': pressure_val,
                                'temperature': temp_val,
                                'salinity': sal_val,
                                'depth': float(level_idx * 10),  # Placeholder, real depth can be calculated from pressure
                                'quality_flag': qc_flag
                            }
                            profiles_data.append(profile_data)
                        except IndexError:
                            logger.warning(f"Index out of bounds for level {level_idx} in profile {profile_idx} of file {file_path}. Skipping level.")
                            continue
            
            return {
                'float': float_data,
                'cycles': cycles_data,
                'profiles': profiles_data
            }

        except Exception as e:
            logger.error(f"Error transforming {file_path}: {str(e)}", exc_info=True)
            return None

    def load_to_postgresql(self, transformed_data: Dict[str, Any]) -> bool:
        """
        Load transformed data to PostgreSQL database, ensuring transactional integrity.

        Args:
            transformed_data: Dictionary containing float, cycles, and profiles data

        Returns:
            Boolean indicating success
        """
        # Use a single session and transaction for the entire operation for this file.
        # The `with` block ensures commit on success and rollback on failure.
        with self.SessionLocal.begin() as session:
            try:
                # Step 1: Insert float data
                float_insert = text("""
                    INSERT INTO floats (float_id, wmo_id, project_name, pi_name, platform_type, deployment_date, last_update)
                    VALUES (:float_id, :wmo_id, :project_name, :pi_name, :platform_type, :deployment_date, :last_update)
                    ON CONFLICT (float_id) DO UPDATE SET
                        last_update = EXCLUDED.last_update
                """)
                session.execute(float_insert, transformed_data['float'])

                # Step 2: Insert cycles data
                for cycle in transformed_data['cycles']:
                    cycle_insert = text("""
                        INSERT INTO cycles (cycle_id, float_id, cycle_number, profile_date, latitude, longitude, profile_type)
                        VALUES (:cycle_id, :float_id, :cycle_number, :profile_date, :latitude, :longitude, :profile_type)
                        ON CONFLICT (cycle_id) DO NOTHING
                    """)
                    session.execute(cycle_insert, cycle)

                # Step 3: Insert profiles with conflict handling
                if transformed_data['profiles']:
                    profile_insert = text("""
                        INSERT INTO profiles (profile_id, cycle_id, pressure, temperature, salinity, depth, quality_flag)
                        VALUES (:profile_id, :cycle_id, :pressure, :temperature, :salinity, :depth, :quality_flag)
                        ON CONFLICT (profile_id) DO NOTHING
                    """)
                    for profile in transformed_data['profiles']:
                        session.execute(profile_insert, profile)
                    
                    logger.info(f"Inserted {len(transformed_data['profiles'])} profile records for float {transformed_data['float']['float_id']}")

                logger.info(f"Successfully loaded data for float {transformed_data['float']['float_id']}")
                return True

            except Exception as e:
                logger.error(f"Error loading data to PostgreSQL for float {transformed_data['float']['float_id']}: {str(e)}", exc_info=True)
                # Log the first few profile IDs that might be causing conflicts
                if transformed_data.get('profiles'):
                    sample_ids = [p['profile_id'] for p in transformed_data['profiles'][:5]]
                    logger.error(f"Sample profile IDs being inserted: {sample_ids}")
                # The `with self.SessionLocal.begin() as session:` block will automatically rollback the transaction here.
                return False

    def generate_document_summaries(self, transformed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate four-tier document summaries for ChromaDB.

        Args:
            transformed_data: Dictionary containing float, cycles, and profiles data

        Returns:
            List of document summaries with metadata
        """
        documents = []
        float_data = transformed_data['float']

        for cycle in transformed_data['cycles']:
            # Get profiles for this cycle
            cycle_profiles = [p for p in transformed_data['profiles'] if p['cycle_id'] == cycle['cycle_id']]

            # 1. Float Metadata Summary
            float_metadata_doc = f"""
            Float Metadata:
            Float ID: {float_data['float_id']}
            WMO ID: {float_data['wmo_id']}
            Project: {float_data['project_name']}
            Principal Investigator: {float_data['pi_name']}
            Platform Type: {float_data['platform_type']}
            Deployment Date: {float_data['deployment_date']}
            """

            # 2. Temporal Context Summary
            temporal_doc = f"""
            Temporal Context:
            Profile Date: {cycle['profile_date']}
            Cycle Number: {cycle['cycle_number']}
            Profile Type: {cycle['profile_type']}
            """

            # 3. Measurement Summary
            temp_values = [p['temperature'] for p in cycle_profiles if p['temperature'] is not None]
            sal_values = [p['salinity'] for p in cycle_profiles if p['salinity'] is not None]
            press_values = [p['pressure'] for p in cycle_profiles if p['pressure'] is not None]

            measurement_doc = f"""
            Measurements Summary:
            Temperature Range: {min(temp_values) if temp_values else 'N/A'} to {max(temp_values) if temp_values else 'N/A'} °C
            Salinity Range: {min(sal_values) if sal_values else 'N/A'} to {max(sal_values) if sal_values else 'N/A'} PSU
            Pressure Range: {min(press_values) if press_values else 'N/A'} to {max(press_values) if press_values else 'N/A'} dbar
            Number of Measurements: {len(cycle_profiles)}
            """

            # 4. Geographic Summary
            geographic_doc = f"""
            Geographic Context:
            Location: {cycle['latitude']:.2f}°N, {cycle['longitude']:.2f}°E
            Latitude: {cycle['latitude']}
            Longitude: {cycle['longitude']}
            """

            # Combine all summaries
            combined_doc = f"{float_metadata_doc}{temporal_doc}{measurement_doc}{geographic_doc}"

            # Create document with metadata
            document = {
                'id': cycle['cycle_id'],
                'content': combined_doc,
                'metadata': {
                    'float_id': float_data['float_id'],
                    'cycle_number': cycle['cycle_number'],
                    'latitude': cycle['latitude'],
                    'longitude': cycle['longitude'],
                    'profile_date': cycle['profile_date'].isoformat(),
                    'project_name': float_data['project_name'],
                    'measurement_count': len(cycle_profiles)
                }
            }

            documents.append(document)

        return documents

    def load_to_chromadb(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Load document summaries to ChromaDB with embeddings.

        Args:
            documents: List of document summaries with metadata

        Returns:
            Boolean indicating success
        """
        try:
            if not documents:
                return True

            # Prepare data for ChromaDB
            ids = [doc['id'] for doc in documents]
            contents = [doc['content'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]

            # Generate embeddings
            embeddings = self.embedding_model.encode(contents).tolist()

            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas,
                embeddings=embeddings
            )

            logger.info(f"Successfully loaded {len(documents)} documents to ChromaDB")
            return True

        except Exception as e:
            logger.error(f"Error loading documents to ChromaDB: {str(e)}")
            return False

    def process_netcdf_file(self, file_path: str) -> bool:
        """
        Complete ETL process for a single NetCDF file.

        Args:
            file_path: Path to NetCDF file

        Returns:
            Boolean indicating success
        """
        logger.info(f"Processing file: {file_path}")

        # Extract and transform
        transformed_data = self.transform_netcdf_to_schema(file_path)
        if not transformed_data:
            return False

        # Load to PostgreSQL
        if not self.load_to_postgresql(transformed_data):
            return False

        # Generate and load document summaries
        documents = self.generate_document_summaries(transformed_data)
        if not self.load_to_chromadb(documents):
            return False

        logger.info(f"Successfully processed {file_path}")
        return True

    def run_etl_pipeline(self, directory_path: str) -> Dict[str, int]:
        """
        Run the complete ETL pipeline on all NetCDF files in a directory.

        Args:
            directory_path: Path to directory containing NetCDF files

        Returns:
            Dictionary with processing statistics
        """
        stats = {'processed': 0, 'failed': 0, 'total': 0}

        # Find all NetCDF files
        netcdf_files = self.extract_netcdf_files(directory_path)
        stats['total'] = len(netcdf_files)

        # Process each file
        for file_path in netcdf_files:
            if self.process_netcdf_file(file_path):
                stats['processed'] += 1
            else:
                stats['failed'] += 1

        logger.info(f"ETL Pipeline completed. Processed: {stats['processed']}, Failed: {stats['failed']}, Total: {stats['total']}")
        return stats

def main():
    """
    Example usage of the ETL pipeline.
    """
    # Configuration
    DB_URL = "postgresql://username:password@localhost:5432/floatchat"
    NETCDF_DIRECTORY = "/path/to/argo/netcdf/files"

    # Initialize and run pipeline
    pipeline = ARGOETLPipeline(DB_URL)
    results = pipeline.run_etl_pipeline(NETCDF_DIRECTORY)
    print(f"ETL Results: {results}")

if __name__ == "__main__":
    main()