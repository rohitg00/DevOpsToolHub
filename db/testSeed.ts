import { supabase } from "./index";
import { seedTools } from "./seed";

export async function seedTestDatabase() {
  try {
    // First clear the tool_upvotes table since it references tools
    const { error: deleteUpvotesError } = await supabase
      .from('tool_upvote_tracking')
      .delete()
      .neq('tool_name', '');

    if (deleteUpvotesError && deleteUpvotesError.code !== '42P01') throw deleteUpvotesError;

    // Transform tools and remove duplicates based on name
    const uniqueTools = new Map();
    seedTools.forEach(tool => {
      uniqueTools.set(tool.name, {
        name: tool.name,
        description: tool.description,
        category: tool.category,
        importance: tool.importance,
        is_open_source: tool.isOpenSource,
        url: tool.url,
        documentation_url: tool.documentationUrl,
        github_url: tool.githubUrl,
        tags: tool.tags,
        upvotes: 0
      });
    });

    const transformedTools = Array.from(uniqueTools.values());

    // Clear existing tools data
    const { error: deleteToolsError } = await supabase
      .from('tools')
      .delete()
      .neq('name', '');

    if (deleteToolsError) throw deleteToolsError;

    // Insert new data in batches of 50 to avoid request size limits
    for (let i = 0; i < transformedTools.length; i += 50) {
      const batch = transformedTools.slice(i, i + 50);
      const { error: insertError } = await supabase
        .from('tools')
        .upsert(batch, {
          onConflict: 'name'
        });

      if (insertError) throw insertError;
      console.log(`Inserted batch ${i / 50 + 1} of ${Math.ceil(transformedTools.length / 50)}`);
    }

    console.log(`Database seeded successfully with ${transformedTools.length} tools`);
  } catch (error) {
    console.error('Error seeding database:', error);
    throw error;
  }
}
