import { useGraphStore } from '@/stores/graphStore';
import { X, Link, ChevronDown, ChevronRight } from 'lucide-react';

interface PropertiesPanelProps {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export default function PropertiesPanel({ isCollapsed, setIsCollapsed }: PropertiesPanelProps) {
  const { nodes, selectedNodeId, setSelectedNode, updateNode, deleteNode, memory } = useGraphStore();

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  if (!selectedNode) {
    return (
      <div className="h-full bg-gray-50 border-l border-gray-200 p-4">
        <p className="text-sm text-gray-500 text-center mt-8">
          Select a node to view its properties
        </p>
      </div>
    );
  }

  const { step, stepTypeInfo } = selectedNode.data;

  // Helper to check if a value is a memory binding
  const isMemoryBinding = (value: any): boolean => {
    return typeof value === 'string' && value.startsWith('{memory.') && value.endsWith('}');
  };

  // Get all available memory fields
  const getAllMemoryFields = (): string[] => {
    const fields: string[] = [];
    Object.keys(memory.inputs).forEach(k => fields.push(`{memory.${k}}`));
    Object.keys(memory.intermediate).forEach(k => fields.push(`{memory.${k}}`));
    Object.keys(memory.outputs).forEach(k => fields.push(`{memory.${k}}`));
    return fields;
  };

  const handleConfigChange = (key: string, value: any) => {
    updateNode(selectedNodeId!, {
      config: {
        ...step.config,
        [key]: value,
      },
    });
  };

  const handleOutputChange = (outputKey: string, memoryLocation: string) => {
    // Ensure it's in the {memory.field} format
    const formattedLocation = memoryLocation.startsWith('{memory.')
      ? memoryLocation
      : `{memory.${memoryLocation}}`;

    updateNode(selectedNodeId!, {
      outputs: {
        ...(step.outputs || {}),
        [outputKey]: formattedLocation,
      },
    });
  };

  const handleDelete = () => {
    if (confirm(`Delete step "${step.id}"?`)) {
      deleteNode(selectedNodeId!);
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 border-l border-gray-200">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 p-3 flex items-center justify-between">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center gap-2 hover:bg-gray-50 transition-colors flex-1 text-left -m-3 p-3"
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4 text-gray-500 flex-shrink-0" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-500 flex-shrink-0" />
          )}
          <h2 className="text-sm font-bold text-gray-900">Properties</h2>
        </button>
        <button
          onClick={() => setSelectedNode(null)}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Step info */}
        <div>
          <div
            className="inline-block px-3 py-1 rounded-full text-sm font-medium text-white"
            style={{ backgroundColor: stepTypeInfo.color }}
          >
            {stepTypeInfo.label}
          </div>
          <p className="text-xs text-gray-600 mt-2">{stepTypeInfo.description}</p>
        </div>

