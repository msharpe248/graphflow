import { useState } from 'react';
import { Loader2, AlertCircle, CheckCircle, Clock, Square, Database, List } from 'lucide-react';
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
  const [activeTab, setActiveTab] = useState<'details' | 'memory' | 'execution'>('details');

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
    <div className="h-full flex flex-col min-w-0">
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
          <button
            onClick={() => setActiveTab('execution')}
            className={`
              flex items-center gap-1 px-3 py-2 text-sm font-medium transition-colors border-b-2
              ${
                activeTab === 'execution'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }
            `}
          >
            <List className="w-4 h-4" />
            Execution
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 min-w-0">
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
        ) : activeTab === 'memory' ? (
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
                  <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                    Inputs ({Object.keys(memory.inputs).length})
                  </h4>
                  {Object.keys(memory.inputs).length > 0 ? (
                    <div className="space-y-2">
                      {Object.entries(memory.inputs).map(([key, value]) => (
                        <div key={key} className="bg-blue-50 border border-blue-200 rounded p-2">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-xs font-semibold text-blue-900">
                              {key}
                            </span>
                          </div>
                          <div
                            className="mt-1 bg-white border border-blue-100 rounded p-2 text-xs font-mono"
                            style={{
                              maxHeight: '128px',
                              overflow: 'auto',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {typeof value === 'string'
                              ? value
                              : JSON.stringify(value, null, 2).split('\n').map((line, idx) => (
                                  <div key={idx} style={{ whiteSpace: 'nowrap' }}>
                                    {line}
                                  </div>
                                ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500 italic p-3 bg-gray-50 rounded border border-gray-200">
                      No inputs
                    </p>
                  )}
                </div>

                {/* Intermediate namespace */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                    Intermediate ({Object.keys(memory.intermediate).length})
                  </h4>
                  {Object.keys(memory.intermediate).length > 0 ? (
                    <div className="space-y-2">
                      {Object.entries(memory.intermediate).map(([key, value]) => (
                        <div key={key} className="bg-purple-50 border border-purple-200 rounded p-2">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-xs font-semibold text-purple-900">
                              {key}
                            </span>
                          </div>
                          <div
                            className="mt-1 bg-white border border-purple-100 rounded p-2 text-xs font-mono"
                            style={{
                              maxHeight: '128px',
                              overflow: 'auto',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {typeof value === 'string'
                              ? value
                              : JSON.stringify(value, null, 2).split('\n').map((line, idx) => (
                                  <div key={idx} style={{ whiteSpace: 'nowrap' }}>
                                    {line}
                                  </div>
                                ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500 italic p-3 bg-gray-50 rounded border border-gray-200">
                      No intermediate values
                    </p>
                  )}
                </div>

                {/* Outputs namespace */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                    Outputs ({Object.keys(memory.outputs).length})
                  </h4>
                  {Object.keys(memory.outputs).length > 0 ? (
                    <div className="space-y-2">
                      {Object.entries(memory.outputs).map(([key, value]) => (
                        <div key={key} className="bg-green-50 border border-green-200 rounded p-2">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-xs font-semibold text-green-900">
                              {key}
                            </span>
                          </div>
                          <div
                            className="mt-1 bg-white border border-green-100 rounded p-2 text-xs font-mono"
                            style={{
                              maxHeight: '128px',
                              overflow: 'auto',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {typeof value === 'string'
                              ? value
                              : JSON.stringify(value, null, 2).split('\n').map((line, idx) => (
                                  <div key={idx} style={{ whiteSpace: 'nowrap' }}>
                                    {line}
                                  </div>
                                ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500 italic p-3 bg-gray-50 rounded border border-gray-200">
                      No outputs
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500">Memory not available</p>
            )}
          </div>
        ) : (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Execution Log</h3>
            {run.execution_log && run.execution_log.length > 0 ? (
              <div className="space-y-3 min-w-0">
                {(() => {
                  // Group entries by step
                  const stepGroups = new Map<string, typeof run.execution_log>();
                  run.execution_log.forEach((entry) => {
                    const stepId = entry.step_id || 'unknown';
                    if (!stepGroups.has(stepId)) {
                      stepGroups.set(stepId, []);
                    }
                    stepGroups.get(stepId)!.push(entry);
                  });

                  return Array.from(stepGroups.entries()).map(([stepId, entries], idx) => {
                    const stepLabel = entries[0]?.step_label || stepId;
                    const reads = entries.filter(e => e.operation === 'read');
                    const writes = entries.filter(e => e.operation === 'write');

                    return (
                      <div
                        key={idx}
                        className="border border-gray-200 rounded-lg overflow-hidden min-w-0"
                      >
                        {/* Step Header */}
                        <div className="bg-gray-100 px-4 py-2 border-b border-gray-200">
                          <h4 className="font-semibold text-gray-900">{stepLabel}</h4>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {reads.length} input(s) read, {writes.length} output(s) written
                          </p>
                        </div>

                        <div className="p-4 space-y-3 min-w-0">
                          {/* Inputs (Reads) */}
                          {reads.length > 0 && (
                            <div className="min-w-0">
                              <h5 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                                Inputs
                              </h5>
                              <div className="space-y-2 min-w-0">
                                {reads.map((entry, readIdx) => (
                                  <div
                                    key={readIdx}
                                    className="bg-blue-50 border border-blue-200 rounded p-2 min-w-0"
                                  >
                                    <div className="flex items-center justify-between mb-1">
                                      <div className="flex items-center gap-2">
                                        <span className="font-mono text-xs font-semibold text-blue-900">
                                          {entry.key}
                                        </span>
                                        <span className="text-xs text-blue-600">
                                          ({entry.namespace})
                                        </span>
                                      </div>
                                    </div>
                                    {entry.value !== undefined && (
                                      <div className="mt-1 bg-white border border-blue-100 rounded p-2 text-xs font-mono"
                                           style={{
                                             maxHeight: '128px',
                                             overflow: 'auto',
                                             whiteSpace: 'nowrap'
                                           }}>
                                        {typeof entry.value === 'string'
                                          ? entry.value
                                          : JSON.stringify(entry.value, null, 2).split('\n').map((line, idx) => (
                                            <div key={idx} style={{ whiteSpace: 'nowrap' }}>{line}</div>
                                          ))
                                        }
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Outputs (Writes) */}
                          {writes.length > 0 && (
                            <div className="min-w-0">
                              <h5 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                                Outputs
                              </h5>
                              <div className="space-y-2 min-w-0">
                                {writes.map((entry, writeIdx) => (
                                  <div
                                    key={writeIdx}
                                    className="bg-green-50 border border-green-200 rounded p-2 min-w-0"
                                  >
                                    <div className="flex items-center justify-between mb-1">
                                      <div className="flex items-center gap-2">
                                        <span className="font-mono text-xs font-semibold text-green-900">
                                          {entry.key}
                                        </span>
                                        <span className="text-xs text-green-600">
                                          ({entry.namespace})
                                        </span>
                                      </div>
                                    </div>
                                    {entry.value !== undefined && (
                                      <div className="mt-1 bg-white border border-green-100 rounded p-2 text-xs font-mono"
                                           style={{
                                             maxHeight: '128px',
                                             overflow: 'auto',
                                             whiteSpace: 'nowrap'
                                           }}>
                                        {typeof entry.value === 'string'
                                          ? entry.value
                                          : JSON.stringify(entry.value, null, 2).split('\n').map((line, idx) => (
                                            <div key={idx} style={{ whiteSpace: 'nowrap' }}>{line}</div>
                                          ))
                                        }
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  });
                })()}
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                {run.status === 'completed'
                  ? 'No execution log available for this run'
                  : 'Execution log will appear when the run completes'}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
