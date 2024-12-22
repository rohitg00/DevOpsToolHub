import { supabase } from '../db';

async function runMigration() {
  try {
    // Drop existing tables if they exist
    await supabase.from('tool_upvote_tracking').delete().neq('tool_name', '');
    
    // Create tracking table
    const { error: createError } = await supabase.rpc('exec_sql', {
      sql_query: `
        -- Add upvotes column to tools table if it doesn't exist
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'tools' 
                          AND column_name = 'upvotes') THEN
                ALTER TABLE tools ADD COLUMN upvotes INTEGER DEFAULT 0;
            END IF;
        END $$;

        -- Create tracking table
        CREATE TABLE IF NOT EXISTS tool_upvote_tracking (
            id SERIAL PRIMARY KEY,
            tool_name TEXT REFERENCES tools(name) ON DELETE CASCADE,
            ip_address TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tool_name, ip_address)
        );
      `
    });

    if (createError) throw createError;
    console.log('Migration completed successfully');

  } catch (error) {
    console.error('Migration failed:', error);
    process.exit(1);
  }
}

runMigration(); 