        {/* Step ID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Step ID
          </label>
          <input
            type="text"
            value={step.id}
            onChange={(e) => updateNode(selectedNodeId!, { id: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>

        {/* Step Inputs/Outputs Schema Info */}
        {(stepTypeInfo.inputsSchema?.description || stepTypeInfo.outputsSchema?.description) && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-blue-900 mb-2">Step Behavior</h4>
            {stepTypeInfo.inputsSchema?.description && (
              <div className="mb-2">
                <p className="text-xs text-blue-800">
                  <strong>Inputs:</strong> {stepTypeInfo.inputsSchema.description}
                </p>
              </div>
            )}
            {stepTypeInfo.outputsSchema?.description && (
              <div>
                <p className="text-xs text-blue-800">
                  <strong>Outputs:</strong> {stepTypeInfo.outputsSchema.description}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Config */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Configuration
          </label>
          <div className="space-y-3">
            {stepTypeInfo.configSchema && Object.keys(stepTypeInfo.configSchema.properties || {}).length > 0 ? (
              Object.entries(stepTypeInfo.configSchema.properties || {}).map(([key, schema]: [string, any]) => {
                const currentValue = step.config[key] ?? schema.default ?? '';
                const isBound = isMemoryBinding(currentValue);

                // Generate a better label from the key or use title from schema
                const label = schema.title || key.split('_').map((word: string) =>
                  word.charAt(0).toUpperCase() + word.slice(1)
                ).join(' ');

                return (
                  <div key={key}>
                    <div className="flex items-center justify-between mb-1">
                      <label className="block text-xs font-medium text-gray-600">
                        {label}
                      </label>
                      {isBound && (
                        <span className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                          <Link className="w-3 h-3" />
                          Bound to {currentValue}
                        </span>
                      )}
                    </div>
                    {schema.type === 'boolean' ? (
                      <input
                        type="checkbox"
                        checked={step.config[key] ?? schema.default ?? false}
                        onChange={(e) => handleConfigChange(key, e.target.checked)}
                        className="rounded border-gray-300"
                      />
                    ) : schema.enum ? (
                      <div>
                        <input
                          type="text"
                          value={currentValue}
                          onChange={(e) => handleConfigChange(key, e.target.value)}
                          placeholder={`e.g., ${schema.enum[0]} or {memory.field_name}`}
                          className={`w-full px-3 py-2 border rounded-md text-sm ${
                            isBound ? 'border-blue-300 bg-blue-50' : 'border-gray-300'
                          }`}
                          list={`${key}-options`}
                        />
                        <datalist id={`${key}-options`}>
                          {schema.enum.map((opt: string) => (
                            <option key={opt} value={opt} />
                          ))}
                          {getAllMemoryFields().map((field) => (
                            <option key={field} value={field} />
                          ))}
                        </datalist>
                      </div>
                    ) : schema.type === 'number' ? (
                      <input
                        type="text"
                        value={currentValue}
                        onChange={(e) => {
                          const val = e.target.value;
                          // If it's a memory binding, keep as string; otherwise parse as number
                          handleConfigChange(key, val.startsWith('{memory.') ? val : (val === '' ? '' : parseFloat(val)));
                        }}
                        placeholder="e.g., 0.7 or {memory.field_name}"
                        className={`w-full px-3 py-2 border rounded-md text-sm ${
                          isBound ? 'border-blue-300 bg-blue-50' : 'border-gray-300'
                        }`}
                        list={`${key}-memory-options`}
                      />
                    ) : schema.type === 'object' || schema.type === 'array' ? (
                      <textarea
                        value={
                          typeof step.config[key] === 'string' ? step.config[key] :
                          step.config[key]
                            ? JSON.stringify(step.config[key], null, 2)
                            : ''
                        }
                        onChange={(e) => {
                          const val = e.target.value;
                          if (val.startsWith('{memory.')) {
                            handleConfigChange(key, val);
                          } else {
                            try {
                              const parsed = JSON.parse(val);
                              handleConfigChange(key, parsed);
                            } catch {
                              // Invalid JSON, keep as string (might be incomplete)
                              handleConfigChange(key, val);
                            }
                          }
                        }}
                        placeholder={`${schema.type === 'object' ? '{}' : '[]'} or {memory.field_name}`}
                        rows={3}
                        className={`w-full px-3 py-2 border rounded-md text-sm font-mono ${
                          isBound ? 'border-blue-300 bg-blue-50' : 'border-gray-300'
                        }`}
                      />
                    ) : (
                      <textarea
                        value={currentValue}
                        onChange={(e) => handleConfigChange(key, e.target.value)}
                        placeholder="Enter value or {memory.field_name}"
                        rows={3}
                        className={`w-full px-3 py-2 border rounded-md text-sm ${
                          isBound ? 'border-blue-300 bg-blue-50' : 'border-gray-300'
                        }`}
                      />
                    )}
                    {schema.description && (
                      <p className="text-xs text-gray-500 mt-1">{schema.description}</p>
                    )}
                  </div>
                );
              })
            ) : (
              <p className="text-xs text-gray-500">No configuration required</p>
            )}
          </div>
        </div>

        {/* Outputs */}
        {stepTypeInfo.outputsSchema?.properties && Object.keys(stepTypeInfo.outputsSchema.properties).length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Outputs
            </label>
            <div className="space-y-3">
              {Object.entries(stepTypeInfo.outputsSchema.properties).map(([outputKey, outputSchema]: [string, any]) => {
                // Get the memory location from step.outputs, defaulting to outputKey
                const outputTemplate = step.outputs?.[outputKey] || `{memory.${outputKey}}`;

                // Extract just the memory key from {memory.field} format
                let memoryKey = outputKey;
                const match = outputTemplate.match(/\{memory\.([^}]+)\}/);
                if (match) {
                  memoryKey = match[1];
                }

                // Determine type label
                const typeLabel = outputSchema.type || 'any';

                return (
                  <div key={outputKey} className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="flex items-start justify-between mb-1">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-green-900">
                            {outputKey}
                          </span>
                          <span className="text-xs text-green-600 bg-green-100 px-2 py-0.5 rounded">
                            {typeLabel}
                          </span>
                        </div>
                        {outputSchema.description && (
                          <p className="text-xs text-green-700 mt-1">
                            {outputSchema.description}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="mt-2 pt-2 border-t border-green-200">
                      <div className="flex items-center gap-2">
                        <Link className="w-3 h-3 text-green-600 flex-shrink-0" />
                        <input
                          type="text"
                          value={memoryKey}
                          onChange={(e) => handleOutputChange(outputKey, e.target.value)}
                          placeholder={outputKey}
                          className="flex-1 px-2 py-1 text-xs border border-green-300 rounded bg-white focus:outline-none focus:ring-2 focus:ring-green-500 font-mono"
                        />
                      </div>
                      <p className="text-xs text-green-700 mt-1 ml-5">
                        Memory location where this output will be written
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Delete button */}
        <div className="pt-4 border-t border-gray-200">
          <button
            onClick={handleDelete}
            className="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
          >
            Delete Step
          </button>
        </div>
      </div>
      )}
    </div>
  );
}
