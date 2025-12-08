import { X, Upload, Server, AlertCircle, CheckCircle } from 'lucide-react';
import { useState, useRef } from 'react';
import { useAgents, useCreateAgent } from '@/hooks/useRuntime';
import { useChatStore } from '@/stores/chatStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { isGraphChatEligible } from '@/types/chat';
import { GraphDefinition } from '@/types/graph';
import clsx from 'clsx';

interface AddGraphModalProps {
  onClose: () => void;
}

type Tab = 'runtime' | 'file';

export default function AddGraphModal({ onClose }: AddGraphModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>('runtime');
  const [error, setError] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { runtime } = useSettingsStore();
  const { data: agents, isLoading: loadingAgents } = useAgents();
  const createAgent = useCreateAgent();
  const { addGraph, activeGraphs, selectGraph } = useChatStore();

  // Filter to eligible agents that aren't already added
  const eligibleAgents = agents?.filter((agent) => {
    const graphDef = agent.graph_definition as GraphDefinition;
    const isEligible = isGraphChatEligible(graphDef);
    const isAlreadyAdded = activeGraphs.some((g) => g.agentId === agent.id);
    return isEligible && !isAlreadyAdded;
  }) || [];

  const ineligibleAgents = agents?.filter((agent) => {
    const graphDef = agent.graph_definition as GraphDefinition;
    return !isGraphChatEligible(graphDef);
  }) || [];

  const handleSelectAgent = (agent: typeof eligibleAgents[0]) => {
    addGraph({
      agentId: agent.id,
      name: agent.name,
      description: agent.description,
      graphDefinition: agent.graph_definition,
    });
    selectGraph(agent.id);
    onClose();
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setUploadStatus('loading');

    try {
      const text = await file.text();
      const graphDefinition = JSON.parse(text) as GraphDefinition;

      // Check eligibility
      if (!isGraphChatEligible(graphDefinition)) {
        setError("This graph is not eligible for chat. It must have a 'query' input and 'query_response' output.");
        setUploadStatus('error');
        return;
      }

      // Upload to runtime
      const agent = await createAgent.mutateAsync({
        name: graphDefinition.metadata?.name || file.name.replace('.json', ''),
        description: graphDefinition.metadata?.description,
        framework: 'pydantic_ai',
        graph_definition: graphDefinition,
      });

      // Add to chat store
      addGraph({
        agentId: agent.id,
        name: agent.name,
        description: agent.description,
        graphDefinition,
      });

      setUploadStatus('success');
      selectGraph(agent.id);
      setTimeout(onClose, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load graph');
      setUploadStatus('error');
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background border border-border rounded-lg shadow-lg w-full max-w-lg max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-lg font-semibold">Add Graph</h2>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-muted transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('runtime')}
            className={clsx(
              "flex-1 px-4 py-2 text-sm font-medium transition-colors",
              activeTab === 'runtime'
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Server className="w-4 h-4 inline-block mr-2" />
            From Runtime
          </button>
          <button
            onClick={() => setActiveTab('file')}
            className={clsx(
              "flex-1 px-4 py-2 text-sm font-medium transition-colors",
              activeTab === 'file'
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Upload className="w-4 h-4 inline-block mr-2" />
            Upload File
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'runtime' ? (
            <div className="space-y-4">
              {!runtime.connected && (
                <div className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-yellow-800 text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>Not connected to runtime. Please check settings.</span>
                </div>
              )}

              {loadingAgents ? (
                <div className="text-center py-8 text-muted-foreground">
                  Loading agents...
                </div>
              ) : eligibleAgents.length === 0 && ineligibleAgents.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No agents found in runtime.
                  <br />
                  <span className="text-sm">Upload a graph file or create one in the Builder.</span>
                </div>
              ) : (
                <>
                  {/* Eligible agents */}
                  {eligibleAgents.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium mb-2 text-green-600 flex items-center gap-1">
                        <CheckCircle className="w-4 h-4" />
                        Chat-Eligible Graphs
                      </h3>
                      <div className="space-y-2">
                        {eligibleAgents.map((agent) => (
                          <button
                            key={agent.id}
                            onClick={() => handleSelectAgent(agent)}
                            className="w-full text-left p-3 border border-border rounded-md hover:bg-muted transition-colors"
                          >
                            <div className="font-medium">{agent.name}</div>
                            {agent.description && (
                              <div className="text-sm text-muted-foreground mt-1 truncate">
                                {agent.description}
                              </div>
                            )}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Ineligible agents */}
                  {ineligibleAgents.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium mb-2 text-muted-foreground flex items-center gap-1">
                        <AlertCircle className="w-4 h-4" />
                        Not Eligible (missing query/query_response)
                      </h3>
                      <div className="space-y-2 opacity-60">
                        {ineligibleAgents.map((agent) => (
                          <div
                            key={agent.id}
                            className="p-3 border border-border rounded-md cursor-not-allowed"
                          >
                            <div className="font-medium">{agent.name}</div>
                            {agent.description && (
                              <div className="text-sm text-muted-foreground mt-1 truncate">
                                {agent.description}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Upload a GraphFlow JSON file. The graph must have a <code className="bg-muted px-1 rounded">query</code> input
                and <code className="bg-muted px-1 rounded">query_response</code> output to be eligible for chat.
              </p>

              <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <Upload className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadStatus === 'loading'}
                  className="text-primary hover:underline"
                >
                  {uploadStatus === 'loading' ? 'Uploading...' : 'Choose a file'}
                </button>
                <p className="text-sm text-muted-foreground mt-1">
                  or drag and drop
                </p>
              </div>

              {/* Status messages */}
              {uploadStatus === 'success' && (
                <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-md text-green-800 text-sm">
                  <CheckCircle className="w-4 h-4 flex-shrink-0" />
                  <span>Graph uploaded successfully!</span>
                </div>
              )}

              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
