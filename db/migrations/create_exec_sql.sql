-- Function to execute SQL statements
CREATE OR REPLACE FUNCTION public.exec_sql(sql_query text)
RETURNS void AS $$
BEGIN
    EXECUTE sql_query;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; 