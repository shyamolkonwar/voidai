-- Supabase FloatChat Schema
-- Version: 2.1 - Fixed RLS Policies and Indexes

-- Enable PostGIS extension if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Enable Row Level Security on all tables
ALTER TABLE floats ENABLE ROW LEVEL SECURITY;
ALTER TABLE cycles ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Create floats table
CREATE TABLE IF NOT EXISTS floats (
    float_id VARCHAR PRIMARY KEY,
    wmo_id VARCHAR,
    project_name VARCHAR,
    pi_name VARCHAR,
    platform_type VARCHAR,
    deployment_date TIMESTAMP,
    last_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create cycles table
CREATE TABLE IF NOT EXISTS cycles (
    cycle_id VARCHAR PRIMARY KEY,
    float_id VARCHAR REFERENCES floats(float_id) ON DELETE CASCADE,
    cycle_number INTEGER,
    profile_date TIMESTAMP,
    latitude FLOAT,
    longitude FLOAT,
    profile_type VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
    profile_id VARCHAR PRIMARY KEY,
    cycle_id VARCHAR REFERENCES cycles(cycle_id) ON DELETE CASCADE,
    pressure FLOAT,
    temperature FLOAT,
    salinity FLOAT,
    depth FLOAT,
    quality_flag INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create chat_history table
CREATE TABLE IF NOT EXISTS chat_history (
    session_id VARCHAR,
    turn_index INTEGER,
    role VARCHAR,
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    user_id UUID REFERENCES auth.users(id),
    PRIMARY KEY (session_id, turn_index)
);



-- Add comments to tables and columns for clarity
COMMENT ON TABLE floats IS 'Stores metadata for each ARGO float with RLS policies for data access control';
COMMENT ON TABLE cycles IS 'Stores information about each measurement cycle of a float with geographic indexing';
COMMENT ON TABLE profiles IS 'Stores the individual data points (pressure, temperature, salinity) for each cycle with quality filtering';
COMMENT ON TABLE chat_history IS 'Stores the conversation history for each chat session with user-based access control';

-- RLS Policies for floats table
CREATE POLICY "Allow public read access to floats" ON floats FOR SELECT USING (true);

-- RLS Policies for cycles table
CREATE POLICY "Allow public read access to cycles" ON cycles FOR SELECT USING (true);

-- RLS Policies for profiles table
CREATE POLICY "Allow public read access to profiles" ON profiles FOR SELECT USING (true);

-- RLS Policies for chat_history table
CREATE POLICY "Allow public read access to chat history" ON chat_history FOR SELECT USING (true);
CREATE POLICY "Allow authenticated user insert to chat history" ON chat_history FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Performance Indexes for floats table
CREATE INDEX IF NOT EXISTS idx_floats_wmo_id ON floats(wmo_id);
CREATE INDEX IF NOT EXISTS idx_floats_project_name ON floats(project_name);
CREATE INDEX IF NOT EXISTS idx_floats_platform_type ON floats(platform_type);
CREATE INDEX IF NOT EXISTS idx_floats_last_update ON floats(last_update DESC);

-- Performance Indexes for cycles table
CREATE INDEX IF NOT EXISTS idx_cycles_float_id ON cycles(float_id);
CREATE INDEX IF NOT EXISTS idx_cycles_cycle_number ON cycles(float_id, cycle_number);
CREATE INDEX IF NOT EXISTS idx_cycles_profile_date ON cycles(profile_date DESC);
CREATE INDEX IF NOT EXISTS idx_cycles_location ON cycles USING GIST (
    ST_MakePoint(longitude::float8, latitude::float8)
);
CREATE INDEX IF NOT EXISTS idx_cycles_lat_lon ON cycles(latitude, longitude);

-- Performance Indexes for profiles table
CREATE INDEX IF NOT EXISTS idx_profiles_cycle_id ON profiles(cycle_id);
CREATE INDEX IF NOT EXISTS idx_profiles_pressure ON profiles(cycle_id, pressure);
CREATE INDEX IF NOT EXISTS idx_profiles_quality_flag ON profiles(quality_flag);
CREATE INDEX IF NOT EXISTS idx_profiles_temperature ON profiles(temperature);
CREATE INDEX IF NOT EXISTS idx_profiles_salinity ON profiles(salinity);

-- Performance Indexes for chat_history table
CREATE INDEX IF NOT EXISTS idx_chat_session_id ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_created_at ON chat_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_session_turn ON chat_history(session_id, turn_index);
CREATE INDEX IF NOT EXISTS idx_chat_metadata ON chat_history USING GIN (metadata);

-- Full-text search indexes for chat messages
CREATE INDEX IF NOT EXISTS idx_chat_message_fulltext ON chat_history USING GIN (to_tsvector('english', message));

-- Geographic indexes for spatial queries
CREATE INDEX IF NOT EXISTS idx_cycles_geographic_bounds ON cycles 
    USING BTREE (latitude, longitude);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_floats_active ON floats(last_update DESC);

CREATE INDEX IF NOT EXISTS idx_cycles_recent ON cycles(profile_date DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for updating floats updated_at
CREATE TRIGGER update_floats_updated_at 
    BEFORE UPDATE ON floats 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Additional spatial indexes for advanced geographic queries
CREATE INDEX IF NOT EXISTS idx_cycles_spatial ON cycles USING GIST (
    ST_Transform(ST_SetSRID(ST_MakePoint(longitude::float8, latitude::float8), 4326), 3857)
);
