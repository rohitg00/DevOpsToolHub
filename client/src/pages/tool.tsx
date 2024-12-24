import { useState, useEffect } from "react";
import { Tool } from "@/lib/types";
import { ToolPopularity } from "@/components/tool-popularity";
import { Button } from "@/components/ui/button";
import { ExternalLink, Github, ChevronDown, ChevronUp } from "lucide-react";
import { Markdown } from "@/components/ui/markdown";

export function ToolPage({ params }: { params: { name: string } }) {
  const [tool, setTool] = useState<Tool | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showReadme, setShowReadme] = useState(false);

  useEffect(() => {
    const fetchTool = async () => {
      if (!params.name) {
        setError('No tool name provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await fetch(`/api/tools/${params.name}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch tool: ${response.statusText}`);
        }
        
        const data = await response.json();
        setTool(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching tool:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch tool');
        setTool(null);
      } finally {
        setLoading(false);
      }
    };

    fetchTool();
  }, [params.name]);

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  if (!tool) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div>Tool not found</div>
      </div>
    );
  }

  const trimmedUrl = tool?.url?.replace('git+', '');

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-4xl font-bold mb-2">{tool.name}</h1>
          <p className="text-lg text-gray-600 dark:text-gray-300 mb-4">
            {tool.description}
          </p>
          <div className="flex gap-2 mb-4">
            <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100 px-3 py-1 rounded-full text-sm">
              {Array.isArray(tool.categories) ? tool.categories[0] : tool.category}
            </span>
            <span className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-100 px-3 py-1 rounded-full text-sm">
              {tool.importance}
            </span>
          </div>
          <div className="flex gap-4">
            {tool.url && (
              <Button variant="outline" asChild>
                <a href={trimmedUrl?.replace(" ", "")} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Website
                </a>
              </Button>
            )}
            {tool.url && (
              <Button variant="outline" asChild>
                <a href={trimmedUrl?.replace(" ", "")} target="_blank" rel="noopener noreferrer">
                  <Github className="w-4 h-4 mr-2" />
                  GitHub
                </a>
              </Button>
            )}
            <ToolPopularity tool={tool} />
          </div>
        </div>
      </div>
    </div>
  );
}

