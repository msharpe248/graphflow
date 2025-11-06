import { useState } from 'react';
import { Edit2, Eye } from 'lucide-react';
import { EditorProps } from './types';
import BaseEditorModal from './BaseEditorModal';

/**
 * MarkdownEditor - Modal editor for markdown content with live preview
 *
 * Schema configuration:
 * {
 *   "type": "string",
 *   "x-editor": "markdown",
 *   "description": "Markdown content"
 * }
 */
export default function MarkdownEditor({ value, onChange, schema }: EditorProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [tempValue, setTempValue] = useState('');
  const [showPreview, setShowPreview] = useState(true);

  const handleOpenModal = () => {
    setTempValue(value || '');
    setIsModalOpen(true);
  };

  const handleSave = () => {
    onChange(tempValue);
  };

  // Simple markdown to HTML conversion for preview
  const renderMarkdown = (text: string): string => {
    if (!text) return '<p class="text-gray-400 italic">No content</p>';

    let html = text;

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3 class="text-lg font-bold mt-4 mb-2">$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-4 mb-2">$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-4 mb-2">$1</h1>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="font-bold">$1</strong>');
    html = html.replace(/__(.+?)__/g, '<strong class="font-bold">$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em class="italic">$1</em>');
    html = html.replace(/_(.+?)_/g, '<em class="italic">$1</em>');

    // Code inline
    html = html.replace(/`(.+?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>');

    // Code blocks
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="bg-gray-100 p-3 rounded-md my-2 overflow-x-auto"><code class="text-sm font-mono">$2</code></pre>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">$1</a>');

    // Unordered lists
    html = html.replace(/^\* (.+)$/gim, '<li class="ml-4">$1</li>');
    html = html.replace(/^- (.+)$/gim, '<li class="ml-4">$1</li>');
    html = html.replace(/(<li class="ml-4">.*<\/li>)/s, '<ul class="list-disc list-inside my-2">$1</ul>');

    // Ordered lists
    html = html.replace(/^\d+\. (.+)$/gim, '<li class="ml-4">$1</li>');

    // Blockquotes
    html = html.replace(/^> (.+)$/gim, '<blockquote class="border-l-4 border-gray-300 pl-4 italic my-2">$1</blockquote>');

    // Horizontal rules
    html = html.replace(/^---$/gim, '<hr class="my-4 border-gray-300" />');

    // Paragraphs (lines that aren't already HTML tags)
    const lines = html.split('\n');
    html = lines.map(line => {
      if (line.trim() === '') return '';
      if (line.trim().startsWith('<')) return line;
      return `<p class="my-2">${line}</p>`;
    }).join('\n');

    return html;
  };

  // Format value for display (show first 50 chars)
  const formatValue = (): string => {
    if (!value || value.trim() === '') return 'No content';
    const preview = value.replace(/\n/g, ' ').substring(0, 50);
    return value.length > 50 ? `${preview}...` : preview;
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <div className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm text-gray-700 truncate">
          {formatValue()}
        </div>
        <button
          type="button"
          onClick={handleOpenModal}
          className="px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors flex items-center gap-1.5"
        >
          <Edit2 className="w-4 h-4" />
          Edit
        </button>
      </div>

      <BaseEditorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        title={schema.description || 'Edit Markdown'}
      >
        <div className="space-y-4">
          {/* Toggle Preview Button */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700">
              Markdown Content
            </label>
            <button
              type="button"
              onClick={() => setShowPreview(!showPreview)}
              className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors flex items-center gap-1.5"
            >
              <Eye className="w-3.5 h-3.5" />
              {showPreview ? 'Hide Preview' : 'Show Preview'}
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Editor */}
            <div className="space-y-2">
              <textarea
                value={tempValue}
                onChange={(e) => setTempValue(e.target.value)}
                placeholder="Enter markdown content..."
                className="w-full h-96 px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
              <p className="text-xs text-gray-500">
                Supports: **bold**, *italic*, `code`, # headers, lists, links, code blocks
              </p>
            </div>

            {/* Preview */}
            {showPreview && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  Preview
                </label>
                <div
                  className="w-full h-96 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 overflow-y-auto prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(tempValue) }}
                />
              </div>
            )}
          </div>
        </div>
      </BaseEditorModal>
    </>
  );
}
