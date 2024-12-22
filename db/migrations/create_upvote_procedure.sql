CREATE OR REPLACE FUNCTION handle_upvote(p_tool_name TEXT, p_ip_address TEXT)
RETURNS jsonb AS $$
DECLARE
    v_current_upvotes INTEGER;
    v_existing_vote BOOLEAN;
    v_result jsonb;
BEGIN
    -- Check if user has already upvoted
    SELECT EXISTS (
        SELECT 1 FROM tool_upvote_tracking
        WHERE tool_name = p_tool_name AND ip_address = p_ip_address
    ) INTO v_existing_vote;

    IF v_existing_vote THEN
        RAISE EXCEPTION 'Already upvoted' USING ERRCODE = '23505';
    END IF;

    -- Insert tracking record
    INSERT INTO tool_upvote_tracking (tool_name, ip_address)
    VALUES (p_tool_name, p_ip_address);

    -- Increment upvotes
    UPDATE tools 
    SET upvotes = COALESCE(upvotes, 0) + 1
    WHERE name = p_tool_name
    RETURNING upvotes INTO v_current_upvotes;

    v_result := jsonb_build_object(
        'upvotes', v_current_upvotes,
        'message', 'Upvote successful'
    );

    RETURN v_result;

EXCEPTION 
    WHEN unique_violation THEN
        RAISE EXCEPTION 'Already upvoted' USING ERRCODE = '23505';
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error upvoting: %', SQLERRM USING ERRCODE = SQLSTATE;
END;
$$ LANGUAGE plpgsql; 