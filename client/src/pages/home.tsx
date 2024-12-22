import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Tool } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { SearchBar } from "@/components/search-bar";
import { CategoryFilter } from "@/components/category-filter";
import { ImportanceFilter } from "@/components/importance-filter";
import { ToolGrid } from "@/components/tool-grid";

export function Home() {
  const [search, setSearch] = useState("");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedImportance, setSelectedImportance] = useState<string[]>([]);
  const [showOpenSourceOnly, setShowOpenSourceOnly] = useState(false);

  const { data: tools = [] } = useQuery<Tool[]>({
    queryKey: ["/api/tools"],
    queryFn: async () => {
      const response = await fetch("/api/tools");
      if (!response.ok) throw new Error("Failed to fetch tools");
      return response.json();
    },
  });

  const filteredTools = tools.filter((tool) => {
    const matchesSearch = tool.name.toLowerCase().includes(search.toLowerCase());
    const matchesCategory =
      selectedCategories.length === 0 ||
      selectedCategories.includes(tool.category) ||
      (tool.categories && selectedCategories.some(cat => tool.categories?.includes(cat)));
    const matchesImportance =
      selectedImportance.length === 0 ||
      selectedImportance.includes(tool.importance || "");
    const matchesOpenSource = !showOpenSourceOnly || tool.is_open_source;

    return matchesSearch && matchesCategory && matchesImportance && matchesOpenSource;
  });

  return (
    <div className="container mx-auto py-8">
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold mb-4 text-blue-500">
          DevOps Tools Directory
        </h1>
        <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto mb-4">
          Discover and compare the best tools for your DevOps workflow
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center mt-6 mb-8">
          <a 
            href="https://github.com/rohitg00/DevOpsCommunity"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
            </svg>
            Star DevOps Community
          </a>
          <a 
            href="https://x.com/i/communities/1523681883384549376"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 bg-[#1DA1F2] text-white rounded-lg hover:bg-[#1a8cd8] transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
            Join DevOps Community
          </a>
          <a 
            href="https://www.devopscommunity.in/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            DevOps Community Portal
          </a>
          <a 
            href="https://interview.devopscommunity.in/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Practice DevOps Interview
          </a>
        </div>
      </div>

      <div className="space-y-4 mb-8">
        <div className="flex gap-4">
          <div className="flex-1">
            <SearchBar value={search} onChange={setSearch} />
          </div>
        </div>

        <div className="flex gap-4 flex-wrap">
          <CategoryFilter
            categories={["CI/CD", "Monitoring", "Container", "Cloud", "Security"]}
            selected={selectedCategories}
            onChange={setSelectedCategories}
          />
          <ImportanceFilter
            importanceLevels={["Essential", "Recommended", "Optional"]}
            selected={selectedImportance}
            onChange={setSelectedImportance}
          />
          <Button
            variant="outline"
            onClick={() => setShowOpenSourceOnly(!showOpenSourceOnly)}
            className={showOpenSourceOnly ? "bg-blue-500 text-white border-blue-500" : ""}
          >
            {showOpenSourceOnly ? "All Tools" : "Open Source Only"}
          </Button>
        </div>
      </div>

      <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
        Showing {filteredTools.length} tools
      </div>

      <ToolGrid tools={filteredTools} />
    </div>
  );
}