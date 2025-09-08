# Complete Database Setup & Sync Guide

This guide walks you through the entire process of analyzing your local Supabase database and syncing it to your online Supabase instance.

## 📋 Overview

Your local database contains **3,975,454 rows** across 4 tables:
- **floats**: 249 rows
- **cycles**: 28,815 rows  
- **profiles**: 3,946,370 rows
- **chat_history**: 20 rows

## 🚀 Quick Start

### 1. Environment Setup

Create a `.env` file in the backend directory:

```bash
# Local database (from your setup_database.py)
LOCAL_DATABASE_URL=postgresql://postgres:your_password@localhost:5432/postgres

# Online Supabase (from your provided credentials)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

### 2. One-Command Setup

Run the complete orchestrator:

```bash
python run_complete_sync.py
```

This will:
1. ✅ Analyze your local database
2. ✅ Guide you through online schema setup
3. ✅ Test connections
4. ✅ Run the full sync process
5. ✅ Export data to CSV files

## 🔧 Manual Setup (Step-by-Step)

### Step 1: Analyze Local Database

```bash
python check_local_database.py
```

This creates `database_analysis.txt` with detailed information.

### Step 2: Setup Online Schema

1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **SQL Editor** (left sidebar)
4. Copy and paste the contents of `create_schema.sql`
5. Click **Run** to create all tables

### Step 3: Test Connections

```bash
python test_sync_small.py
```

This verifies both local and online connections work correctly.

### Step 4: Run Full Sync

```bash
python sync_local_to_online_supabase.py
```

**Note**: This will take approximately **66 hours** for 4M+ records.

### Step 5: Export to CSV

```bash
python export_supabase_to_csv.py
```

Creates timestamped CSV files in `exported_data/` directory.

## ⚙️ Configuration

### Performance Tuning

Edit `sync_config.py` to optimize for your system:

```python
# For faster sync (more memory usage)
BATCH_SIZE = 1000
DELAY_BETWEEN_BATCHES = 0.1

# For slower sync (less memory usage)
BATCH_SIZE = 100
DELAY_BETWEEN_BATCHES = 1.0
```

### Table Selection

Sync only specific tables:

```python
# In sync_config.py
TABLES_TO_SYNC = ['floats', 'cycles']  # Skip large tables
```

## 📊 Monitoring Progress

### Real-time Logs

Watch the sync progress:

```bash
tail -f sync.log  # If you redirect output to log file
```

### Sync Statistics

The sync script provides:
- ✅ Tables processed count
- ✅ Total records transferred
- ✅ Error count
- ✅ Processing rate (rows/second)
- ✅ Estimated time remaining

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Table not found" error
- **Solution**: Run the online schema setup first
- **Command**: Follow Step 2 in Manual Setup

#### 2. Connection timeout
- **Solution**: Reduce batch size in `sync_config.py`
- **File**: `sync_config.py` → `BATCH_SIZE = 500`

#### 3. Memory issues
- **Solution**: Use smaller batches and longer delays
- **File**: `sync_config.py` → `BATCH_SIZE = 100`, `DELAY_BETWEEN_BATCHES = 2.0`

#### 4. Rate limiting
- **Solution**: Add longer delays between batches
- **File**: `sync_config.py` → `DELAY_BETWEEN_BATCHES = 5.0`

### Debug Mode

Enable verbose logging:

```bash
# Add to your .env file
DEBUG=true

# Then run with debug output
python sync_local_to_online_supabase.py
```

## 📁 File Structure

```
backend/
├── check_local_database.py      # Database analyzer
├── sync_local_to_online_supabase.py  # Main sync script
├── export_supabase_to_csv.py   # CSV export
├── test_sync_small.py          # Connection tester
├── run_complete_sync.py        # Complete orchestrator
├── sync_config.py              # Configuration
├── create_schema.sql           # Online schema setup
├── README_COMPLETE_SETUP.md    # This file
├── database_analysis.txt       # Analysis results (generated)
└── exported_data/              # CSV files (generated)
    ├── floats_20250907_121500.csv
    ├── cycles_20250907_121501.csv
    └── ...
```

## 🎯 Next Steps

After successful sync:

1. **Verify Data**: Check row counts match between local and online
2. **Test Queries**: Run some sample queries on online database
3. **Setup API**: Configure your application to use online Supabase
4. **Backup**: Consider setting up automated backups

## 📞 Support

If you encounter issues:

1. Check the logs in terminal output
2. Verify your `.env` file credentials
3. Ensure online schema is properly created
4. Try running with smaller batch sizes
5. Check Supabase dashboard for any rate limits

## ⏱️ Time Estimates

| Operation | Time Estimate |
|-----------|---------------|
| Local analysis | 30 seconds |
| Schema setup | 2 minutes |
| Test sync | 1 minute |
| Full sync (4M rows) | 66 hours |
| CSV export | 15 minutes |

**Pro tip**: Start with the one-command setup (`run_complete_sync.py`) and let it guide you through the process!