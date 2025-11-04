import { Square, Trash2, Eye, Loader2, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { useRuns, useStopRun, useDeleteRun } from '@/hooks/useRuntime';
import { Agent, AgentRun } from '@/types/runtime';

interface RunsListProps {
  agent: Agent;
  onSelectRun: (run: AgentRun) => void;
  selectedRunId?: string;
}

const STATUS_ICONS = {
  pending: Clock,
  running: Loader2,
  completed: CheckCircle,
  failed: AlertCircle,
  stopped: Square,
};

const STATUS_COLORS = {
  pending: 'text-yellow-600 bg-yellow-50',
  running: 'text-blue-600 bg-blue-50',
  completed: 'text-green-600 bg-green-50',
  failed: 'text-red-600 bg-red-50',
  stopped: 'text-gray-600 bg-gray-50',
};

export default function RunsList({ agent, onSelectRun, selectedRunId }: RunsListProps) {
  const { data: runs, isLoading } = useRuns(agent.id);
  const stopRun = useStopRun();
  const deleteRun = useDeleteRun();

  const handleStop = (runId: string) => {
    stopRun.mutate({ agentId: agent.id, runId });
  };

  const handleDelete = (runId: string) => {
    if (confirm('Delete this run?')) {
      deleteRun.mutate({ agentId: agent.id, runId });
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div>
          <h2 className="text-lg font-bold text-gray-900">{agent.name}</h2>
          <p className="text-xs text-gray-500 mt-1">{agent.description}</p>
        </div>
      </div>

      {/* Runs list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : runs && runs.length > 0 ? (
          runs.map((run) => {
            const StatusIcon = STATUS_ICONS[run.status];
            const statusColor = STATUS_COLORS[run.status];

            return (
              <div
                key={run.id}
                className={`
                  p-3 rounded-lg border-2 cursor-pointer transition-all
                  ${
                    selectedRunId === run.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }
                `}
                onClick={() => onSelectRun(run)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <div className={`p-1 rounded ${statusColor}`}>
                        <StatusIcon
                          className={`w-3 h-3 ${
                            run.status === 'running' ? 'animate-spin' : ''
                          }`}
                        />
                      </div>
                      <span className="font-medium text-sm text-gray-900 truncate">
                        {run.id.slice(0, 8)}
                      </span>
                      <span className={`text-xs font-medium ${statusColor} px-2 py-0.5 rounded`}>
                        {run.status}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      Started: {new Date(run.started_at).toLocaleString()}
                      {run.completed_at && (
                        <>
                          {' • '}
                          Duration: {Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s
                        </>
                      )}
                    </div>
                    {run.error && (
                      <div className="text-xs text-red-600 mt-1 line-clamp-2">
                        Error: {run.error}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-1">
                    {(run.status === 'running' || run.status === 'pending') && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStop(run.id);
                        }}
                        className="p-1.5 hover:bg-orange-50 text-orange-600 rounded transition-colors"
                        title="Stop run"
                      >
                        <Square className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRun(run);
                      }}
                      className="p-1.5 hover:bg-blue-50 text-blue-600 rounded transition-colors"
                      title="View details"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(run.id);
                      }}
                      className="p-1.5 hover:bg-red-50 text-red-600 rounded transition-colors"
                      title="Delete run"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-8">
            <p className="text-sm text-gray-500">No runs yet</p>
            <p className="text-xs text-gray-400 mt-1">
              Start a new run to see it here
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
