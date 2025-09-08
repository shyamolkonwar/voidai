# Supabase Online Setup Guide

This guide explains how to set up and use the Supabase online database instead of localhost.

## Files Created

1. `setup_supabase_online.py` - Sets up the database schema on Supabase online
2. `run_etl_supabase.py` - Runs the ETL pipeline against Supabase online
3. `.env.example` - Example environment configuration

## Setup Instructions

### 1. Configure Your Password

Replace `YOUR_PASSWORD_HERE` in the Supabase database URL with your actual database password.

### 2. Set Environment Variables

Create a `.env` file in the backend directory with:

```bash
SUPABASE_DATABASE_URL=postgresql://postgres.bdwxbfhyfrtchaxkyurf:YOUR_PASSWORD_HERE@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://bdwxbfhyfrtchaxkyurf.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJkd3hiZmh5ZnJ0Y2hheGt5dXJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NzY5NzQsImV4cCI6MjA3MjU1Mjk3NH0.O0pLfogr3v5dfx59WMEFgECr5cZsjSbGVR90r0_vcOA
```

### 3. Run Setup

```bash
# Set up the database schema
python setup_supabase_online.py

# Run the ETL pipeline
python run_etl_supabase.py
```

## Notes

- The database password is your Supabase project password
- Ensure your Supabase project allows external connections
- You may need to configure Supabase connection pooling settings