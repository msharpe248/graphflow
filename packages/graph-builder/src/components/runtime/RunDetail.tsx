import { useState } from 'react';
import { Loader2, AlertCircle, CheckCircle, Clock, Square, Database, List, Network, History, Copy, Check, MessageCircle } from 'lucide-react';
import { useRun, useMemory, useSessionHistory } from '@/hooks/useRuntime';
import GraphDebugView from './GraphDebugView';

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
  const [activeTab, setActiveTab] = useState<'details' | 'memory' | 'execution' | 'graph' | 'session'>('details');
  const [copiedSessionId, setCopiedSessionId] = useState(false);

  // Fetch session history when session tab is active and we have a session_id
  const { data: sessionHistory, isLoading: sessionLoading } = useSessionHistory(
    run?.session_id || null,
    activeTab === 'session'
  );

  const copySessionId = async () => {
    if (run?.session_id) {
      await navigator.clipboard.writeText(run.session_id);
      setCopiedSessionId(true);
      setTimeout(() => setCopiedSessionId(false), 2000);
    }
  };

  // Auto-switch to graph tab if in debug mode
  useState(() => {
    if (run?.debug_mode && activeTab === 'details') {
      setActiveTab('graph');
    }
  });

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
          {run.debug_mode && (
            <button
              onClick={() => setActiveTab('graph')}
              className={`
                flex items-center gap-1 px-3 py-2 text-sm font-medium transition-colors border-b-2
                ${
                  activeTab === 'graph'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }
              `}
            >
              <Network className="w-4 h-4" />
              Graph
            </button>
          )}
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
          {run.session_id && (
            <button
              onClick={() => setActiveTab('session')}
              className={`
                flex items-center gap-1 px-3 py-2 text-sm font-medium transition-colors border-b-2
                ${
                  activeTab === 'session'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }
              `}
            >
              <MessageCircle className="w-4 h-4" />
              Session
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto min-w-0" style={{ padding: activeTab === 'graph' ? 0 : '1rem' }}>
        {activeTab === 'graph' ? (
          <GraphDebugView agentId={agentId} runId={runId} />
        ) : activeTab === 'details' ? (
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

            {/* Session ID */}
            {run.session_id && (
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <History className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-semibold text-purple-900">Session ID</h3>
                      <button
                        onClick={copySessionId}
                        className="flex items-center gap-1 px-2 py-1 text-xs text-purple-700 hover:bg-purple-100 rounded transition-colors"
                        title="Copy session ID to continue conversation"
                      >
                        {copiedSessionId ? (
                          <>
                            <Check className="w-3 h-3" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            Copy
                          </>
                        )}
                      </button>
                    </div>
                    <code className="text-xs text-purple-800 font-mono break-all block mt-1">
                      {run.session_id}
                    </code>
                    <p className="text-xs text-purple-600 mt-1">
                      Use this ID when starting a new run to continue the conversation.
                    </p>
                  </div>
                </div>
              </div>
            )}

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

                {/* Config namespace */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                    Config ({Object.keys(memory.config || {}).length})
                  </h4>
                  {memory.config && Object.keys(memory.config).length > 0 ? (
                    <div className="space-y-2">
                      {Object.entries(memory.config).map(([key, value]) => (
                        <div key={key} className="bg-orange-50 border border-orange-200 rounded p-2">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-xs font-semibold text-orange-900">
                              {key}
                            </span>
                          </div>
                          <div
                            className="mt-1 bg-white border border-orange-100 rounded p-2 text-xs font-mono"
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
                      No config values
                    </p>
                  )}
                </div>

                {/* Environment namespace */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                    Environment ({Object.keys(memory.environment || {}).length})
                  </h4>
                  {memory.environment && Object.keys(memory.environment).length > 0 ? (
                    <div className="space-y-2">
                      {Object.entries(memory.environment).map(([key, value]) => (
                        <div key={key} className="bg-yellow-50 border border-yellow-200 rounded p-2">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-xs font-semibold text-yellow-900">
                              {key}
                            </span>
                          </div>
                          <div
                            className="mt-1 bg-white border border-yellow-100 rounded p-2 text-xs font-mono"
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
                      No environment variables
                    </p>
                  )}
                </div>

                {/* Secrets namespace */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                    Secrets ({Object.keys(memory.secrets || {}).length})
                  </h4>
                  {memory.secrets && Object.keys(memory.secrets).length > 0 ? (
                    <div className="space-y-2">
                      {Object.entries(memory.secrets).map(([key, value]) => (
                        <div key={key} className="bg-red-50 border border-red-200 rounded p-2">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-xs font-semibold text-red-900">
                              {key}
                            </span>
                          </div>
                          <div
                            className="mt-1 bg-white border border-red-100 rounded p-2 text-xs font-mono"
                            style={{
                              maxHeight: '128px',
                              overflow: 'auto',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {typeof value === 'string' && value.length > 0
                              ? '••••••••'
                              : typeof value === 'string'
                              ? '(empty)'
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
                      No secrets
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500">Memory not available</p>
            )}
          </div>
        ) : activeTab === 'execution' ? (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Execution Log</h3>
            {(() => {
              // Use live execution log from memory if available (during active run), otherwise use persisted run log
              const executionLog = (memory?.execution_log && memory.execution_log.length > 0)
                ? memory.execution_log
                : run.execution_log;

              if (!executionLog || executionLog.length === 0) {
                return <p className="text-sm text-gray-500">No execution log available</p>;
              }

              return (
              <div className="space-y-3 min-w-0">
                {(() => {
                  // Group entries by step
                  const stepGroups = new Map<string, typeof executionLog>();
                  executionLog.forEach((entry) => {
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
                    const toolCalls = entries.filter(e => e.operation === 'tool_call');

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
                            {toolCalls.length > 0 && `, ${toolCalls.length} tool call(s)`}
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

                          {/* Tool Calls */}
                          {toolCalls.length > 0 && (
                            <div className="min-w-0">
                              <h5 className="text-xs font-semibold text-purple-700 uppercase mb-2">
                                Tool Calls
                              </h5>
                              <div className="space-y-2 min-w-0">
                                {toolCalls.map((entry, toolIdx) => (
                                  <div
                                    key={toolIdx}
                                    className="bg-purple-50 border border-purple-200 rounded p-2 min-w-0"
                                  >
                                    <div className="flex items-center gap-2 mb-1">
                                      <span className="font-mono text-xs font-semibold text-purple-900">
                                        {entry.value?.tool_name || entry.key}
                                      </span>
                                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                                        entry.value?.event === 'call'
                                          ? 'bg-purple-200 text-purple-800'
                                          : 'bg-green-200 text-green-800'
                                      }`}>
                                        {entry.value?.event === 'call' ? 'CALL' : 'RESULT'}
                                      </span>
                                    </div>
                                    {entry.value?.event === 'call' && entry.value?.arguments && (
                                      <details className="text-xs mt-1">
                                        <summary className="cursor-pointer text-purple-600 hover:text-purple-800">
                                          Arguments
                                        </summary>
                                        <div className="mt-1 bg-white border border-purple-100 rounded p-2 font-mono"
                                             style={{
                                               maxHeight: '128px',
                                               overflow: 'auto',
                                               whiteSpace: 'nowrap'
                                             }}>
                                          {JSON.stringify(entry.value.arguments, null, 2).split('\n').map((line, idx) => (
                                            <div key={idx} style={{ whiteSpace: 'nowrap' }}>{line}</div>
                                          ))}
                                        </div>
                                      </details>
                                    )}
                                    {entry.value?.event === 'result' && entry.value?.result !== undefined && (
                                      <details className="text-xs mt-1">
                                        <summary className="cursor-pointer text-purple-600 hover:text-purple-800">
                                          Result
                                        </summary>
                                        <div className="mt-1 bg-white border border-purple-100 rounded p-2 font-mono"
                                             style={{
                                               maxHeight: '128px',
                                               overflow: 'auto',
                                               whiteSpace: 'nowrap'
                                             }}>
                                          {typeof entry.value.result === 'string'
                                            ? entry.value.result
                                            : JSON.stringify(entry.value.result, null, 2).split('\n').map((line, idx) => (
                                              <div key={idx} style={{ whiteSpace: 'nowrap' }}>{line}</div>
                                            ))
                                          }
                                        </div>
                                      </details>
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
              );
            })()}
          </div>
        ) : activeTab === 'session' ? (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Session History</h3>
            {sessionLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : sessionHistory?.history && Object.keys(sessionHistory.history).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(sessionHistory.history).map(([stepId, messages]) => (
                  <div key={stepId} className="border border-gray-200 rounded-lg overflow-hidden">
                    {/* Step Header */}
                    <div className="bg-purple-50 px-4 py-2 border-b border-purple-200">
                      <h4 className="font-semibold text-purple-900">{stepId}</h4>
                      <p className="text-xs text-purple-600 mt-0.5">
                        {(messages as any[]).length} message(s)
                      </p>
                    </div>

                    {/* Messages */}
                    <div className="p-4 space-y-3">
                      {(messages as any[]).map((msg, idx) => {
                        // Determine message role/type
                        const role = msg.role || msg.kind || msg.type || 'unknown';
                        const content = msg.content || msg.text || (typeof msg === 'string' ? msg : JSON.stringify(msg));

                        // Style based on role
                        const isUser = ['user', 'human', 'request'].includes(role.toLowerCase());
                        const isAssistant = ['assistant', 'ai', 'response', 'model-text-response'].includes(role.toLowerCase());
                        const isSystem = ['system'].includes(role.toLowerCase());
                        const isTool = ['tool', 'tool-return'].includes(role.toLowerCase());

                        let bgColor = 'bg-gray-50';
                        let borderColor = 'border-gray-200';
                        let roleLabel = role;

                        if (isUser) {
                          bgColor = 'bg-blue-50';
                          borderColor = 'border-blue-200';
                          roleLabel = 'User';
                        } else if (isAssistant) {
                          bgColor = 'bg-green-50';
                          borderColor = 'border-green-200';
                          roleLabel = 'Assistant';
                        } else if (isSystem) {
                          bgColor = 'bg-orange-50';
                          borderColor = 'border-orange-200';
                          roleLabel = 'System';
                        } else if (isTool) {
                          bgColor = 'bg-purple-50';
                          borderColor = 'border-purple-200';
                          roleLabel = 'Tool';
                        }

                        return (
                          <div
                            key={idx}
                            className={`${bgColor} border ${borderColor} rounded-lg p-3`}
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                                isUser ? 'bg-blue-200 text-blue-800' :
                                isAssistant ? 'bg-green-200 text-green-800' :
                                isSystem ? 'bg-orange-200 text-orange-800' :
                                isTool ? 'bg-purple-200 text-purple-800' :
                                'bg-gray-200 text-gray-800'
                              }`}>
                                {roleLabel}
                              </span>
                              {msg.timestamp && (
                                <span className="text-xs text-gray-500">
                                  {new Date(msg.timestamp).toLocaleTimeString()}
                                </span>
                              )}
                            </div>
                            <div
                              className="text-sm text-gray-800 whitespace-pre-wrap break-words"
                              style={{ maxHeight: '200px', overflow: 'auto' }}
                            >
                              {typeof content === 'string' ? content : (
                                <pre className="text-xs font-mono">
                                  {JSON.stringify(content, null, 2)}
                                </pre>
                              )}
                            </div>
                            {/* Show tool calls if present */}
                            {msg.parts && Array.isArray(msg.parts) && msg.parts.some((p: any) => p.tool_name) && (
                              <div className="mt-2 pt-2 border-t border-gray-200">
                                <details>
                                  <summary className="text-xs text-purple-600 cursor-pointer hover:text-purple-800">
                                    Tool Calls ({msg.parts.filter((p: any) => p.tool_name).length})
                                  </summary>
                                  <div className="mt-1 space-y-1">
                                    {msg.parts.filter((p: any) => p.tool_name).map((part: any, pIdx: number) => (
                                      <div key={pIdx} className="text-xs bg-white border border-purple-100 rounded p-2">
                                        <span className="font-semibold text-purple-700">{part.tool_name}</span>
                                        {part.args && (
                                          <pre className="mt-1 text-gray-600 overflow-auto" style={{ maxHeight: '100px' }}>
                                            {JSON.stringify(part.args, null, 2)}
                                          </pre>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </details>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="text-sm text-gray-500">
                  No session history available yet. History is populated after LLM steps with history enabled have been executed.
                </p>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
