import { supabase } from '../db';
import { seedTestDatabase } from '../db/testSeed';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

// Get current file path and directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function runMigration() {
  try {
    const sqlPath = join(__dirname, '../db/migrations/increment_upvotes.sql');
    const sql = fs.readFileSync(sqlPath, 'utf8');
    
    // Execute SQL directly
    const { error } = await supabase.rpc('exec_sql', { sql_query: sql });
    if (error) throw error;
    
    console.log('Migration completed successfully');
  } catch (error) {
    console.error('Migration failed:', error);
    throw error;
  }
}

async function testUpvoting() {
  try {
    // First seed the database
    await seedTestDatabase();
    console.log('Database seeded successfully');

    // First verify the exact tool name from database
    const { data: toolData } = await supabase
      .from('tools')
      .select('name')
      .ilike('name', '%docker%curriculum%')
      .single();

    if (!toolData) {
      throw new Error('Test tool not found in database');
    }

    const testTool = toolData.name; // Use exact name from database
    const testIp = '127.0.0.1';

    // Get initial upvotes
    const { data: initialData } = await supabase
      .from('tools')
      .select('upvotes')
      .eq('name', testTool)
      .single();

    const initialUpvotes = initialData?.upvotes || 0;
    console.log(`Initial upvotes for ${testTool}: ${initialUpvotes}`);

    // First upvote using the stored procedure
    const { error: firstUpvoteError } = await supabase.rpc('handle_upvote', {
      p_tool_name: testTool,
      p_ip_address: testIp
    });

    if (!firstUpvoteError) {
      console.log('First upvote successful');
    } else {
      console.error('First upvote failed:', firstUpvoteError);
    }

    // Verify upvote count
    const { data: finalData } = await supabase
      .from('tools')
      .select('upvotes')
      .eq('name', testTool)
      .single();

    const finalUpvotes = finalData?.upvotes || 0;
    console.log(`Final upvotes for ${testTool}: ${finalUpvotes}`);

    // Try second upvote
    const { error: duplicateError } = await supabase.rpc('handle_upvote', {
      p_tool_name: testTool,
      p_ip_address: testIp
    });

    if (duplicateError) {
      console.log('✅ Duplicate upvote correctly prevented');
    } else {
      console.log('❌ Duplicate upvote was not prevented');
    }

    // Verify final count is correct
    if (finalUpvotes === initialUpvotes + 1) {
      console.log('✅ Final upvote count is correct');
    } else {
      console.log('❌ Final upvote count is incorrect');
      console.log(`Expected ${initialUpvotes + 1}, got ${finalUpvotes}`);
    }

  } catch (error) {
    console.error('Error testing upvotes:', error);
    throw error;
  }
}

// Run the test
testUpvoting(); 