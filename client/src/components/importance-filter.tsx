import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface ImportanceFilterProps {
  importanceLevels: string[];
  selected: string[];
  onChange: (levels: string[]) => void;
}

export function ImportanceFilter({ importanceLevels, selected, onChange }: ImportanceFilterProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline">
          Importance {selected.length > 0 && `(${selected.length})`}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-48">
        {importanceLevels.map((level) => (
          <DropdownMenuCheckboxItem
            key={level}
            checked={selected.includes(level)}
            onCheckedChange={(checked) => {
              if (checked) {
                onChange([...selected, level]);
              } else {
                onChange(selected.filter((l) => l !== level));
              }
            }}
          >
            {level}
          </DropdownMenuCheckboxItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
