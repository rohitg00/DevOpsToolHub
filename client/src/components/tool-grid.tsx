import { Tool } from "@/lib/types";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Link } from "wouter";
import { Github, ExternalLink, Book } from "lucide-react";
import { ToolPopularity } from "./tool-popularity";

export function ToolGrid({ tools }: { tools: Tool[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {tools.map((tool) => (
        <Card key={tool.name} className="p-6">
          <div className="flex flex-col h-full">
            <h3 className="text-xl font-semibold mb-2">
              <Link href={`/tool/${encodeURIComponent(tool.name)}`}>
                {tool.name}
              </Link>
            </h3>
            
            <p className="text-muted-foreground mb-4 flex-grow">
              {tool.description}
            </p>

            {/* README Preview - show first 150 characters if available */}
            {tool.readme && (
              <div className="mb-4 p-3 bg-muted rounded-md">
                <p className="text-sm text-muted-foreground">
                  {tool.readme.slice(0, 150)}...
                </p>
                <Link href={`/tool/${encodeURIComponent(tool.name)}`}>
                  <Button variant="link" size="sm" className="mt-2 p-0">
                    Read more
                  </Button>
                </Link>
              </div>
            )}

            <div className="flex gap-2 mt-auto">
              {tool.url && (
                <Button variant="outline" size="sm" asChild>
                  <a href={tool.url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Website
                  </a>
                </Button>
              )}
              {tool.github_url && (
                <Button variant="outline" size="sm" asChild>
                  <a href={tool.github_url} target="_blank" rel="noopener noreferrer">
                    <Github className="w-4 h-4 mr-2" />
                    GitHub
                  </a>
                </Button>
              )}
              <ToolPopularity tool={tool} />
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
