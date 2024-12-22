import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

interface MarkdownProps {
  children: string;
}

export function Markdown({ children }: MarkdownProps) {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // Custom components for markdown elements
          a: ({ node, ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-600" />
          ),
          pre: ({ node, ...props }) => (
            <pre {...props} className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg overflow-auto" />
          ),
          code: ({ node, inline, ...props }) => (
            inline ? 
              <code {...props} className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded" /> :
              <code {...props} className="block" />
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
} 