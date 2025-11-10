import { useState } from 'react';
import { Trash2, Play, Upload, Loader2 } from 'lucide-react';
import { useAgents, useDeleteAgent, useCreateAgent, useCreateRun } from '@/hooks/useRuntime';
import { useGraphStore } from '@/stores/graphStore';
import { Agent } from '@/types/runtime';
import RunInputModal from '../RunInputModal';
import { GraphDefinition } from '@/types/graph';

interface AgentsListProps {
  onSelectAgent: (agent: Agent) => void;
  selectedAgentId?: string;
}

export default function AgentsList({ onSelectAgent, selectedAgentId }: AgentsListProps) {
  const { data: agents, isLoading, error } = useAgents();
  const deleteAgent = useDeleteAgent();
  const createAgent = useCreateAgent();
  const createRun = useCreateRun();
  const exportGraph = useGraphStore((state) => state.exportGraph);
  const [framework, setFramework] = useState<'pydantic_ai' | 'langgraph'>('pydantic_ai');
  const [showRunModal, setShowRunModal] = useState(false);
  const [agentToRun, setAgentToRun] = useState<Agent | null>(null);

  const handleDelete = (agentId: string, agentName: string) => {
    if (confirm(`Delete agent "${agentName}"?`)) {
      deleteAgent.mutate(agentId);
    }
  };

  const handleUploadCurrent = () => {
    const graph = exportGraph();

    // Check if an agent with same name, version, and revision already exists
    const existingAgent = agents?.find(
      (agent) => {
        const graphDef = agent.graph_definition as GraphDefinition;
        return (
          graphDef.metadata.name === graph.metadata.name &&
          graphDef.metadata.version === graph.metadata.version &&
          graphDef.metadata.revision === graph.metadata.revision
        );
      }
    );

    if (existingAgent) {
      // Agent with same version.revision already exists, just select it
      onSelectAgent(existingAgent);
      return;
    }

    // Create new agent
    createAgent.mutate({
      name: graph.metadata.name,
      description: graph.metadata.description,
      framework,
      graph_definition: graph,
    });
  };

  const handleStartRun = (agent: Agent) => {
    setAgentToRun(agent);
    setShowRunModal(true);
  };

  const handleRunWithInputs = async (inputs: Record<string, any>, debugMode?: boolean) => {
    if (!agentToRun) return;

    try {
      await createRun.mutateAsync({
        agentId: agentToRun.id,
        data: {
          inputs,
          debug_mode: debugMode,
        },
      });

      // Close modal and select agent to view the new run
      setShowRunModal(false);
      setAgentToRun(null);
      onSelectAgent(agentToRun);
    } catch (error) {
      console.error('Failed to create run:', error);
      alert(`Failed to start run: ${(error as Error).message}`);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">Failed to load agents</p>
          <p className="text-xs text-red-600 mt-1">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-bold text-gray-900 mb-3">Runtime Agents</h2>

        {/* Upload current graph */}
        <div className="space-y-2">
          <div className="flex gap-2">
            <select
              value={framework}
              onChange={(e) => setFramework(e.target.value as any)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="pydantic_ai">Pydantic AI</option>
              <option value="langgraph">LangGraph</option>
            </select>
            <button
              onClick={handleUploadCurrent}
              disabled={createAgent.isPending}
              className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50"
            >
              {createAgent.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              Upload
            </button>
          </div>
          <p className="text-xs text-gray-500">
            Upload current graph from builder to runtime
          </p>
        </div>
      </div>

      {/* Agents list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {agents && agents.length > 0 ? (
          agents.map((agent) => (
            <div
              key={agent.id}
              className={`
                p-3 rounded-lg border-2 cursor-pointer transition-all
                ${
                  selectedAgentId === agent.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }
              `}
              onClick={() => onSelectAgent(agent)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm text-gray-900 truncate">
                    {agent.name}
                    {(() => {
                      const graphDef = agent.graph_definition as GraphDefinition;
                      const version = graphDef.metadata.version || '1.0';
                      const revision = graphDef.metadata.revision || 1;
                      return ` (${version}.${revision})`;
                    })()}
                  </div>
                  {agent.description && (
                    <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                      {agent.description}
                    </div>
                  )}
                  <div className="flex items-center gap-2 mt-2">
                    <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">
                      {agent.framework}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(agent.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartRun(agent);
                    }}
                    className="p-1.5 hover:bg-green-50 text-green-600 rounded transition-colors"
                    title="Start new run"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(agent.id, agent.name);
                    }}
                    className="p-1.5 hover:bg-red-50 text-red-600 rounded transition-colors"
                    title="Delete agent"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8">
            <p className="text-sm text-gray-500">No agents in runtime</p>
            <p className="text-xs text-gray-400 mt-1">
              Upload a graph from the builder to get started
            </p>
          </div>
        )}
      </div>

      {/* Run Input Modal */}
      {agentToRun && (
        <RunInputModal
          isOpen={showRunModal}
          onClose={() => {
            setShowRunModal(false);
            setAgentToRun(null);
          }}
          onRun={handleRunWithInputs}
          graphName={agentToRun.name}
          memory={(agentToRun.graph_definition as GraphDefinition).memory}
          validation={{ isValid: true, errors: [], warnings: [], hasIssues: false }}
        />
      )}
    </div>
  );
}
