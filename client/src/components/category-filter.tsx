import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface CategoryFilterProps {
  selected: string[];
  onChange: (categories: string[]) => void;
}

export function CategoryFilter({ selected, onChange }: CategoryFilterProps) {
  // Fetch unique categories from tools
  const { data: tools = [] } = useQuery<Tool[]>({
    queryKey: ["/api/tools"],
  });

  // Get unique categories from all tools
  const categories = Array.from(new Set(
    tools.map(tool => tool.category)
      .concat(...tools.map(tool => tool.categories || []))
  )).sort();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="h-8 border-dashed">
          {selected.length > 0 ? `${selected.length} selected` : "Categories"}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[200px]">
        {categories.map((category) => (
          <DropdownMenuCheckboxItem
            key={category}
            checked={selected.includes(category)}
            onCheckedChange={(checked) => {
              if (checked) {
                onChange([...selected, category]);
              } else {
                onChange(selected.filter((c) => c !== category));
              }
            }}
          >
            {category}
          </DropdownMenuCheckboxItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
