-- Migration: Add full_response column to chat_history table for storing complete AI responses
-- Created: 2025-01-04

-- Add full_response column to store complete AI response data including tables, maps, etc.
ALTER TABLE chat_history 
ADD COLUMN IF NOT EXISTS full_response JSONB DEFAULT '{}'::jsonb;

-- Update comment for the metadata column to clarify its purpose
COMMENT ON COLUMN chat_history.metadata IS 'Additional metadata about the message (embeddings, tokens, etc.)';

-- Add comment for the new full_response column
COMMENT ON COLUMN chat_history.full_response IS 'Complete AI response data including tables, maps, visualizations, and structured data in JSON format';

-- Update the get_recent_chat_history function to include full_response
CREATE OR REPLACE FUNCTION get_recent_chat_history(
    p_session_id UUID,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    turn_index INTEGER,
    role VARCHAR,
    message TEXT,
    full_response JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ch.turn_index,
        ch.role,
        ch.message,
        ch.full_response,
        ch.created_at
    FROM chat_history ch
    WHERE ch.session_id = p_session_id
    ORDER BY ch.turn_index DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Create an index on full_response for better query performance
CREATE INDEX IF NOT EXISTS idx_chat_history_full_response ON chat_history USING GIN (full_response);

-- Update comment for the function
COMMENT ON FUNCTION get_recent_chat_history IS 'Retrieve recent chat history including complete AI response data';