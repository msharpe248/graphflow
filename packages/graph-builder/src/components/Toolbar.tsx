import { useRef } from 'react';
import { Download, Upload, Trash2, Settings, FileJson } from 'lucide-react';
import { useGraphStore } from '@/stores/graphStore';

interface ToolbarProps {
  onOpenSettings: () => void;
}

export default function Toolbar({ onOpenSettings }: ToolbarProps) {
  const { exportGraph, loadGraph, clearGraph, metadata } = useGraphStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleExport = () => {
    const graph = exportGraph();
    const json = JSON.stringify(graph, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${metadata.name.replace(/\s+/g, '_').toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target?.result as string);
        loadGraph(json);
      } catch (error) {
        alert('Failed to load graph: Invalid JSON');
        console.error(error);
      }
    };
    reader.readAsText(file);
  };

  const handleClear = () => {
    if (confirm('Clear the entire graph? This cannot be undone.')) {
      clearGraph();
    }
  };

  return (
    <div className="h-14 bg-white border-b border-gray-200 px-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <FileJson className="w-6 h-6 text-primary" />
          <h1 className="text-xl font-bold text-gray-900">GraphFlow Builder</h1>
        </div>
        <div className="text-sm text-gray-600">
          {metadata.name}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handleImport}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          title="Import graph from JSON"
        >
          <Upload className="w-4 h-4" />
          Import
        </button>

        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          title="Export graph to JSON"
        >
          <Download className="w-4 h-4" />
          Export
        </button>

        <button
          onClick={onOpenSettings}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          title="Graph settings"
        >
          <Settings className="w-4 h-4" />
          Settings
        </button>

        <button
          onClick={handleClear}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-md transition-colors"
          title="Clear graph"
        >
          <Trash2 className="w-4 h-4" />
          Clear
        </button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
}
