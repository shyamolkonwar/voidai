# Supabase Local to Online Sync Guide

This guide explains how to use the `sync_local_to_online_supabase.py` script to efficiently transfer large amounts of data from your local Supabase database to the online Supabase instance.

## Overview

The sync script is designed to handle **big data** transfers with:
- **Batch processing** to manage memory efficiently
- **Error handling and recovery** for reliable transfers
- **Progress tracking** with detailed logging
- **Rate limiting** to respect Supabase limits
- **Resume capability** for interrupted transfers

## Prerequisites

### 1. Environment Setup
Create a `.env` file in the backend directory with your local database URL:

```bash
# .env file
DATABASE_URL=postgresql://postgres:your_password@localhost:54322/postgres
```

### 2. Install Dependencies
Ensure you have the required packages:

```bash
cd backend
pip install -r config/requirements.txt
pip install supabase  # Additional dependency for online sync
```

### 3. Verify Online Supabase
- **Project URL**: `https://hxnnvfykvdhllwrgtjtg.supabase.co`
- **Service Role Key**: Already configured in the script
- **Table Structure**: Ensure online tables match local schema

## Usage

### Basic Sync (All Tables)
```bash
cd backend
python sync_local_to_online_supabase.py
```

### Advanced Usage

#### Sync Specific Tables
Modify the script to sync only specific tables:

```python
# In main() function, replace sync_all_tables() with:
specific_tables = ['floats', 'cycles', 'profiles']
for table in specific_tables:
    sync_service.sync_table(table)
```

#### Exclude Tables
The script automatically excludes system tables, but you can add custom exclusions:

```python
exclude_tables = ['chat_history']  # Skip chat history
tables = [t for t in tables if t not in exclude_tables]
```

#### Adjust Batch Size
For very large datasets, adjust the batch size:

```python
# Initialize with custom batch size
sync_service = BigDataSupabaseSync(
    local_db_url=local_db_url,
    online_supabase_url=online_supabase_url,
    online_service_role_key=online_service_role_key,
    batch_size=500  # Smaller batches for very large records
)
```

## Configuration Options

### Batch Size Recommendations
| Dataset Size | Batch Size | Memory Usage |
|-------------|------------|--------------|
| < 10K rows  | 1000-2000  | Low          |
| 10K-100K    | 500-1000   | Medium       |
| 100K-1M     | 100-500    | High         |
| > 1M        | 50-100     | Very High    |

### Rate Limiting
The script includes built-in delays:
- **0.1s delay** between batches
- **Retry logic** for failed requests
- **Supabase limits**: Respects 100MB/hour database limits

## Monitoring Progress

### Real-time Logs
Monitor the sync progress in real-time:
```bash
tail -f sync_supabase.log
```

### Sync Report
After completion, check the detailed report:
```bash
cat sync_report.txt
```

### Expected Output
```
2024-12-20 14:30:15 - INFO - Starting Supabase sync from local to online...
2024-12-20 14:30:16 - INFO - Found 4 tables to sync: ['floats', 'cycles', 'profiles', 'chat_history']
2024-12-20 14:30:17 - INFO - Starting sync for table: floats
2024-12-20 14:30:18 - INFO - Table floats: 1250 total rows, 7 columns
2024-12-20 14:30:19 - INFO - Processed 1000/1250 rows for floats
2024-12-20 14:30:20 - INFO - Processed 1250/1250 rows for floats
2024-12-20 14:30:21 - INFO - Successfully synced floats: 1250 records
```

## Troubleshooting

### Common Issues

#### 1. Connection Timeouts
**Problem**: Large datasets cause connection timeouts
**Solution**: Reduce batch size to 100-500 records

#### 2. Memory Errors
**Problem**: Out of memory errors with large datasets
**Solution**: Use smaller batch sizes and monitor system resources

#### 3. Rate Limiting
**Problem**: Supabase rate limit exceeded
**Solution**: Increase delays between batches:
```python
# In sync_table method, increase delay
time.sleep(1.0)  # Instead of 0.1s
```

#### 4. Schema Mismatches
**Problem**: Column types don't match between local and online
**Solution**: Ensure identical schema before syncing:
```bash
# Check schema locally
python -c "
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute('SELECT * FROM floats LIMIT 1')
    print('Local columns:', [col for col in result.keys()])
"
```

### Performance Optimization

#### 1. Parallel Processing (Advanced)
For very large datasets, implement parallel processing:

```python
import concurrent.futures

# In sync_table method
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = []
    for offset in range(0, total_rows, batch_size):
        future = executor.submit(self.fetch_batch, table_name, offset, batch_size)
        futures.append(future)
```

#### 2. Index Optimization
Ensure online Supabase has proper indexes:
```sql
-- Run in Supabase SQL editor
CREATE INDEX IF NOT EXISTS idx_floats_wmo_id ON floats(wmo_id);
CREATE INDEX IF NOT EXISTS idx_cycles_float_id ON cycles(float_id);
CREATE INDEX IF NOT EXISTS idx_profiles_cycle_id ON profiles(cycle_id);
```

#### 3. Connection Pooling
For faster transfers, use connection pooling:

```python
from sqlalchemy.pool import QueuePool

self.local_engine = create_engine(
    local_db_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

## Data Validation

### Pre-sync Validation
```bash
# Check local data integrity
python -c "
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

for table in ['floats', 'cycles', 'profiles', 'chat_history']:
    count = pd.read_sql(f'SELECT COUNT(*) as cnt FROM {table}', engine)['cnt'][0]
    print(f'{table}: {count} rows')
"
```

### Post-sync Validation
```bash
# Check online data
python -c "
from supabase import create_client
supabase = create_client('https://hxnnvfykvdhllwrgtjtg.supabase.co', 'YOUR_SERVICE_ROLE_KEY')

for table in ['floats', 'cycles', 'profiles', 'chat_history']:
    result = supabase.table(table).select('*', count='exact').execute()
    print(f'{table}: {len(result.data)} rows')
"
```

## Emergency Recovery

### Resume Interrupted Sync
If sync is interrupted, you can resume from specific tables:

```python
# Resume from specific table
completed_tables = ['floats', 'cycles']  # Already completed
remaining_tables = ['profiles', 'chat_history']

for table in remaining_tables:
    sync_service.sync_table(table)
```

### Rollback Changes
To rollback changes, use Supabase's built-in rollback features or manually clear tables:

```python
# Clear specific tables
for table in ['profiles', 'cycles', 'floats', 'chat_history']:
    sync_service.clear_online_table(table)
```

## Best Practices

1. **Test First**: Sync a small table first to verify setup
2. **Monitor Resources**: Use `htop` to monitor CPU/memory usage
3. **Backup Online**: Export online data before sync if needed
4. **Incremental Sync**: For ongoing syncs, implement timestamp-based filtering
5. **Error Alerts**: Set up notifications for sync failures

## Support

For issues or questions:
1. Check the log file: `sync_supabase.log`
2. Verify connection settings
3. Ensure sufficient Supabase quota
4. Review Supabase documentation: https://supabase.com/docs