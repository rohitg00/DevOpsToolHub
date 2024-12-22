import { Link } from "wouter";
import { Tool } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExternalLink, Github, Book } from "lucide-react";
import { ToolPopularity } from "@/components/tool-popularity";

interface ToolCardProps {
  tool: Tool;
}

export function ToolCard({ tool }: ToolCardProps) {
  return (
    <Card className="flex flex-col hover:border-blue-500/50 transition-colors">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="text-lg font-medium">{tool.name}</span>
          <ToolPopularity tool={tool} />
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">{tool.description}</p>
        
        <div className="flex flex-wrap gap-2">
          {tool.categories?.map((category) => (
            <Badge key={category} variant="secondary" className="bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200">
              {category}
            </Badge>
          ))}
          {tool.importance && (
            <Badge variant="outline">{tool.importance}</Badge>
          )}
          {tool.isOpenSource && (
            <Badge variant="default" className="bg-blue-500 text-white">
              Open Source
            </Badge>
          )}
        </div>

        <div className="flex gap-2 mt-auto pt-4">
          <Link href={`/tool/${encodeURIComponent(tool.name)}`}>
            <Button variant="default" size="sm" className="bg-blue-500 hover:bg-blue-600 text-white">
              View Details
            </Button>
          </Link>
          {tool.url && (
            <Button variant="outline" size="sm" asChild>
              <a href={tool.url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-2" />
                Website
              </a>
            </Button>
          )}
          {tool.githubUrl && (
            <Button variant="outline" size="sm" asChild>
              <a href={tool.githubUrl} target="_blank" rel="noopener noreferrer">
                <Github className="h-4 w-4 mr-2" />
                GitHub
              </a>
            </Button>
          )}
          {tool.docsUrl && (
            <Button variant="outline" size="sm" asChild>
              <a href={tool.docsUrl} target="_blank" rel="noopener noreferrer">
                <Book className="h-4 w-4 mr-2" />
                Docs
              </a>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
