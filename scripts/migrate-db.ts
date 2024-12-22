import { createClient } from '@supabase/supabase-js';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';
import dotenv from 'dotenv';
import { supabase } from '../db';
// Load environment variables
dotenv.config();

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE;

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing Supabase credentials');
  process.exit(1);
}

// Create Supabase client with service role key
const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

// Get current file path and directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = dirname(dirname(__filename));

async function verifySetup() {
  // Check if table exists
  const { data: tableInfo, error: tableError } = await supabase
    .from('tool_upvote_tracking')
    .select('*')
    .limit(1);

  if (tableError) {
    console.error('Error verifying table:', tableError);
    return false;
  }

  // Try to call the function
  const { error: functionError } = await supabase.rpc('handle_upvote', {
    p_tool_name: 'test',
    p_ip_address: '127.0.0.1'
  });

  // We expect a foreign key error since 'test' tool doesn't exist
  if (functionError && !functionError.message.includes('foreign key')) {
    console.error('Error verifying function:', functionError);
    return false;
  }

  return true;
}

async function runMigration() {
  try {
    // Read all migration files in order
    const upvotesMigration = fs.readFileSync(
      join(rootDir, 'db/migrations/create_tool_upvotes.sql'), 
      'utf8'
    );
    const procedureMigration = fs.readFileSync(
      join(rootDir, 'db/migrations/create_upvote_procedure.sql'), 
      'utf8'
    );

    // Execute migrations in sequence
    const migrations = [
      {
        name: 'Create upvotes table',
        sql: upvotesMigration
      },
      {
        name: 'Create upvote procedure',
        sql: procedureMigration
      }
    ];

    for (const migration of migrations) {
      console.log(`Running migration: ${migration.name}`);
      const { error } = await supabase.rpc('exec_sql', {
        sql_query: migration.sql
      });

      if (error) {
        console.error(`Error in ${migration.name}:`, error);
        throw error;
      }
      console.log(`Completed migration: ${migration.name}`);
    }

    console.log('All migrations completed successfully');

  } catch (error) {
    console.error('Migration failed:', error);
    process.exit(1);
  }
}

runMigration();