import { supabase } from '../db';
import dotenv from 'dotenv';

dotenv.config();

async function clearUpvotes() {
  try {
    console.log('Clearing upvote tracking table...');
    const { error: trackingError } = await supabase
      .from('tool_upvote_tracking')
      .delete()
      .neq('tool_name', '');
    
    if (trackingError) throw trackingError;
    console.log('Upvote tracking cleared successfully');

    console.log('Resetting tool upvote counts...');
    const { error: toolsError } = await supabase
      .from('tools')
      .update({ upvotes: 0 })
      .neq('name', '');
    
    if (toolsError) throw toolsError;
    console.log('Tool upvote counts reset successfully');

    console.log('All upvote data cleared successfully');
  } catch (error) {
    console.error('Error clearing upvotes:', error);
    process.exit(1);
  }
}

clearUpvotes()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('Script failed:', error);
    process.exit(1);
  }); 