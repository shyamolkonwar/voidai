"""
Enhanced ARGO Data Reader
=========================

Specialized class for extracting database-ready attributes from ARGO NetCDF files
following the ARGO file naming convention and data standards.

Author: FloatChat Backend System
"""

import os
import re
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import xarray as xr

# Configure logging
logger = logging.getLogger(__name__)

class ArgoDataReader:
    """
    Enhanced ARGO data reader that extracts database-ready attributes from NetCDF files
    following ARGO standards and file naming conventions.
    """
    
    def __init__(self):
        """Initialize the ARGO data reader."""
        pass
    
    @staticmethod
    def decode_bytes(value) -> Optional[str]:
        """
        Handle various NetCDF byte string formats.
        
        Args:
            value: NetCDF byte array, bytes, or string
            
        Returns:
            Decoded string or None if invalid
        """
        if value is None:
            return None
            
        try:
            # Handle bytes and byte arrays
            if isinstance(value, bytes):
                decoded = value.decode('utf-8').strip()
                return decoded if decoded and decoded != '--' else None
                
            elif isinstance(value, np.ndarray):
                # Handle numpy arrays containing bytes or strings
                if value.size == 0:
                    return None
                    
                # Handle object arrays containing bytes
                if value.dtype == np.dtype('O'):
                    if isinstance(value.item(), bytes):
                        decoded = value.item().decode('utf-8').strip()
                        return decoded if decoded and decoded != '--' else None
                    elif isinstance(value.item(), str):
                        return value.item().strip() if value.item().strip() and value.item() != '--' else None
                    else:
                        return str(value.item()).strip()
                
                # Handle string arrays (S, U types)
                elif value.dtype.kind in ['S', 'U']:
                    # Handle string arrays - flatten and join
                    if value.ndim > 0:
                        flat_values = value.flatten()
                        chars = []
                        for item in flat_values:
                            if isinstance(item, bytes):
                                decoded = item.decode('utf-8').strip()
                                if decoded and decoded != '--' and decoded != '-':
                                    chars.append(decoded)
                            elif isinstance(item, str) and item.strip() and item != '--' and item != '-':
                                chars.append(item.strip())
                        if chars:
                            return ''.join(chars).strip()
                        return None
                    else:
                        # Single value array
                        if isinstance(value.item(), bytes):
                            decoded = value.item().decode('utf-8').strip()
                            return decoded if decoded and decoded != '--' else None
                        else:
                            return str(value.item()).strip()
                else:
                    return str(value.item()).strip()
                        
            elif isinstance(value, str):
                return value.strip() if value.strip() and value != '--' else None
                
            else:
                # Try to convert to string
                str_value = str(value).strip()
                return str_value if str_value and str_value != '--' else None
                
        except Exception as e:
            logger.warning(f"Error decoding bytes: {e}")
            return None
    
    @staticmethod
    def julian_to_datetime(julian_days: float) -> Optional[datetime]:
        """
        Convert Julian days since 1950-01-01 to datetime.
        
        Args:
            julian_days: Days since 1950-01-01 00:00:00 UTC
            
        Returns:
            datetime object or None for invalid values
        """
        if julian_days is None or np.isnan(julian_days):
            return None
            
        try:
            # Reference date: 1950-01-01 00:00:00 UTC
            reference_date = datetime(1950, 1, 1)
            return reference_date + timedelta(days=float(julian_days))
        except (ValueError, TypeError) as e:
            logger.warning(f"Error converting Julian date: {e}")
            return None
    
    @staticmethod
    def parse_date_update(date_update_bytes) -> Optional[datetime]:
        """
        Parse DATE_UPDATE format (YYYYMMDDHHMISS) to datetime.
        
        Args:
            date_update_bytes: Byte string in YYYYMMDDHHMISS format
            
        Returns:
            datetime object or None if invalid
        """
        date_str = ArgoDataReader.decode_bytes(date_update_bytes)
        if not date_str or len(date_str) != 14:
            return None
            
        try:
            return datetime.strptime(date_str, '%Y%m%d%H%M%S')
        except ValueError:
            return None
    
    @staticmethod
    def parse_filename_attributes(file_path: str) -> Dict[str, Any]:
        """
        Parse ARGO filename to extract WMO ID and cycle number.
        
        Args:
            file_path: Path to NetCDF file
            
        Returns:
            Dictionary with filename attributes
        """
        filename = os.path.basename(file_path)
        
        # ARGO filename pattern: [D|R]WMOID_CYCLENUMBER.nc
        pattern = r'^([DR])(\d{7})_(\d+)\.nc$'
        match = re.match(pattern, filename)
        
        if match:
            file_type = 'delayed' if match.group(1) == 'D' else 'real-time'
            wmo_id = match.group(2)
            cycle_number = int(match.group(3))
            
            return {
                'file_type': file_type,
                'wmo_id': wmo_id,
                'cycle_number': cycle_number,
                'filename_valid': True
            }
        else:
            logger.warning(f"Filename {filename} doesn't match ARGO naming convention")
            return {
                'file_type': 'unknown',
                'wmo_id': None,
                'cycle_number': None,
                'filename_valid': False
            }
    
    def extract_database_attributes(self, file_path: str) -> Dict[str, Any]:
        """
        Extract database-ready attributes from ARGO NetCDF file.
        
        Args:
            file_path: Path to NetCDF file
            
        Returns:
            Dictionary with database attributes
        """
        try:
            with xr.open_dataset(file_path) as dataset:
                # Parse filename attributes first
                filename_attrs = self.parse_filename_attributes(file_path)
                
                # Extract core database attributes
                attributes = {
                    'float_id': filename_attrs['wmo_id'],
                    'wmo_id': filename_attrs['wmo_id'],
                    'file_type': filename_attrs['file_type'],
                    'cycle_number': filename_attrs['cycle_number'],
                    'filename_valid': filename_attrs['filename_valid']
                }
                
                # Extract PI_NAME
                if 'PI_NAME' in dataset.variables:
                    pi_name = self.decode_bytes(dataset.PI_NAME.values)
                    attributes['pi_name'] = pi_name
                else:
                    attributes['pi_name'] = None
                
                # Extract PLATFORM_TYPE
                if 'PLATFORM_TYPE' in dataset.variables:
                    platform_type = self.decode_bytes(dataset.PLATFORM_TYPE.values)
                    attributes['platform_type'] = platform_type
                else:
                    attributes['platform_type'] = None
                
                # Extract PROJECT_NAME
                if 'PROJECT_NAME' in dataset.variables:
                    project_name = self.decode_bytes(dataset.PROJECT_NAME.values)
                    attributes['project_name'] = project_name
                else:
                    attributes['project_name'] = None
                
                # Extract DATA_CENTRE
                if 'DATA_CENTRE' in dataset.variables:
                    data_centre = self.decode_bytes(dataset.DATA_CENTRE.values)
                    attributes['data_centre'] = data_centre
                else:
                    attributes['data_centre'] = None
                
                # Extract DIRECTION
                if 'DIRECTION' in dataset.variables:
                    direction = self.decode_bytes(dataset.DIRECTION.values)
                    attributes['direction'] = direction
                else:
                    attributes['direction'] = None
                
                # Extract JULD (profile date) - handle both Julian days and datetime formats
                if 'JULD' in dataset.variables:
                    juld_value = dataset.JULD.values
                    
                    # Handle different JULD formats
                    if isinstance(juld_value, np.ndarray) and juld_value.dtype.kind == 'M':
                        # Already datetime format
                        if juld_value.size > 0:
                            deployment_date = pd.to_datetime(juld_value.item())
                            attributes['deployment_date'] = deployment_date
                        else:
                            attributes['deployment_date'] = None
                    else:
                        # Handle Julian days format
                        if hasattr(juld_value, 'item'):
                            juld_value = juld_value.item()
                        deployment_date = self.julian_to_datetime(juld_value)
                        attributes['deployment_date'] = deployment_date
                else:
                    attributes['deployment_date'] = None
                
                # Extract DATE_UPDATE
                if 'DATE_UPDATE' in dataset.variables:
                    last_update = self.parse_date_update(dataset.DATE_UPDATE.values)
                    attributes['last_update'] = last_update
                else:
                    attributes['last_update'] = None
                
                # Extract location data
                if 'LATITUDE' in dataset.variables:
                    attributes['latitude'] = float(dataset.LATITUDE.values)
                else:
                    attributes['latitude'] = None
                
                if 'LONGITUDE' in dataset.variables:
                    attributes['longitude'] = float(dataset.LONGITUDE.values)
                else:
                    attributes['longitude'] = None
                
                # Extract number of levels
                if 'N_LEVELS' in dataset.dims:
                    attributes['n_levels'] = dataset.sizes['N_LEVELS']
                else:
                    attributes['n_levels'] = 0
                
                # Construct derived identifiers
                if attributes['float_id'] and attributes['cycle_number'] is not None:
                    attributes['cycle_id'] = f"{attributes['float_id']}_{attributes['cycle_number']}"
                    attributes['profile_id'] = f"{attributes['cycle_id']}_profile"
                else:
                    attributes['cycle_id'] = None
                    attributes['profile_id'] = None
                
                return attributes
                
        except Exception as e:
            logger.error(f"Error extracting attributes from {file_path}: {e}")
            return {
                'error': str(e),
                'filename_valid': False
            }
    
    def validate_attributes(self, attributes: Dict[str, Any]) -> bool:
        """
        Validate that required attributes are present.
        
        Args:
            attributes: Dictionary of extracted attributes
            
        Returns:
            True if valid, False otherwise
        """
        required = ['float_id', 'wmo_id', 'cycle_id']
        return all(attributes.get(field) for field in required)

# Example usage
if __name__ == "__main__":
    # Test the data reader
    reader = ArgoDataReader()
    
    # Test with a sample file
    sample_file = "data/netcdf/1902670/profiles/D1902670_001.nc"
    if os.path.exists(sample_file):
        attrs = reader.extract_database_attributes(sample_file)
        print("Extracted attributes:")
        for key, value in attrs.items():
            print(f"  {key}: {value}")
        
        print(f"\nValidation: {reader.validate_attributes(attrs)}")
    else:
        print(f"Sample file not found: {sample_file}")