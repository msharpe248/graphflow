import { useState, useEffect } from 'react';
import { Activity, AlertCircle } from 'lucide-react';
import { useHealth, useAgent, useRun, useAgents, useRuns } from '@/hooks/useRuntime';
import { useAppStore } from '@/stores/appStore';
import { Agent, AgentRun } from '@/types/runtime';
import AgentsList from './AgentsList';
import RunsList from './RunsList';
import RunDetail from './RunDetail';

export default function RuntimeView() {
  const { data: health, error: healthError } = useHealth();
  const { data: agents } = useAgents();
  const { runtimeContext } = useAppStore();
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);

  // Fetch runs for the selected agent
  const { data: runs } = useRuns(selectedAgent?.id || null);

  // Fetch agent and run from context if provided
  const { data: contextAgent } = useAgent(runtimeContext?.agentId || null);
  const { data: contextRun } = useRun(
    runtimeContext?.agentId || null,
    runtimeContext?.runId || null
  );

  // Auto-select agent and run when context is provided
  useEffect(() => {
    if (contextAgent) {
      setSelectedAgent(contextAgent);
    }
  }, [contextAgent]);

  useEffect(() => {
    if (contextRun) {
      setSelectedRun(contextRun);
    }
  }, [contextRun]);

  // Clear selection if selected agent no longer exists in the list
  useEffect(() => {
    if (selectedAgent && agents) {
      const agentStillExists = agents.some(agent => agent.id === selectedAgent.id);
      if (!agentStillExists) {
        setSelectedAgent(null);
        setSelectedRun(null);
      }
    }
  }, [agents, selectedAgent]);

  // Clear selection if selected run no longer exists in the list
  useEffect(() => {
    if (selectedRun && runs) {
      const runStillExists = runs.some(run => run.id === selectedRun.id);
      if (!runStillExists) {
        setSelectedRun(null);
      }
    }
  }, [runs, selectedRun]);

  // Show error if runtime is not available
  if (healthError) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="max-w-md p-6 bg-white border-2 border-red-200 rounded-lg">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-red-50 rounded-lg">
              <AlertCircle className="w-6 h-6 text-red-600" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">Runtime Not Available</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Could not connect to the GraphFlow runtime server. Make sure it's running:
          </p>
          <pre className="p-3 bg-gray-50 border border-gray-200 rounded text-xs font-mono mb-4">
            graphflow-runtime --port 8000
          </pre>
          <p className="text-xs text-gray-500">
            Expected at: <code className="text-blue-600">http://localhost:8000</code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header with health status */}
      <div className="h-12 bg-white border-b border-gray-200 px-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-green-600" />
          <h1 className="text-lg font-bold text-gray-900">Runtime</h1>
        </div>
        {health && (
          <div className="flex items-center gap-3 text-sm">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-gray-600">{health.status}</span>
            </div>
            <div className="text-gray-600">
              Active runs: <span className="font-medium text-gray-900">{health.active_runs}</span>
            </div>
          </div>
        )}
      </div>

      {/* Main content - 3 column layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Agents list */}
        <div className="w-80 border-r border-gray-200 bg-gray-50">
          <AgentsList
            onSelectAgent={(agent) => {
              setSelectedAgent(agent);
              setSelectedRun(null);
            }}
            selectedAgentId={selectedAgent?.id}
          />
        </div>

        {/* Middle: Runs list (only show if agent selected) */}
        {selectedAgent ? (
          <div className="w-80 border-r border-gray-200 bg-gray-50">
            <RunsList
              agent={selectedAgent}
              onSelectRun={setSelectedRun}
              selectedRunId={selectedRun?.id}
            />
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">Select an agent to view runs</p>
            </div>
          </div>
        )}

        {/* Right: Run detail (only show if run selected) */}
        {selectedRun && selectedAgent ? (
          <div className="flex-1 bg-white">
            <RunDetail agentId={selectedAgent.id} runId={selectedRun.id} />
          </div>
        ) : selectedAgent ? (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">Select a run to view details</p>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
