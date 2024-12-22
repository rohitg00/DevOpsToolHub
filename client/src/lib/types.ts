export interface Tool {
  id: number;
  name: string;
  description: string;
  category: string;
  categories?: string[];
  importance: string;
  is_open_source: boolean;
  upvotes: number;
  url?: string;
  github_url?: string;
  documentation_url?: string;
  readme?: string;
  github_data?: {
    stars: number;
    forks: number;
    last_update: string;
    issues: number;
  };
}
