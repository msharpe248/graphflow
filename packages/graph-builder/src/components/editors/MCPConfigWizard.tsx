import { useState, useCallback } from 'react';
import { RefreshCw, AlertCircle, CheckCircle, Loader2, Link, ChevronDown, ChevronRight, Plus, Trash2, Plug } from 'lucide-react';
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
  // MCP protocol uses snake_case
  input_schema?: {
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

interface MCPConfig {
  server: {
    transport: 'stdio' | 'sse' | 'streamable_http';
    command?: string;
    args?: string[];
    env?: Record<string, string>;
    url?: string;
    headers?: Record<string, string>;
    timeout?: number;
  };
  tool_name: string;
  tool_args: Record<string, any>;
  // Cached tools from discovery (persisted in config)
  _discovered_tools?: MCPTool[];
}

const DEFAULT_CONFIG: MCPConfig = {
  server: {
    transport: 'stdio',
    timeout: 30,
  },
  tool_name: '',
  tool_args: {},
  _discovered_tools: [],
};

export default function MCPConfigWizard({ value, onChange }: EditorProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [serverExpanded, setServerExpanded] = useState(true);
  const [toolExpanded, setToolExpanded] = useState(true);
  const [argsExpanded, setArgsExpanded] = useState(true);
  const [headersExpanded, setHeadersExpanded] = useState(false);
  const [jsonArgsText, setJsonArgsText] = useState<string | null>(null);
  const [jsonArgsError, setJsonArgsError] = useState<string | null>(null);

  // Parse the current value
  const config: MCPConfig = typeof value === 'object' && value !== null
    ? { ...DEFAULT_CONFIG, ...value, server: { ...DEFAULT_CONFIG.server, ...value?.server } }
    : DEFAULT_CONFIG;

  // Use tools from persisted config (survives re-renders)
  const tools = config._discovered_tools || [];
  const connectionTested = tools.length > 0;

  // Get memory from store for bindings
  const memory = useGraphStore((state) => state.memory);

  // Find the selected tool
  const selectedTool = tools.find((t) => t.name === config.tool_name);

  // Extract parameters from selected tool's input schema
  const getToolParams = (tool: MCPTool | undefined): MCPToolParam[] => {
    if (!tool?.input_schema?.properties) return [];
    const required = tool.input_schema.required || [];
    return Object.entries(tool.input_schema.properties).map(([name, prop]) => ({
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

  // Check if a value is a secrets binding
  const isSecretBinding = (val: any): boolean => {
    return typeof val === 'string' && val.startsWith('{secrets.') && val.endsWith('}');
  };

  // Check if a value is any binding (including placeholder)
  const isBinding = (val: any): boolean => {
    return isMemoryBinding(val) || isSecretBinding(val) || val === '{binding}';
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

  // Get all available secret keys for binding
  const getSecretKeys = (): string[] => {
    if (memory.secrets) {
      return Object.keys(memory.secrets);
    }
    return [];
  };

  // Check if we have enough config to test connection
  const canTest = config.server.transport === 'stdio'
    ? Boolean(config.server.command)
    : Boolean(config.server.url);

  // Update config helper
  const updateConfig = (updates: Partial<MCPConfig>) => {
    onChange({ ...config, ...updates });
  };

  // Update server config - clears tools only for connection-affecting changes
  const updateServer = (updates: Partial<MCPConfig['server']>, clearTools = true) => {
    if (clearTools) {
      onChange({
        ...config,
        server: { ...config.server, ...updates },
        _discovered_tools: [],
        tool_name: '',
        tool_args: {},
      });
    } else {
      onChange({
        ...config,
        server: { ...config.server, ...updates },
      });
    }
  };

  // Update headers without clearing tools (headers don't affect tool discovery)
  const updateHeaders = (headers: Record<string, string>) => {
    onChange({
      ...config,
      server: { ...config.server, headers },
    });
  };

  // Test connection / discover tools
  const testConnection = useCallback(async () => {
    if (!canTest) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/mcp/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transport: config.server.transport,
          command: config.server.transport === 'stdio' ? config.server.command : undefined,
          args: config.server.transport === 'stdio' ? config.server.args : undefined,
          env: config.server.transport === 'stdio' ? config.server.env : undefined,
          url: config.server.transport !== 'stdio' ? config.server.url : undefined,
          headers: config.server.transport !== 'stdio' ? config.server.headers : undefined,
          timeout: config.server.timeout || 10,
        }),
      });

      const data: DiscoverResponse = await response.json();

      if (data.success && data.tools) {
        // Persist discovered tools in config
        onChange({
          ...config,
          _discovered_tools: data.tools,
        });
        if (data.tools.length === 0) {
          setError('Connected but no tools found');
        }
      } else {
        setError(data.error || 'Connection failed');
        onChange({
          ...config,
          _discovered_tools: [],
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
      onChange({
        ...config,
        _discovered_tools: [],
      });
    } finally {
      setLoading(false);
    }
  }, [config, canTest, onChange]);

  // Handle tool selection
  const handleToolSelect = (toolName: string) => {
    const newTool = tools.find(t => t.name === toolName);
    const newParams = getToolParams(newTool);
    const newArgs: Record<string, any> = {};

    // Initialize with defaults
    newParams.forEach(param => {
      if (param.default !== undefined) {
        newArgs[param.name] = param.default;
      }
    });

    updateConfig({
      tool_name: toolName,
      tool_args: newArgs,
    });
  };

  // Handle argument value change
  const handleArgChange = (paramName: string, newValue: any) => {
    updateConfig({
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
      handleArgChange(paramName, '');
    } else {
      const keys = getMemoryKeys();
      handleArgChange(paramName, keys.length > 0 ? `{memory.${keys[0]}}` : '{memory.}');
    }
  };

  // Header management - stored as array internally for stable keys
  const headerEntries = Object.entries(config.server.headers || {});

  const addHeader = () => {
    const headers = { ...(config.server.headers || {}) };
    // Generate unique placeholder key
    let idx = Object.keys(headers).length + 1;
    while (headers[`header-${idx}`] !== undefined) idx++;
    headers[`header-${idx}`] = '';
    updateHeaders(headers);
  };

  const updateHeaderKey = (index: number, newKey: string) => {
    // Rebuild headers object preserving order but with new key at index
    const entries = Object.entries(config.server.headers || {});
    const newHeaders: Record<string, string> = {};
    entries.forEach(([k, v], i) => {
      if (i === index) {
        newHeaders[newKey] = v;
      } else {
        // Handle key collision - if new key matches existing key at different index, skip
        if (k !== newKey) {
          newHeaders[k] = v;
        }
      }
    });
    updateHeaders(newHeaders);
  };

  const updateHeaderValue = (key: string, value: string) => {
    const headers = { ...(config.server.headers || {}) };
    headers[key] = value;
    updateHeaders(headers);
  };

  const removeHeader = (key: string) => {
    const headers = { ...(config.server.headers || {}) };
    delete headers[key];
    updateHeaders(headers);
  };

  // Toggle binding mode for header value
  const toggleHeaderBinding = (key: string) => {
    const currentValue = config.server.headers?.[key] || '';
    if (isBinding(currentValue)) {
      // Switch to literal value
      updateHeaderValue(key, '');
    } else {
      // Switch to binding mode - use placeholder that shows dropdown
      // User must select from the dropdown
      updateHeaderValue(key, '{binding}');
    }
  };

  // Args management
  const addArg = () => {
    const args = [...(config.server.args || []), ''];
    updateServer({ args });
  };

  const updateArg = (index: number, value: string) => {
    const args = [...(config.server.args || [])];
    args[index] = value;
    updateServer({ args });
  };

  const removeArg = (index: number) => {
    const args = [...(config.server.args || [])];
    args.splice(index, 1);
    updateServer({ args });
  };

  return (
    <div className="space-y-4">
      {/* Server Configuration Section */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <button
          onClick={() => setServerExpanded(!serverExpanded)}
          className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center gap-2">
            {serverExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            <Plug className="w-4 h-4 text-gray-500" />
            <span className="font-medium text-sm">Server Connection</span>
          </div>
          {connectionTested && (
            <span className="flex items-center gap-1 text-xs text-green-600">
              <CheckCircle className="w-3 h-3" />
              Connected
            </span>
          )}
        </button>

        {serverExpanded && (
          <div className="p-3 space-y-3 bg-white">
            {/* Transport */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Transport</label>
              <select
                value={config.server.transport}
                onChange={(e) => updateServer({ transport: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="stdio">stdio (Local Process)</option>
                <option value="sse">SSE (Server-Sent Events)</option>
                <option value="streamable_http">Streamable HTTP</option>
              </select>
            </div>

            {/* Stdio config */}
            {config.server.transport === 'stdio' && (
              <>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Command</label>
                  <input
                    type="text"
                    value={config.server.command || ''}
                    onChange={(e) => updateServer({ command: e.target.value })}
                    placeholder="e.g., uvx, npx, python"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs font-medium text-gray-600">Arguments</label>
                    <button
                      onClick={addArg}
                      className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" /> Add
                    </button>
                  </div>
                  <div className="space-y-1">
                    {(config.server.args || []).map((arg, index) => (
                      <div key={index} className="flex gap-2">
                        <input
                          type="text"
                          value={arg}
                          onChange={(e) => updateArg(index, e.target.value)}
                          placeholder={`Argument ${index + 1}`}
                          className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                          onClick={() => removeArg(index)}
                          className="p-1 text-gray-400 hover:text-red-500"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    {(!config.server.args || config.server.args.length === 0) && (
                      <p className="text-xs text-gray-400 italic">No arguments configured</p>
                    )}
                  </div>
                </div>
              </>
            )}

            {/* HTTP config */}
            {config.server.transport !== 'stdio' && (
              <>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">URL</label>
                  <input
                    type="text"
                    value={config.server.url || ''}
                    onChange={(e) => updateServer({ url: e.target.value })}
                    placeholder="https://example.com/mcp"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Headers */}
                <div>
                  <button
                    onClick={() => setHeadersExpanded(!headersExpanded)}
                    className="flex items-center justify-between w-full text-xs font-medium text-gray-600 mb-1"
                  >
                    <span className="flex items-center gap-1">
                      {headersExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                      Headers ({Object.keys(config.server.headers || {}).length})
                    </span>
                    <button
                      onClick={(e) => { e.stopPropagation(); addHeader(); setHeadersExpanded(true); }}
                      className="text-blue-600 hover:text-blue-700 flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" /> Add
                    </button>
                  </button>

                  {headersExpanded && (
                    <div className="space-y-2 mt-1">
                      {headerEntries.map(([key, value], index) => {
                        const isBound = isBinding(value);
                        const secretKeys = getSecretKeys();
                        const memoryKeys = getMemoryKeys();

                        return (
                          <div key={`header-${index}`} className="space-y-1">
                            <div className="flex gap-2 items-center">
                              <input
                                type="text"
                                value={key}
                                onChange={(e) => updateHeaderKey(index, e.target.value)}
                                placeholder="Header name"
                                className="w-1/3 px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                              {isBound ? (
                                <select
                                  value={value}
                                  onChange={(e) => updateHeaderValue(key, e.target.value)}
                                  className="flex-1 px-2 py-1 text-sm border border-blue-300 rounded bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                  <option value="">Select binding...</option>
                                  {secretKeys.length > 0 && (
                                    <optgroup label="Secrets">
                                      {secretKeys.map((k) => (
                                        <option key={`secret-${k}`} value={`{secrets.${k}}`}>
                                          {`{secrets.${k}}`}
                                        </option>
                                      ))}
                                    </optgroup>
                                  )}
                                  {memoryKeys.length > 0 && (
                                    <optgroup label="Memory">
                                      {memoryKeys.map((k) => (
                                        <option key={`memory-${k}`} value={`{memory.${k}}`}>
                                          {`{memory.${k}}`}
                                        </option>
                                      ))}
                                    </optgroup>
                                  )}
                                </select>
                              ) : (
                                <input
                                  type="text"
                                  value={value}
                                  onChange={(e) => updateHeaderValue(key, e.target.value)}
                                  placeholder="Value"
                                  className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                              )}
                              <button
                                onClick={() => toggleHeaderBinding(key)}
                                className={`flex items-center gap-1 text-xs px-1.5 py-1 rounded transition-colors ${
                                  isBound
                                    ? 'text-blue-600 bg-blue-50 hover:bg-blue-100'
                                    : 'text-gray-400 hover:text-blue-600 hover:bg-blue-50'
                                }`}
                                title={isBound ? 'Switch to literal value' : 'Bind to secret/memory'}
                              >
                                <Link className="w-3 h-3" />
                              </button>
                              <button
                                onClick={() => removeHeader(key)}
                                className="p-1 text-gray-400 hover:text-red-500"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        );
                      })}
                      {headerEntries.length === 0 && (
                        <p className="text-xs text-gray-400 italic">No headers configured</p>
                      )}
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Timeout */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Timeout (seconds)</label>
              <input
                type="number"
                value={config.server.timeout || 30}
                onChange={(e) => updateServer({ timeout: parseInt(e.target.value) || 30 }, false)}
                min={1}
                max={300}
                className="w-24 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Test Connection Button */}
            <button
              onClick={testConnection}
              disabled={loading || !canTest}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  Test Connection & Discover Tools
                </>
              )}
            </button>

            {/* Error display */}
            {error && (
              <div className="flex items-start gap-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tool Selection Section */}
      {tools.length > 0 && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => setToolExpanded(!toolExpanded)}
            className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center gap-2">
              {toolExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              <span className="font-medium text-sm">Tool Selection</span>
              <span className="text-xs text-gray-500">({tools.length} available)</span>
            </div>
            {config.tool_name && (
              <span className="text-xs text-blue-600 font-mono bg-blue-50 px-2 py-0.5 rounded">
                {config.tool_name}
              </span>
            )}
          </button>

          {toolExpanded && (
            <div className="p-3 space-y-3 bg-white">
              <select
                value={config.tool_name || ''}
                onChange={(e) => handleToolSelect(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a tool...</option>
                {tools.map((tool) => (
                  <option key={tool.name} value={tool.name}>
                    {tool.name}
                  </option>
                ))}
              </select>

              {selectedTool?.description && (
                <p className="text-xs text-gray-500 bg-gray-50 p-2 rounded">{selectedTool.description}</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tool Arguments Section - with schema */}
      {config.tool_name && toolParams.length > 0 && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => setArgsExpanded(!argsExpanded)}
            className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center gap-2">
              {argsExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              <span className="font-medium text-sm">Tool Arguments</span>
              <span className="text-xs text-gray-500">({toolParams.length} parameters)</span>
            </div>
          </button>

          {argsExpanded && (
            <div className="p-3 space-y-3 bg-white">
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

      {/* Tool Arguments Section - manual JSON (when no schema detected) */}
      {config.tool_name && toolParams.length === 0 && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => setArgsExpanded(!argsExpanded)}
            className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center gap-2">
              {argsExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              <span className="font-medium text-sm">Tool Arguments</span>
              <span className="text-xs text-amber-600">(manual entry)</span>
            </div>
          </button>

          {argsExpanded && (
            <div className="p-3 space-y-3 bg-white">
              <p className="text-xs text-gray-500">
                No parameter schema detected. Enter arguments as JSON:
              </p>
              <textarea
                value={jsonArgsText !== null ? jsonArgsText : JSON.stringify(config.tool_args || {}, null, 2)}
                onChange={(e) => {
                  const text = e.target.value;
                  setJsonArgsText(text);
                  try {
                    const parsed = JSON.parse(text);
                    setJsonArgsError(null);
                    updateConfig({ tool_args: parsed });
                  } catch {
                    setJsonArgsError('Invalid JSON');
                  }
                }}
                onBlur={() => {
                  // Reset local state on blur if valid
                  if (!jsonArgsError) {
                    setJsonArgsText(null);
                  }
                }}
                placeholder='{"arg1": "value1", "arg2": "{memory.someVar}"}'
                rows={5}
                className={`w-full px-2 py-1.5 text-sm font-mono border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  jsonArgsError ? 'border-red-300 bg-red-50' : 'border-gray-300'
                }`}
              />
              {jsonArgsError && (
                <p className="text-xs text-red-500">{jsonArgsError}</p>
              )}
              <p className="text-xs text-gray-400">
                Use {'{memory.variableName}'} syntax to bind values from memory.
              </p>
              {selectedTool?.input_schema && (
                <details className="text-xs">
                  <summary className="text-gray-500 cursor-pointer hover:text-gray-700">
                    View raw input schema
                  </summary>
                  <pre className="mt-2 p-2 bg-gray-100 rounded overflow-auto text-xs">
                    {JSON.stringify(selectedTool.input_schema, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          )}
        </div>
      )}

      {/* No tools hint */}
      {!connectionTested && !loading && (
        <p className="text-xs text-gray-500 text-center py-2">
          Configure server connection above and click "Test Connection" to discover available tools
        </p>
      )}
    </div>
  );
}
