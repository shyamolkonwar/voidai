#!/usr/bin/env python3
"""
Split large CSV files into smaller chunks for Supabase dashboard upload.
Each chunk will be less than 100MB (targeting ~80MB for safety).
"""

import os
import sys
import csv
from pathlib import Path

def get_file_size_mb(file_path):
    """Get file size in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)

def estimate_rows_per_chunk(file_path, target_size_mb=80):
    """Estimate how many rows fit in target_size_mb."""
    total_size_mb = get_file_size_mb(file_path)
    
    # Count total rows
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        total_rows = sum(1 for row in reader)
    
    # Estimate rows per chunk
    if total_rows == 0:
        return 1000  # Default fallback
    
    rows_per_chunk = int((target_size_mb / total_size_mb) * total_rows)
    return max(1000, rows_per_chunk)  # Ensure minimum 1000 rows

def split_csv_file(input_file, output_dir, target_size_mb=80):
    """Split CSV file into chunks smaller than target_size_mb."""
    
    input_path = Path(input_file)
    base_name = input_path.stem
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Read header
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)
        
        # Estimate rows per chunk
        rows_per_chunk = estimate_rows_per_chunk(input_file, target_size_mb)
        print(f"Estimated {rows_per_chunk} rows per chunk for ~{target_size_mb}MB target")
        
        chunk_num = 1
        rows_written = 0
        current_chunk = []
        
        for row_num, row in enumerate(reader, 1):
            current_chunk.append(row)
            
            # Write chunk when we reach the estimated size or every 100k rows
            if len(current_chunk) >= rows_per_chunk:
                output_file = output_path / f"{base_name}_chunk_{chunk_num:03d}.csv"
                
                with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(header)
                    writer.writerows(current_chunk)
                
                chunk_size_mb = get_file_size_mb(output_file)
                print(f"Created {output_file.name} ({chunk_size_mb:.1f} MB, {len(current_chunk)} rows)")
                
                chunk_num += 1
                rows_written += len(current_chunk)
                current_chunk = []
        
        # Write remaining rows
        if current_chunk:
            output_file = output_path / f"{base_name}_chunk_{chunk_num:03d}.csv"
            
            with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.writer(outfile)
                writer.writerow(header)
                writer.writerows(current_chunk)
            
            chunk_size_mb = get_file_size_mb(output_file)
            print(f"Created {output_file.name} ({chunk_size_mb:.1f} MB, {len(current_chunk)} rows)")
            rows_written += len(current_chunk)
    
    print(f"\nTotal chunks created: {chunk_num}")
    print(f"Total rows processed: {rows_written}")
    return chunk_num

def main():
    """Main function to split all profiles CSV files."""
    
    # Configuration
    exported_data_dir = "/Users/shyamolkonwar/Documents/VOID/VOID_1/backend/exported_data"
    output_dir = "/Users/shyamolkonwar/Documents/VOID/VOID_1/backend/split_profiles"
    
    # Find all profiles CSV files
    csv_files = []
    for file in os.listdir(exported_data_dir):
        if file.startswith('profiles_') and file.endswith('.csv'):
            csv_files.append(os.path.join(exported_data_dir, file))
    
    if not csv_files:
        print("No profiles CSV files found!")
        return
    
    print(f"Found {len(csv_files)} profiles CSV files to split")
    
    for csv_file in csv_files:
        file_size_mb = get_file_size_mb(csv_file)
        print(f"\nProcessing {os.path.basename(csv_file)} ({file_size_mb:.1f} MB)")
        
        if file_size_mb >= 100:
            chunks = split_csv_file(csv_file, output_dir)
            print(f"Successfully split into {chunks} chunks")
        else:
            print(f"File is already under 100MB, skipping split")
    
    print(f"\nAll files processed. Check {output_dir} for split files.")

if __name__ == "__main__":
    main()