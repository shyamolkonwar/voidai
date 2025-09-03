-- Migration: Create chat_history table for session-based chat memory
-- Created: 2025-01-03

CREATE TABLE IF NOT EXISTS chat_history (
    session_id UUID NOT NULL,
    turn_index SERIAL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    PRIMARY KEY (session_id, turn_index)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_history_role ON chat_history(role);

-- Add comment to table
COMMENT ON TABLE chat_history IS 'Stores chat conversation history for session-based context awareness';

-- Add comments to columns
COMMENT ON COLUMN chat_history.session_id IS 'Unique session identifier for the chat conversation';
COMMENT ON COLUMN chat_history.turn_index IS 'Auto-incrementing turn number within the session';
COMMENT ON COLUMN chat_history.role IS 'Role of the message sender (user, assistant, or system)';
COMMENT ON COLUMN chat_history.message IS 'The message content';
COMMENT ON COLUMN chat_history.created_at IS 'Timestamp when the message was created';
COMMENT ON COLUMN chat_history.metadata IS 'Additional metadata about the message (embeddings, tokens, etc.)';

-- Enable Row Level Security (optional - can be enabled later if needed)
-- CREATE POLICY "Allow all operations" ON chat_history FOR ALL USING (true);

-- Create a function to get recent chat history for a session
CREATE OR REPLACE FUNCTION get_recent_chat_history(
    p_session_id UUID,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    turn_index INTEGER,
    role VARCHAR,
    message TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ch.turn_index,
        ch.role,
        ch.message,
        ch.created_at
    FROM chat_history ch
    WHERE ch.session_id = p_session_id
    ORDER BY ch.turn_index DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Create a function to count messages in a session
CREATE OR REPLACE FUNCTION count_chat_messages(p_session_id UUID)
RETURNS INTEGER AS $$
DECLARE
    message_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO message_count
    FROM chat_history
    WHERE session_id = p_session_id;
    
    RETURN message_count;
END;
$$ LANGUAGE plpgsql;