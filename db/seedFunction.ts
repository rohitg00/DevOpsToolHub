import { db } from "./index";
import { tools } from "./schema";
import { sql } from "drizzle-orm";
import { seedTools } from "./seed";

export async function seedDatabase() {
  try {
    // Transform tools before insertion
    const transformedTools = seedTools.map(tool => ({
      ...tool,
      upvotes: 0,
      stars: null,
      language: null,
      topics: null
    }));

    // Insert all tools
    await db.insert(tools).values(transformedTools)
      .onConflictDoUpdate({
        target: tools.name,
        set: {
          description: sql`EXCLUDED.description`,
          category: sql`EXCLUDED.category`,
          importance: sql`EXCLUDED.importance`,
          isOpenSource: sql`EXCLUDED.is_open_source`,
          url: sql`EXCLUDED.url`,
          documentationUrl: sql`EXCLUDED.documentation_url`,
          githubUrl: sql`EXCLUDED.github_url`,
          tags: sql`EXCLUDED.tags`
        }
      });
    
    console.log("Database seeded successfully!");
  } catch (error) {
    console.error("Error seeding database:", error);
    throw error;
  }
}
