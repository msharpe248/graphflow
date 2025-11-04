import { useState } from 'react';
import { Loader2, AlertCircle, CheckCircle, Clock, Square, Database } from 'lucide-react';
import { useRun, useMemory } from '@/hooks/useRuntime';

interface RunDetailProps {
  agentId: string;
  runId: string;
}

const STATUS_CONFIG = {
  pending: { icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' },
  running: { icon: Loader2, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
  completed: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
  failed: { icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' },
  stopped: { icon: Square, color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200' },
};

export default function RunDetail({ agentId, runId }: RunDetailProps) {
  const { data: run, isLoading: runLoading } = useRun(agentId, runId);
  const { data: memory, isLoading: memoryLoading } = useMemory(agentId, runId);
  const [activeTab, setActiveTab] = useState<'details' | 'memory'>('details');

  if (runLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!run) {
    return (
      <div className="p-4">
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-500">Run not found</p>
        </div>
      </div>
    );
  }

  const statusConfig = STATUS_CONFIG[run.status];
  const StatusIcon = statusConfig.icon;

  const formatDuration = () => {
    const start = new Date(run.started_at);
    const end = run.completed_at ? new Date(run.completed_at) : new Date();
    const duration = end.getTime() - start.getTime();
    return `${(duration / 1000).toFixed(2)}s`;
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-start gap-3 mb-3">
          <div className={`p-2 rounded-lg ${statusConfig.bg}`}>
            <StatusIcon
              className={`w-5 h-5 ${statusConfig.color} ${
                run.status === 'running' ? 'animate-spin' : ''
              }`}
            />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-bold text-gray-900">Run {runId.slice(0, 8)}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className={`inline-block px-2 py-1 ${statusConfig.bg} ${statusConfig.color} text-xs font-medium rounded`}>
                {run.status.toUpperCase()}
              </span>
              <span className="text-xs text-gray-500">{formatDuration()}</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('details')}
            className={`
              px-3 py-2 text-sm font-medium transition-colors border-b-2
              ${
                activeTab === 'details'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }
            `}
          >
            Details
          </button>
          <button
            onClick={() => setActiveTab('memory')}
            className={`
              flex items-center gap-1 px-3 py-2 text-sm font-medium transition-colors border-b-2
              ${
                activeTab === 'memory'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }
            `}
          >
            <Database className="w-4 h-4" />
            Memory
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'details' ? (
          <div className="space-y-4">
            {/* Timestamps */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Timeline</h3>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Started:</span>
                  <span className="text-gray-900">{new Date(run.started_at).toLocaleString()}</span>
                </div>
                {run.completed_at && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Completed:</span>
                      <span className="text-gray-900">{new Date(run.completed_at).toLocaleString()}</span>
                    </div>
                    {run.started_at && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Duration:</span>
                        <span className="text-gray-900">
                          {Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s
                        </span>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Inputs */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Inputs</h3>
              <pre className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs font-mono overflow-x-auto">
                {JSON.stringify(run.inputs, null, 2)}
              </pre>
            </div>

            {/* Outputs */}
            {run.outputs && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Outputs</h3>
                <pre className="p-3 bg-green-50 border border-green-200 rounded-lg text-xs font-mono overflow-x-auto">
                  {JSON.stringify(run.outputs, null, 2)}
                </pre>
              </div>
            )}

            {/* Error */}
            {run.error && (
              <div>
                <h3 className="text-sm font-semibold text-red-700 mb-2">Error</h3>
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-900">
                  {run.error}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Memory State</h3>
            {memoryLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : memory ? (
              <div className="space-y-4">
                {/* Inputs namespace */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">Inputs</h4>
                  <pre className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs font-mono overflow-x-auto">
                    {JSON.stringify(memory.inputs, null, 2)}
                  </pre>
                </div>

                {/* Intermediate namespace */}
                {Object.keys(memory.intermediate).length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">Intermediate</h4>
                    <pre className="p-3 bg-purple-50 border border-purple-200 rounded-lg text-xs font-mono overflow-x-auto">
                      {JSON.stringify(memory.intermediate, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Outputs namespace */}
                {Object.keys(memory.outputs).length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">Outputs</h4>
                    <pre className="p-3 bg-green-50 border border-green-200 rounded-lg text-xs font-mono overflow-x-auto">
                      {JSON.stringify(memory.outputs, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">Memory not available</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
