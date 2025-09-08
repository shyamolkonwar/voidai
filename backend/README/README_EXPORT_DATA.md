# Export Supabase Data to CSV

This guide explains how to use the `export_supabase_to_csv.py` script to export all data from your local Supabase database to CSV files.

## Prerequisites

1. **Environment Setup**: Ensure your `.env` file contains the correct `DATABASE_URL` for your local Supabase instance.

   Example `.env` file:
   ```
   DATABASE_URL=postgresql://postgres:your_password@localhost:54322/postgres
   ```

2. **Dependencies**: All required packages are already listed in `config/requirements.txt`.

## Usage

### Method 1: Export All Tables
```bash
cd backend
python export_supabase_to_csv.py
```

### Method 2: Export Specific Tables
You can modify the script to export only specific tables by changing the `main()` function:

```python
# Instead of exporter.export_all_tables(), use:
specific_tables = ['floats', 'cycles', 'profiles']
exported_files = exporter.export_specific_tables(specific_tables)
```

## Output

- **Location**: All CSV files are saved in the `exported_data/` directory
- **Naming**: Files are named as `{table_name}_{timestamp}.csv`
- **Format**: UTF-8 encoded CSV files with headers

## Tables

Based on your database schema, the following tables will be exported:

1. **floats** - Float metadata and deployment information
2. **cycles** - Cycle data with geographic coordinates
3. **profiles** - Profile measurements (temperature, salinity, pressure, etc.)
4. **chat_history** - Chat conversation history

## Example Output

```
exported_data/
├── floats_20241220_143022.csv
├── cycles_20241220_143022.csv
├── profiles_20241220_143022.csv
└── chat_history_20241220_143022.csv
```

## Troubleshooting

### Connection Issues
- Verify your `DATABASE_URL` is correct
- Ensure Supabase is running locally
- Check if the database is accessible

### Permission Issues
- Ensure your database user has read permissions
- Check if the tables exist in the public schema

### Memory Issues
- For very large datasets, consider exporting tables individually
- Monitor system memory usage during export

## Customization

The script provides several customization options:

- **Output directory**: Change `self.output_dir` in the `__init__` method
- **File naming**: Modify the filename format in `export_table_to_csv`
- **Query filtering**: Add WHERE clauses to the SQL queries for filtered exports
- **Data transformation**: Add data cleaning or transformation steps before CSV export