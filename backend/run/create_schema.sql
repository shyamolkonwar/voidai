-- Create Online Supabase Schema
-- Run this SQL in your Supabase dashboard SQL editor

-- Create floats table
CREATE TABLE IF NOT EXISTS public.floats (
    float_id TEXT PRIMARY KEY,
    wmo_id TEXT,
    project_name TEXT,
    pi_name TEXT,
    platform_type TEXT,
    deployment_date TIMESTAMP WITH TIME ZONE,
    last_update TIMESTAMP WITH TIME ZONE
);

-- Create cycles table
CREATE TABLE IF NOT EXISTS public.cycles (
    cycle_id TEXT PRIMARY KEY,
    float_id TEXT REFERENCES public.floats(float_id) ON DELETE CASCADE,
    cycle_number INTEGER,
    profile_date TIMESTAMP WITH TIME ZONE,
    latitude REAL,
    longitude REAL,
    profile_type TEXT
);

-- Create profiles table
CREATE TABLE IF NOT EXISTS public.profiles (
    profile_id TEXT PRIMARY KEY,
    cycle_id TEXT REFERENCES public.cycles(cycle_id) ON DELETE CASCADE,
    pressure REAL,
    temperature REAL,
    salinity REAL,
    depth REAL,
    quality_flag INTEGER
);

-- Create chat_history table
CREATE TABLE IF NOT EXISTS public.chat_history (
    session_id TEXT,
    turn_index INTEGER,
    role TEXT,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    full_response JSONB,
    PRIMARY KEY (session_id, turn_index)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cycles_float_id ON public.cycles(float_id);
CREATE INDEX IF NOT EXISTS idx_profiles_cycle_id ON public.profiles(cycle_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON public.chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON public.chat_history(created_at);

-- Grant permissions (adjust based on your security requirements)
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;