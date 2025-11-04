import { useRef, useState } from 'react';
import { Download, Upload, Trash2, Settings, FileJson, Play } from 'lucide-react';
import { useGraphStore } from '@/stores/graphStore';
import { useAppStore } from '@/stores/appStore';
import { useCreateAgent, useCreateRun } from '@/hooks/useRuntime';
import RunInputModal from './RunInputModal';

interface ToolbarProps {
  onOpenSettings: () => void;
}

export default function Toolbar({ onOpenSettings }: ToolbarProps) {
  const { exportGraph, loadGraph, clearGraph, metadata, memory, validateGraph, linkToAgent } = useGraphStore();
  const { switchToRuntime } = useAppStore();
  const createAgent = useCreateAgent();
  const createRun = useCreateRun();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showRunModal, setShowRunModal] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [pendingAgentId, setPendingAgentId] = useState<string | null>(null);

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

  const handleRun = () => {
    // Validate the graph
    const validation = validateGraph();
    setValidationResult(validation);

    // Show modal regardless (modal will handle errors)
    setShowRunModal(true);
  };

  const handleRunWithInputs = async (inputs: Record<string, any>) => {
    try {
      const graph = exportGraph();

      // Smart detection: check if linked to an agent
      const agentId = metadata.linkedAgentId;

      let targetAgentId: string;

      if (agentId) {
        // Update existing agent (not implementing update for now, just use existing)
        targetAgentId = agentId;
      } else {
        // Create new temporary agent
        const createResult = await createAgent.mutateAsync({
          name: graph.metadata.name,
          description: graph.metadata.description,
          framework: 'pydantic_ai',
          graph_definition: graph,
        });

        targetAgentId = createResult.id;

        // Link the graph to this agent
        linkToAgent(targetAgentId);
      }

      // Create and start the run
      const runResult = await createRun.mutateAsync({
        agentId: targetAgentId,
        data: { inputs },
      });

      // Close modal
      setShowRunModal(false);

      // Switch to Runtime view with agent and run selected
      switchToRuntime({
        agentId: targetAgentId,
        runId: runResult.id,
      });
    } catch (error) {
      console.error('Failed to run graph:', error);
      alert(`Failed to run graph: ${(error as Error).message}`);
    }
  };

  return (
    <>
      <RunInputModal
        isOpen={showRunModal}
        onClose={() => setShowRunModal(false)}
        onRun={handleRunWithInputs}
        graphName={metadata.name}
        memory={memory}
        validation={validationResult || { isValid: true, errors: [], warnings: [], hasIssues: false }}
      />
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

        <div className="h-6 w-px bg-gray-300" />

        <button
          onClick={handleRun}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
          title="Run graph"
        >
          <Play className="w-4 h-4" />
          Run
        </button>

        <div className="h-6 w-px bg-gray-300" />

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
    </>
  );
}
