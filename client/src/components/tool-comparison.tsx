import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tool } from "@/lib/types";

interface ToolComparisonProps {
  tools: Tool[];
}

export function ToolComparison({ tools }: ToolComparisonProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Feature</TableHead>
          {tools.map((tool) => (
            <TableHead key={tool.name}>{tool.name}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>Category</TableCell>
          {tools.map((tool) => (
            <TableCell key={tool.name}>
              {Array.isArray(tool.categories) ? tool.categories[0] : tool.category}
            </TableCell>
          ))}
        </TableRow>
        <TableRow>
          <TableCell>Type</TableCell>
          {tools.map((tool) => (
            <TableCell key={tool.name}>
              {tool.isOpenSource ? "Open Source" : "Proprietary"}
            </TableCell>
          ))}
        </TableRow>
        <TableRow>
          <TableCell>Importance</TableCell>
          {tools.map((tool) => (
            <TableCell key={tool.name}>{tool.importance}</TableCell>
          ))}
        </TableRow>
        <TableRow>
          <TableCell>Categories</TableCell>
          {tools.map((tool) => (
            <TableCell key={tool.name}>
              {Array.isArray(tool.categories) 
                ? tool.categories.join(", ") 
                : tool.category}
            </TableCell>
          ))}
        </TableRow>
      </TableBody>
    </Table>
  );
}
