-- Drop existing tables and functions to start fresh
DROP TABLE IF EXISTS tool_upvote_tracking CASCADE;
DROP FUNCTION IF EXISTS handle_upvote CASCADE;

-- Add upvotes column to tools table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'tools' 
                  AND column_name = 'upvotes') THEN
        ALTER TABLE tools ADD COLUMN upvotes INTEGER DEFAULT 0;
    END IF;
END $$;

-- Create table to track upvotes by IP
CREATE TABLE tool_upvote_tracking (
    tool_name TEXT REFERENCES tools(name) ON DELETE CASCADE,
    ip_address TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tool_name, ip_address)
);

-- Create stored procedure for handling upvotes with better error handling
CREATE OR REPLACE FUNCTION handle_upvote(p_tool_name TEXT, p_ip_address TEXT)
RETURNS void AS $$
BEGIN
    -- Insert tracking record first (will fail if duplicate due to PRIMARY KEY)
    INSERT INTO tool_upvote_tracking (tool_name, ip_address)
    VALUES (p_tool_name, p_ip_address);

    -- If insert succeeded, increment upvotes
    UPDATE tools 
    SET upvotes = COALESCE(upvotes, 0) + 1
    WHERE name = p_tool_name;

EXCEPTION 
    WHEN unique_violation THEN
        RAISE EXCEPTION 'Already upvoted' USING ERRCODE = '23505';
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error upvoting: %', SQLERRM USING ERRCODE = SQLSTATE;
END;
$$ LANGUAGE plpgsql;