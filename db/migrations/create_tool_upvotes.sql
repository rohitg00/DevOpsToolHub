-- Drop existing tables if they exist
DROP TABLE IF EXISTS public.tool_upvotes CASCADE;
DROP TABLE IF EXISTS public.tool_upvote_tracking CASCADE;
DROP FUNCTION IF EXISTS public.increment_upvotes CASCADE;
DROP FUNCTION IF EXISTS public.handle_upvote CASCADE;

-- Add upvotes column to tools table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'tools' 
                  AND column_name = 'upvotes') THEN
        ALTER TABLE public.tools ADD COLUMN upvotes INTEGER DEFAULT 0;
    END IF;
END $$;

-- Create the tool_upvote_tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.tool_upvote_tracking (
    id SERIAL PRIMARY KEY,
    tool_name TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tool_name FOREIGN KEY (tool_name) REFERENCES public.tools(name) ON DELETE CASCADE,
    CONSTRAINT unique_vote UNIQUE(tool_name, ip_address)
);

-- Enable RLS
ALTER TABLE public.tool_upvote_tracking ENABLE ROW LEVEL SECURITY;

-- Create policy to allow inserts and deletes
DROP POLICY IF EXISTS tool_upvote_insert_policy ON public.tool_upvote_tracking;
CREATE POLICY tool_upvote_insert_policy ON public.tool_upvote_tracking
    FOR ALL TO authenticated, anon
    USING (true)
    WITH CHECK (true);

-- Create policy to allow reads
DROP POLICY IF EXISTS tool_upvote_select_policy ON public.tool_upvote_tracking;
CREATE POLICY tool_upvote_select_policy ON public.tool_upvote_tracking
    FOR SELECT TO authenticated, anon
    USING (true);

-- Create or replace the upvote function to handle both upvoting and removing upvotes
CREATE OR REPLACE FUNCTION public.handle_upvote(p_tool_name TEXT, p_ip_address TEXT)
RETURNS jsonb AS $$
DECLARE
    v_current_upvotes INTEGER;
    v_existing_vote BOOLEAN;
    v_result jsonb;
BEGIN
    -- Check if user has already upvoted
    SELECT EXISTS (
        SELECT 1 FROM public.tool_upvote_tracking
        WHERE tool_name = p_tool_name AND ip_address = p_ip_address
    ) INTO v_existing_vote;

    IF v_existing_vote THEN
        -- Remove upvote
        DELETE FROM public.tool_upvote_tracking
        WHERE tool_name = p_tool_name AND ip_address = p_ip_address;

        -- Decrement upvotes
        UPDATE public.tools 
        SET upvotes = GREATEST(upvotes - 1, 0)
        WHERE name = p_tool_name
        RETURNING upvotes INTO v_current_upvotes;

        v_result := jsonb_build_object(
            'action', 'removed',
            'upvotes', v_current_upvotes,
            'message', 'Upvote removed successfully'
        );
    ELSE
        -- Add upvote
        INSERT INTO public.tool_upvote_tracking (tool_name, ip_address)
        VALUES (p_tool_name, p_ip_address);

        -- Increment upvotes
        UPDATE public.tools 
        SET upvotes = COALESCE(upvotes, 0) + 1
        WHERE name = p_tool_name
        RETURNING upvotes INTO v_current_upvotes;

        v_result := jsonb_build_object(
            'action', 'added',
            'upvotes', v_current_upvotes,
            'message', 'Upvote added successfully'
        );
    END IF;

    RETURN v_result;

EXCEPTION 
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error managing upvote: %', SQLERRM USING ERRCODE = SQLSTATE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; 