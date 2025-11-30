import { useState, useEffect, useCallback } from 'react';
import { RefreshCw, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { EditorProps } from './types';
import { useGraphStore } from '@/stores/graphStore';

interface MCPTool {
  name: string;
  description: string;
  inputSchema?: Record<string, any>;
}

interface DiscoverResponse {
  success: boolean;
  tools?: MCPTool[];
  error?: string;
}

export default function MCPToolSelector({ value, onChange, stepId }: EditorProps) {
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastConfig, setLastConfig] = useState<string>('');

  // Get the node from the store to access the step config
  const nodes = useGraphStore((state) => state.nodes);
  const node = nodes.find((n) => n.data?.step?.id === stepId);
  const stepConfig = node?.data?.step?.config || {};

  // Extract MCP server configuration from step config
  const transport = stepConfig.transport || 'stdio';
  const command = stepConfig.command || '';
  const args = stepConfig.args || [];
  const url = stepConfig.url || '';

  // Build config key for change detection
  const configKey = JSON.stringify({ transport, command, args, url });

  // Check if we have enough config to discover tools
  const canDiscover = transport === 'stdio'
    ? Boolean(command)
    : Boolean(url);

  // Discover tools from MCP server
  const discoverTools = useCallback(async () => {
    if (!canDiscover) {
      setError('Configure the MCP server connection first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/mcp/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transport,
          command: transport === 'stdio' ? command : undefined,
          args: transport === 'stdio' ? args : undefined,
          url: transport !== 'stdio' ? url : undefined,
          timeout: 10.0,
        }),
      });

      const data: DiscoverResponse = await response.json();

      if (data.success && data.tools) {
        setTools(data.tools);
        setLastConfig(configKey);
        if (data.tools.length === 0) {
          setError('No tools found on this MCP server');
        }
      } else {
        setError(data.error || 'Failed to discover tools');
        setTools([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
      setTools([]);
    } finally {
      setLoading(false);
    }
  }, [transport, command, args, url, canDiscover, configKey]);

  // Auto-discover when config changes (with debounce)
  useEffect(() => {
    if (configKey !== lastConfig && canDiscover) {
      const timer = setTimeout(() => {
        discoverTools();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [configKey, lastConfig, canDiscover, discoverTools]);

  // Handle tool selection
  const handleSelect = (toolName: string) => {
    onChange(toolName);
  };

  // Find selected tool info
  const selectedTool = tools.find((t) => t.name === value);

  return (
    <div className="space-y-2">
      {/* Connection status and refresh */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs">
          {loading ? (
            <>
              <Loader2 className="w-3 h-3 animate-spin text-blue-500" />
              <span className="text-blue-600">Discovering tools...</span>
            </>
          ) : error ? (
            <>
              <AlertCircle className="w-3 h-3 text-amber-500" />
              <span className="text-amber-600">{error}</span>
            </>
          ) : tools.length > 0 ? (
            <>
              <CheckCircle className="w-3 h-3 text-green-500" />
              <span className="text-green-600">{tools.length} tool(s) available</span>
            </>
          ) : !canDiscover ? (
            <span className="text-gray-500">Configure server connection above</span>
          ) : null}
        </div>

        <button
          onClick={discoverTools}
          disabled={loading || !canDiscover}
          className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Refresh tool list"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Tool selector dropdown */}
      <select
        value={value || ''}
        onChange={(e) => handleSelect(e.target.value)}
        disabled={loading || tools.length === 0}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        <option value="">
          {loading ? 'Loading...' : tools.length === 0 ? 'No tools available' : 'Select a tool...'}
        </option>
        {tools.map((tool) => (
          <option key={tool.name} value={tool.name}>
            {tool.name}
          </option>
        ))}
      </select>

      {/* Selected tool description */}
      {selectedTool && selectedTool.description && (
        <div className="p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
          {selectedTool.description}
        </div>
      )}

      {/* Manual input fallback */}
      {tools.length === 0 && !loading && (
        <div className="mt-2">
          <label className="block text-xs text-gray-500 mb-1">
            Or enter tool name manually:
          </label>
          <input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Enter MCP tool name..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
        </div>
      )}
    </div>
  );
}
