import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownTextProps {
  content: string;
  fontSize?: number;
  fontWeight?: 'normal' | 'medium' | 'semibold' | 'bold';
  textAlign?: 'left' | 'center' | 'right';
  textColor?: string;
  className?: string;
}

export default function MarkdownText({
  content,
  fontSize = 12,
  fontWeight = 'normal',
  textAlign = 'left',
  textColor = '#1f2937',
  className = '',
}: MarkdownTextProps) {
  const fontWeightClass =
    fontWeight === 'bold'
      ? 'font-bold'
      : fontWeight === 'semibold'
      ? 'font-semibold'
      : fontWeight === 'medium'
      ? 'font-medium'
      : 'font-normal';

  const textAlignClass =
    textAlign === 'left'
      ? 'text-left'
      : textAlign === 'right'
      ? 'text-right'
      : 'text-center';

  return (
    <div
      className={`markdown-content ${fontWeightClass} ${textAlignClass} ${className}`}
      style={{
        fontSize: `${fontSize}px`,
        color: textColor,
      }}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Style headings
          h1: ({ node, ...props }) => (
            <h1 className="text-2xl font-bold mb-2 mt-4 first:mt-0" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-xl font-bold mb-2 mt-3 first:mt-0" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-lg font-bold mb-1 mt-2 first:mt-0" {...props} />
          ),
          h4: ({ node, ...props }) => (
            <h4 className="text-base font-bold mb-1 mt-2 first:mt-0" {...props} />
          ),
          h5: ({ node, ...props }) => (
            <h5 className="text-sm font-bold mb-1 mt-1 first:mt-0" {...props} />
          ),
          h6: ({ node, ...props }) => (
            <h6 className="text-xs font-bold mb-1 mt-1 first:mt-0" {...props} />
          ),
          // Style paragraphs
          p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
          // Style lists
          ul: ({ node, ...props }) => (
            <ul className="list-disc list-inside mb-2 space-y-1" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />
          ),
          li: ({ node, ...props }) => <li className="ml-2" {...props} />,
          // Style links
          a: ({ node, ...props }) => (
            <a
              className="text-blue-600 hover:text-blue-800 underline"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            />
          ),
          // Style code
          code: ({ node, inline, ...props }: any) =>
            inline ? (
              <code
                className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono"
                {...props}
              />
            ) : (
              <code
                className="block bg-gray-100 p-2 rounded text-sm font-mono overflow-x-auto mb-2"
                {...props}
              />
            ),
          // Style blockquotes
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-l-4 border-gray-300 pl-4 italic my-2"
              {...props}
            />
          ),
          // Style horizontal rules
          hr: ({ node, ...props }) => <hr className="my-4 border-gray-300" {...props} />,
          // Style tables
          table: ({ node, ...props }) => (
            <table className="border-collapse border border-gray-300 mb-2" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th className="border border-gray-300 px-2 py-1 bg-gray-100 font-bold" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="border border-gray-300 px-2 py-1" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
