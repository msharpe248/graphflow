import { useState, useEffect, useCallback } from 'react';
import { RefreshCw, AlertCircle, CheckCircle, Loader2, Link, ChevronDown, ChevronRight } from 'lucide-react';
import { EditorProps } from './types';
import { useGraphStore } from '@/stores/graphStore';

interface MCPToolParam {
  name: string;
  type: string;
  description?: string;
  required?: boolean;
  default?: any;
}

interface MCPTool {
  name: string;
  description: string;
  inputSchema?: {
    type?: string;
    properties?: Record<string, {
      type?: string;
      description?: string;
      default?: any;
    }>;
    required?: string[];
  };
}

interface DiscoverResponse {
  success: boolean;
  tools?: MCPTool[];
  error?: string;
}

interface ToolConfig {
  tool_name: string;
  tool_args: Record<string, any>;
}

export default function MCPToolEditor({ value, onChange, stepId }: EditorProps) {
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastConfig, setLastConfig] = useState<string>('');
  const [argsExpanded, setArgsExpanded] = useState(true);

  // Parse the current value
  const config: ToolConfig = typeof value === 'object' && value !== null
    ? value
    : { tool_name: '', tool_args: {} };

  // Get the node from the store to access the step config
  const nodes = useGraphStore((state) => state.nodes);
  const memory = useGraphStore((state) => state.memory);
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

  // Find the selected tool
  const selectedTool = tools.find((t) => t.name === config.tool_name);

  // Extract parameters from selected tool's input schema
  const getToolParams = (tool: MCPTool | undefined): MCPToolParam[] => {
    if (!tool?.inputSchema?.properties) return [];
    const required = tool.inputSchema.required || [];
    return Object.entries(tool.inputSchema.properties).map(([name, prop]) => ({
      name,
      type: prop.type || 'string',
      description: prop.description,
      required: required.includes(name),
      default: prop.default,
    }));
  };

  const toolParams = getToolParams(selectedTool);

  // Check if a value is a memory binding
  const isMemoryBinding = (val: any): boolean => {
    return typeof val === 'string' && val.startsWith('{memory.') && val.endsWith('}');
  };

  // Get all available memory keys for binding
  const getMemoryKeys = (): string[] => {
    const keys: string[] = [];
    if (memory.inputs) {
      Object.keys(memory.inputs).forEach(k => keys.push(k));
    }
    if (memory.intermediate) {
      Object.keys(memory.intermediate).forEach(k => keys.push(k));
    }
    if (memory.outputs) {
      Object.keys(memory.outputs).forEach(k => keys.push(k));
    }
    return keys;
  };

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
  const handleToolSelect = (toolName: string) => {
    // When tool changes, reset args but keep any that match new tool's params
    const newTool = tools.find(t => t.name === toolName);
    const newParams = getToolParams(newTool);
    const newArgs: Record<string, any> = {};

    // Preserve existing args that match new tool's params
    newParams.forEach(param => {
      if (config.tool_args[param.name] !== undefined) {
        newArgs[param.name] = config.tool_args[param.name];
      } else if (param.default !== undefined) {
        newArgs[param.name] = param.default;
      }
    });

    onChange({
      tool_name: toolName,
      tool_args: newArgs,
    });
  };

  // Handle argument value change
  const handleArgChange = (paramName: string, newValue: any) => {
    onChange({
      ...config,
      tool_args: {
        ...config.tool_args,
        [paramName]: newValue,
      },
    });
  };

  // Toggle memory binding for a parameter
  const handleToggleBinding = (paramName: string) => {
    const currentValue = config.tool_args[paramName];
    if (isMemoryBinding(currentValue)) {
      // Convert from binding to literal
      handleArgChange(paramName, '');
    } else {
      // Convert to binding - show first available memory key
      const keys = getMemoryKeys();
      handleArgChange(paramName, keys.length > 0 ? `{memory.${keys[0]}}` : '{memory.}');
    }
  };

  return (
    <div className="space-y-4 border border-gray-200 rounded-lg p-3 bg-gray-50">
      {/* Tool Selection Section */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-gray-700">MCP Tool</label>
          <div className="flex items-center gap-2">
            {loading ? (
              <span className="flex items-center gap-1 text-xs text-blue-600">
                <Loader2 className="w-3 h-3 animate-spin" />
                Discovering...
              </span>
            ) : error ? (
              <span className="flex items-center gap-1 text-xs text-amber-600">
                <AlertCircle className="w-3 h-3" />
                {error}
              </span>
            ) : tools.length > 0 ? (
              <span className="flex items-center gap-1 text-xs text-green-600">
                <CheckCircle className="w-3 h-3" />
                {tools.length} tool(s)
              </span>
            ) : null}
            <button
              onClick={discoverTools}
              disabled={loading || !canDiscover}
              className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors disabled:opacity-50"
              title="Refresh tools"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        <select
          value={config.tool_name || ''}
          onChange={(e) => handleToolSelect(e.target.value)}
          disabled={loading || tools.length === 0}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 bg-white"
        >
          <option value="">
            {loading ? 'Loading...' : tools.length === 0 ? 'Configure server above' : 'Select a tool...'}
          </option>
          {tools.map((tool) => (
            <option key={tool.name} value={tool.name}>
              {tool.name}
            </option>
          ))}
        </select>

        {selectedTool?.description && (
          <p className="mt-1 text-xs text-gray-500">{selectedTool.description}</p>
        )}
      </div>

      {/* Tool Arguments Section */}
      {config.tool_name && toolParams.length > 0 && (
        <div>
          <button
            onClick={() => setArgsExpanded(!argsExpanded)}
            className="flex items-center gap-1 text-sm font-medium text-gray-700 hover:text-gray-900 mb-2"
          >
            {argsExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
            Arguments ({toolParams.length})
          </button>

          {argsExpanded && (
            <div className="space-y-3 ml-1 pl-3 border-l-2 border-gray-200">
              {toolParams.map((param) => {
                const argValue = config.tool_args[param.name];
                const isBound = isMemoryBinding(argValue);
                const memoryKeys = getMemoryKeys();

                return (
                  <div key={param.name} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-medium text-gray-600">
                        {param.name}
                        {param.required && <span className="text-red-500 ml-0.5">*</span>}
                        <span className="ml-1 text-gray-400">({param.type})</span>
                      </label>
                      <button
                        onClick={() => handleToggleBinding(param.name)}
                        className={`flex items-center gap-1 text-xs px-1.5 py-0.5 rounded transition-colors ${
                          isBound
                            ? 'text-blue-600 bg-blue-50 hover:bg-blue-100'
                            : 'text-gray-400 hover:text-blue-600 hover:bg-blue-50'
                        }`}
                        title={isBound ? 'Switch to literal value' : 'Bind to memory'}
                      >
                        <Link className="w-3 h-3" />
                        {isBound ? 'Bound' : 'Bind'}
                      </button>
                    </div>

                    {isBound ? (
                      <select
                        value={argValue || ''}
                        onChange={(e) => handleArgChange(param.name, e.target.value)}
                        className="w-full px-2 py-1.5 text-sm border border-blue-300 rounded bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select memory location...</option>
                        {memoryKeys.map((key) => (
                          <option key={key} value={`{memory.${key}}`}>
                            {`{memory.${key}}`}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type={param.type === 'number' || param.type === 'integer' ? 'number' : 'text'}
                        value={argValue ?? param.default ?? ''}
                        onChange={(e) => {
                          const val = param.type === 'number' || param.type === 'integer'
                            ? parseFloat(e.target.value) || 0
                            : e.target.value;
                          handleArgChange(param.name, val);
                        }}
                        placeholder={param.description || `Enter ${param.name}...`}
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    )}

                    {param.description && !isBound && (
                      <p className="text-xs text-gray-400">{param.description}</p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Manual input for tools with no schema */}
      {config.tool_name && toolParams.length === 0 && (
        <div className="text-xs text-gray-500 italic">
          This tool has no defined parameters, or the schema is not available.
        </div>
      )}

      {/* No tool selected hint */}
      {!config.tool_name && tools.length > 0 && (
        <div className="text-xs text-gray-500 text-center py-2">
          Select a tool above to configure its arguments
        </div>
      )}
    </div>
  );
}
