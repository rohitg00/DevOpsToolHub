import { pgTable, text, integer, boolean } from 'drizzle-orm/pg-core';

export const tools = pgTable('tools', {
  name: text('name').primaryKey(),
  description: text('description').notNull(),
  category: text('category').notNull(),
  importance: text('importance').notNull(),
  isOpenSource: boolean('is_open_source').notNull(),
  url: text('url').notNull(),
  documentationUrl: text('documentation_url'),
  githubUrl: text('github_url'),
  tags: text('tags').array().notNull(),
  upvotes: integer('upvotes').default(0),
  stars: text('stars'),
  language: text('language'),
  topics: text('topics')
});

export type Tool = typeof tools.$inferSelect;
export type NewTool = typeof tools.$inferInsert;