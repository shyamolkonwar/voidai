#!/usr/bin/env python3
"""
Complete Sync Orchestrator

This script orchestrates the entire process:
1. Analyze local database
2. Setup online schema (if needed)
3. Run data sync
4. Generate final report
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'LOCAL_DATABASE_URL',
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    """Main orchestration function."""
    print("🚀 Starting Complete Database Sync Process")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\nPlease set the missing environment variables in your .env file:")
        print("LOCAL_DATABASE_URL=postgresql://...")
        print("SUPABASE_URL=https://...")
        print("SUPABASE_SERVICE_ROLE_KEY=...")
        return 1
    
    # Step 1: Analyze local database
    print("\n📊 Step 1: Analyzing Local Database")
    if not run_command("python check_local_database.py", "Database analysis"):
        return 1
    
    # Read analysis results
    analysis_file = Path("database_analysis.txt")
    if analysis_file.exists():
        print("\n📋 Database Analysis Summary:")
        print(analysis_file.read_text())
    
    # Step 2: Check if schema exists online
    print("\n🔍 Step 2: Checking Online Schema")
    print("\nTo setup the online schema:")
    print("1. Go to your Supabase dashboard")
    print("2. Open SQL Editor")
    print("3. Copy and paste the contents of create_schema.sql")
    print("4. Run the SQL commands")
    
    response = input("\nHave you created the online schema? (y/n): ").lower()
    if response != 'y':
        print("Please create the schema first, then run this script again.")
        return 1
    
    # Step 3: Run test sync
    print("\n🧪 Step 3: Running Test Sync")
    if not run_command("python test_sync_small.py", "Test sync"):
        print("Please fix the test sync issues before proceeding.")
        return 1
    
    # Step 4: Run full sync
    print("\n🔄 Step 4: Running Full Database Sync")
    print("This will transfer all 4M+ records. This may take several hours.")
    
    response = input("Do you want to proceed with the full sync? (y/n): ").lower()
    if response != 'y':
        print("Sync cancelled by user.")
        return 1
    
    print("\n🚀 Starting full sync...")
    print("You can monitor progress in the logs.")
    print("To stop the sync, press Ctrl+C")
    
    try:
        start_time = time.time()
        success = run_command("python sync_local_to_online_supabase.py", "Full sync")
        elapsed = time.time() - start_time
        
        if success:
            print(f"\n🎉 Full sync completed successfully in {elapsed/3600:.1f} hours!")
            
            # Step 5: Export data to CSV
            print("\n📊 Step 5: Exporting Data to CSV")
            if run_command("python export_supabase_to_csv.py", "CSV export"):
                print("\n📁 CSV files created in exported_data/ directory")
            
        else:
            print("\n❌ Full sync failed. Check the logs for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Sync interrupted by user")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())