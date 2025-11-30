import { useState, useEffect, useCallback } from 'react';
import {
  X,
  ChevronRight,
  ChevronLeft,
  Check,
  AlertCircle,
  Loader2,
  Server,
  CheckCircle2,
  Plug,
  Eye,
  EyeOff,
} from 'lucide-react';
import {
  MCPTool,
  MCPServerConfig,
  MCPToolDefinition,
  ToolPropertyMapping,
  createEmptyMCPServerConfig,
  createEmptyMCPToolDefinition,
  createMCPTool,
} from '@/types/tool';
import { useGraphStore } from '@/stores/graphStore';

interface MCPBuilderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (tools: MCPTool[]) => void;
  initialServer?: MCPServerConfig;
  initialTools?: MCPTool[];
  title?: string;
  stepId?: string;
}

interface DiscoveredTool {
  name: string;
  description: string;
  input_schema: Record<string, any>;
}

type WizardStep = 'server' | 'tools';

export default function MCPBuilderModal({
  isOpen,
  onClose,
  onSave,
  initialServer,
  initialTools,
  title = 'Add MCP Server',
  stepId,
}: MCPBuilderModalProps) {
  const { memory, setMemoryValue } = useGraphStore();

  // Current wizard step
  const [currentStep, setCurrentStep] = useState<WizardStep>('server');

  // Server configuration
  const [serverConfig, setServerConfig] = useState<MCPServerConfig>(
    initialServer || createEmptyMCPServerConfig()
  );

  // Connection state
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [connectionError, setConnectionError] = useState<string | null>(null);

  // Discovered tools from server
  const [discoveredTools, setDiscoveredTools] = useState<DiscoveredTool[]>([]);

  // Selected tools with their configurations
  const [selectedTools, setSelectedTools] = useState<Map<string, MCPToolDefinition>>(new Map());

  // Validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Reset when modal opens
  useEffect(() => {
    if (isOpen) {
      setServerConfig(initialServer || createEmptyMCPServerConfig());
      setCurrentStep('server');
      setConnectionStatus('idle');
      setConnectionError(null);
      setDiscoveredTools([]);
      setSelectedTools(new Map());
      setErrors({});

      // If editing existing tools, pre-populate
      if (initialTools && initialTools.length > 0) {
        const toolMap = new Map<string, MCPToolDefinition>();
        initialTools.forEach(t => {
          toolMap.set(t.definition.mcp_tool_name, t.definition);
        });
        setSelectedTools(toolMap);
      }
    }
  }, [isOpen, initialServer, initialTools]);

  // Test connection and discover tools
  const testConnection = useCallback(async () => {
    setIsConnecting(true);
    setConnectionError(null);
    setConnectionStatus('idle');

    try {
      const response = await fetch('/api/v1/mcp/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transport: serverConfig.transport,
          command: serverConfig.command,
          args: serverConfig.args,
          env: serverConfig.env,
          url: serverConfig.url,
          headers: serverConfig.headers,
          timeout: serverConfig.timeout || 30,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setConnectionStatus('success');
        setDiscoveredTools(data.tools || []);

        // Pre-select all tools if none were previously selected
        if (selectedTools.size === 0 && data.tools?.length > 0) {
          const toolMap = new Map<string, MCPToolDefinition>();
          data.tools.forEach((tool: DiscoveredTool) => {
            const def = createToolDefinitionFromDiscovered(tool);
            toolMap.set(tool.name, def);
          });
          setSelectedTools(toolMap);
        }
      } else {
        setConnectionStatus('error');
        setConnectionError(data.error || 'Failed to connect to MCP server');
      }
    } catch (err) {
      setConnectionStatus('error');
      setConnectionError(err instanceof Error ? err.message : 'Connection failed');
    } finally {
      setIsConnecting(false);
    }
  }, [serverConfig, selectedTools.size]);

  // Create tool definition from discovered tool
  const createToolDefinitionFromDiscovered = (tool: DiscoveredTool): MCPToolDefinition => {
    const properties = tool.input_schema?.properties || {};
    const required = tool.input_schema?.required || [];

    // Create property mappings - default all to LLM-controlled
    const mappings: ToolPropertyMapping[] = Object.entries(properties).map(
      ([key, schema]: [string, any]) => ({
        source_property: key,
        visibility: 'llm' as const,
        llm_parameter_name: key,
        llm_description: schema.description || `Parameter: ${key}`,
        llm_schema: schema,
        required: required.includes(key),
      })
    );

    return {
      id: `mcp_${tool.name}_${Date.now()}`,
      name: tool.name,
      description: tool.description || '',
      mcp_tool_name: tool.name,
      property_mappings: mappings,
      output_key: 'result',
    };
  };

  // Toggle tool selection
  const toggleToolSelection = (tool: DiscoveredTool) => {
    const newSelected = new Map(selectedTools);
    if (newSelected.has(tool.name)) {
      newSelected.delete(tool.name);
    } else {
      newSelected.set(tool.name, createToolDefinitionFromDiscovered(tool));
    }
    setSelectedTools(newSelected);
  };

  // Update property visibility
  const updatePropertyVisibility = (
    toolName: string,
    propertyName: string,
    visibility: 'llm' | 'runtime'
  ) => {
    const newSelected = new Map(selectedTools);
    const toolDef = newSelected.get(toolName);
    if (!toolDef) return;

    const updatedMappings = toolDef.property_mappings.map(mapping => {
      if (mapping.source_property === propertyName) {
        const updated = { ...mapping, visibility };
        if (visibility === 'runtime' && stepId && toolDef.name) {
          // Create memory binding for runtime property
          const memoryKey = `${stepId}.${toolDef.name}.${propertyName}`;
          updated.runtime_value = `{memory.${memoryKey}}`;

          // Create memory location if it doesn't exist
          if (!memory.intermediate[memoryKey]) {
            setMemoryValue('intermediate', memoryKey, {
              type: mapping.llm_schema?.type || 'string',
              description: `Runtime value for ${toolDef.name}.${propertyName}`,
              value: null,
            });
          }
        } else {
          updated.runtime_value = undefined;
        }
        return updated;
      }
      return mapping;
    });

    newSelected.set(toolName, { ...toolDef, property_mappings: updatedMappings });
    setSelectedTools(newSelected);
  };

  // Validate current step
  const validateStep = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (currentStep === 'server') {
      if (serverConfig.transport === 'stdio') {
        if (!serverConfig.command?.trim()) {
          newErrors.command = 'Command is required for stdio transport';
        }
      } else {
        if (!serverConfig.url?.trim()) {
          newErrors.url = 'URL is required for HTTP transport';
        }
      }
    }

    if (currentStep === 'tools') {
      if (selectedTools.size === 0) {
        newErrors.tools = 'Select at least one tool';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Navigation
  const canGoNext = (): boolean => {
    if (currentStep === 'server') {
      return connectionStatus === 'success' && discoveredTools.length > 0;
    }
    return selectedTools.size > 0;
  };

  const handleNext = () => {
    if (!validateStep()) return;
    if (currentStep === 'server') {
      setCurrentStep('tools');
    }
  };

  const handleBack = () => {
    if (currentStep === 'tools') {
      setCurrentStep('server');
    }
  };

  const handleSave = () => {
    if (!validateStep()) return;

    // Create MCPTool array from selected tools
    const tools: MCPTool[] = Array.from(selectedTools.values()).map(def =>
      createMCPTool(serverConfig, def)
    );

    onSave(tools);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress indicator */}
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <div
              className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
                currentStep === 'server'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-green-100 text-green-700'
              }`}
            >
              <Server className="w-4 h-4" />
              <span>Server</span>
              {currentStep !== 'server' && <Check className="w-4 h-4" />}
            </div>
            <ChevronRight className="w-4 h-4 text-gray-400" />
            <div
              className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
                currentStep === 'tools'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              <Plug className="w-4 h-4" />
              <span>Tools</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {currentStep === 'server' && (
            <ServerConfigStep
              config={serverConfig}
              onChange={setServerConfig}
              errors={errors}
              isConnecting={isConnecting}
              connectionStatus={connectionStatus}
              connectionError={connectionError}
              onTestConnection={testConnection}
              discoveredToolCount={discoveredTools.length}
            />
          )}

          {currentStep === 'tools' && (
            <ToolSelectionStep
              discoveredTools={discoveredTools}
              selectedTools={selectedTools}
              onToggleSelection={toggleToolSelection}
              onUpdateVisibility={updatePropertyVisibility}
              errors={errors}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={currentStep === 'server' ? onClose : handleBack}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            {currentStep === 'server' ? 'Cancel' : (
              <span className="flex items-center gap-1">
                <ChevronLeft className="w-4 h-4" />
                Back
              </span>
            )}
          </button>

          {currentStep === 'tools' ? (
            <button
              onClick={handleSave}
              disabled={selectedTools.size === 0}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Check className="w-4 h-4" />
              Add {selectedTools.size} Tool{selectedTools.size !== 1 ? 's' : ''}
            </button>
          ) : (
            <button
              onClick={handleNext}
              disabled={!canGoNext()}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Server Configuration Step
// ============================================================================

interface ServerConfigStepProps {
  config: MCPServerConfig;
  onChange: (config: MCPServerConfig) => void;
  errors: Record<string, string>;
  isConnecting: boolean;
  connectionStatus: 'idle' | 'success' | 'error';
  connectionError: string | null;
  onTestConnection: () => void;
  discoveredToolCount: number;
}

function ServerConfigStep({
  config,
  onChange,
  errors,
  isConnecting,
  connectionStatus,
  connectionError,
  onTestConnection,
  discoveredToolCount,
}: ServerConfigStepProps) {
  const [showEnvVars, setShowEnvVars] = useState(false);

  const updateConfig = (updates: Partial<MCPServerConfig>) => {
    onChange({ ...config, ...updates });
  };

  const updateEnvVar = (key: string, value: string) => {
    const newEnv = { ...(config.env || {}), [key]: value };
    updateConfig({ env: newEnv });
  };

  const removeEnvVar = (key: string) => {
    const newEnv = { ...(config.env || {}) };
    delete newEnv[key];
    updateConfig({ env: Object.keys(newEnv).length > 0 ? newEnv : undefined });
  };

  const addEnvVar = () => {
    const newEnv = { ...(config.env || {}), '': '' };
    updateConfig({ env: newEnv });
  };

  return (
    <div className="space-y-6">
      {/* Transport Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Transport Type
        </label>
        <div className="flex gap-2">
          {(['stdio', 'sse', 'streamable_http'] as const).map(transport => (
            <button
              key={transport}
              onClick={() => updateConfig({ transport })}
              className={`px-4 py-2 text-sm font-medium rounded-md border ${
                config.transport === transport
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {transport === 'stdio' ? 'Local (stdio)' :
               transport === 'sse' ? 'SSE' : 'HTTP'}
            </button>
          ))}
        </div>
      </div>

      {/* Stdio Configuration */}
      {config.transport === 'stdio' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Command *
            </label>
            <input
              type="text"
              value={config.command || ''}
              onChange={e => updateConfig({ command: e.target.value })}
              placeholder="e.g., uvx, npx, python"
              className={`w-full px-3 py-2 border rounded-md text-sm ${
                errors.command ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.command && (
              <p className="mt-1 text-xs text-red-600">{errors.command}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Arguments
            </label>
            <input
              type="text"
              value={(config.args || []).join(' ')}
              onChange={e => updateConfig({
                args: e.target.value ? e.target.value.split(/\s+/) : undefined
              })}
              placeholder="e.g., mcp-server-fetch"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
            <p className="mt-1 text-xs text-gray-500">Space-separated arguments</p>
          </div>

          {/* Environment Variables */}
          <div>
            <button
              onClick={() => setShowEnvVars(!showEnvVars)}
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
            >
              {showEnvVars ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              Environment Variables
            </button>
            {showEnvVars && (
              <div className="mt-2 space-y-2">
                {Object.entries(config.env || {}).map(([key, value], index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={key}
                      onChange={e => {
                        const newEnv = { ...(config.env || {}) };
                        delete newEnv[key];
                        newEnv[e.target.value] = value;
                        updateConfig({ env: newEnv });
                      }}
                      placeholder="KEY"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                    <input
                      type="text"
                      value={value}
                      onChange={e => updateEnvVar(key, e.target.value)}
                      placeholder="value"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                    <button
                      onClick={() => removeEnvVar(key)}
                      className="px-2 text-gray-400 hover:text-red-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                <button
                  onClick={addEnvVar}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  + Add Variable
                </button>
              </div>
            )}
          </div>
        </>
      )}

      {/* HTTP Configuration */}
      {(config.transport === 'sse' || config.transport === 'streamable_http') && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Server URL *
            </label>
            <input
              type="text"
              value={config.url || ''}
              onChange={e => updateConfig({ url: e.target.value })}
              placeholder="https://example.com/mcp"
              className={`w-full px-3 py-2 border rounded-md text-sm ${
                errors.url ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.url && (
              <p className="mt-1 text-xs text-red-600">{errors.url}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Headers
            </label>
            <div className="space-y-2">
              {Object.entries(config.headers || {}).map(([key, value], index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={key}
                    onChange={e => {
                      const newHeaders = { ...(config.headers || {}) };
                      delete newHeaders[key];
                      newHeaders[e.target.value] = value;
                      updateConfig({ headers: newHeaders });
                    }}
                    placeholder="Header-Name"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                  <input
                    type="text"
                    value={value}
                    onChange={e => {
                      const newHeaders = { ...(config.headers || {}), [key]: e.target.value };
                      updateConfig({ headers: newHeaders });
                    }}
                    placeholder="value or {secrets.KEY}"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                  <button
                    onClick={() => {
                      const newHeaders = { ...(config.headers || {}) };
                      delete newHeaders[key];
                      updateConfig({ headers: Object.keys(newHeaders).length > 0 ? newHeaders : undefined });
                    }}
                    className="px-2 text-gray-400 hover:text-red-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
              <button
                onClick={() => {
                  const newHeaders = { ...(config.headers || {}), '': '' };
                  updateConfig({ headers: newHeaders });
                }}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                + Add Header
              </button>
            </div>
          </div>
        </>
      )}

      {/* Timeout */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Timeout (seconds)
        </label>
        <input
          type="number"
          value={config.timeout || 30}
          onChange={e => updateConfig({ timeout: parseInt(e.target.value) || 30 })}
          min={1}
          max={300}
          className="w-32 px-3 py-2 border border-gray-300 rounded-md text-sm"
        />
      </div>

      {/* Test Connection Button */}
      <div className="pt-4 border-t border-gray-200">
        <button
          onClick={onTestConnection}
          disabled={isConnecting}
          className="w-full px-4 py-3 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isConnecting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Connecting...
            </>
          ) : (
            <>
              <Plug className="w-4 h-4" />
              Test Connection & Discover Tools
            </>
          )}
        </button>

        {/* Connection Status */}
        {connectionStatus === 'success' && (
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-md flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
            <span className="text-sm text-green-700">
              Connected! Found {discoveredToolCount} tool{discoveredToolCount !== 1 ? 's' : ''}
            </span>
          </div>
        )}

        {connectionStatus === 'error' && connectionError && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span className="text-sm text-red-700">{connectionError}</span>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Tool Selection Step
// ============================================================================

interface ToolSelectionStepProps {
  discoveredTools: DiscoveredTool[];
  selectedTools: Map<string, MCPToolDefinition>;
  onToggleSelection: (tool: DiscoveredTool) => void;
  onUpdateVisibility: (toolName: string, propertyName: string, visibility: 'llm' | 'runtime') => void;
  errors: Record<string, string>;
}

function ToolSelectionStep({
  discoveredTools,
  selectedTools,
  onToggleSelection,
  onUpdateVisibility,
  errors,
}: ToolSelectionStepProps) {
  const [expandedTool, setExpandedTool] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">
          Select Tools to Add ({selectedTools.size} selected)
        </h3>
        {errors.tools && (
          <p className="text-xs text-red-600 mb-2">{errors.tools}</p>
        )}
      </div>

      <div className="space-y-3">
        {discoveredTools.map(tool => {
          const isSelected = selectedTools.has(tool.name);
          const isExpanded = expandedTool === tool.name;
          const toolDef = selectedTools.get(tool.name);
          const hasProperties = Object.keys(tool.input_schema?.properties || {}).length > 0;

          return (
            <div
              key={tool.name}
              className={`border rounded-lg ${
                isSelected ? 'border-blue-300 bg-blue-50/50' : 'border-gray-200'
              }`}
            >
              {/* Tool Header */}
              <div
                className="p-3 flex items-start gap-3 cursor-pointer"
                onClick={() => onToggleSelection(tool)}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => {}}
                  className="mt-1 h-4 w-4 text-blue-600 rounded border-gray-300"
                />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 text-sm">
                    {tool.name}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                    {tool.description || 'No description'}
                  </p>
                </div>
                {isSelected && hasProperties && (
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      setExpandedTool(isExpanded ? null : tool.name);
                    }}
                    className="px-2 py-1 text-xs text-blue-600 hover:bg-blue-100 rounded"
                  >
                    {isExpanded ? 'Hide Parameters' : 'Configure Parameters'}
                  </button>
                )}
              </div>

              {/* Parameter Mappings */}
              {isSelected && isExpanded && toolDef && (
                <div className="px-3 pb-3 pt-0 border-t border-gray-200 bg-gray-50">
                  <div className="mt-3 space-y-2">
                    <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                      Parameter Control
                    </div>
                    {toolDef.property_mappings.map(mapping => (
                      <div
                        key={mapping.source_property}
                        className="flex items-center justify-between py-2 px-3 bg-white rounded border border-gray-200"
                      >
                        <div className="flex-1">
                          <div className="text-sm font-medium text-gray-700">
                            {mapping.source_property}
                            {mapping.required && (
                              <span className="ml-1 text-red-500">*</span>
                            )}
                          </div>
                          <div className="text-xs text-gray-500">
                            {mapping.llm_description || mapping.llm_schema?.type || 'string'}
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <button
                            onClick={() => onUpdateVisibility(tool.name, mapping.source_property, 'llm')}
                            className={`px-3 py-1 text-xs rounded ${
                              mapping.visibility === 'llm'
                                ? 'bg-blue-100 text-blue-700 font-medium'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            LLM
                          </button>
                          <button
                            onClick={() => onUpdateVisibility(tool.name, mapping.source_property, 'runtime')}
                            className={`px-3 py-1 text-xs rounded ${
                              mapping.visibility === 'runtime'
                                ? 'bg-purple-100 text-purple-700 font-medium'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            Runtime
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {discoveredTools.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No tools discovered. Go back and test the connection.
        </div>
      )}
    </div>
  );
}
