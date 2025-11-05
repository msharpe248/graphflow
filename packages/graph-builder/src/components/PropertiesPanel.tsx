import { useState } from 'react';
import { useGraphStore } from '@/stores/graphStore';
import { X, Link, ChevronDown, ChevronRight, Edit2, Search } from 'lucide-react';
import ColorPicker from './ColorPicker';

interface PropertiesPanelProps {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export default function PropertiesPanel({ isCollapsed, setIsCollapsed }: PropertiesPanelProps) {
  const { nodes, selectedNodeId, setSelectedNode, updateNode, deleteNode, memory, setMemoryValue, shapes, selectedShapeId, updateShape, deleteShape, setSelectedShape } = useGraphStore();
  const [inputsCollapsed, setInputsCollapsed] = useState(false);
  const [outputsCollapsed, setOutputsCollapsed] = useState(false);
  const [bindingDialog, setBindingDialog] = useState<{ configKey: string; currentValue: string } | null>(null);
  const [outputBindingDialog, setOutputBindingDialog] = useState<{ outputKey: string; currentValue: string } | null>(null);

  // Dialog-specific state
  const [inputDialogSearch, setInputDialogSearch] = useState('');
  const [inputDialogSections, setInputDialogSections] = useState({ inputs: true, intermediate: true, outputs: true });
  const [outputDialogSearch, setOutputDialogSearch] = useState('');
  const [outputDialogSections, setOutputDialogSections] = useState({ intermediate: true, outputs: true });

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);
  const selectedShape = shapes.find((s) => s.id === selectedShapeId);

  // If a shape is selected, show shape properties
  if (selectedShape) {
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
            <h2 className="text-sm font-bold text-gray-900">Shape Properties</h2>
          </button>
          <button
            onClick={() => setSelectedShape(null)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {!isCollapsed && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Shape Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Shape Type
              </label>
              <input
                type="text"
                value={
                  selectedShape.type === 'rectangle' ? 'Rectangle' :
                  selectedShape.type === 'ellipse' ? 'Ellipse' :
                  selectedShape.type === 'textbox' ? 'Text Box' :
                  'Sticky Note'
                }
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100"
              />
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title (optional)
              </label>
              <input
                type="text"
                value={selectedShape.title || ''}
                onChange={(e) => updateShape(selectedShape.id, { title: e.target.value })}
                placeholder="Enter title..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            {/* Text */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Text (optional)
              </label>
              <textarea
                value={selectedShape.text || ''}
                onChange={(e) => updateShape(selectedShape.id, { text: e.target.value })}
                placeholder={
                  selectedShape.type === 'textbox' || selectedShape.type === 'stickynote'
                    ? 'Enter text... Supports markdown: **bold**, *italic*, etc.'
                    : 'Enter text...'
                }
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            {/* Text Formatting */}
            <div className="space-y-3">
              {/* Text Color */}
              <ColorPicker
                value={selectedShape.textColor || '#1f2937'}
                onChange={(color) => updateShape(selectedShape.id, { textColor: color })}
                label="Text Color"
              />

              {/* Font Weight */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Font Weight
                </label>
                <select
                  value={selectedShape.fontWeight || 'semibold'}
                  onChange={(e) => updateShape(selectedShape.id, { fontWeight: e.target.value as 'normal' | 'medium' | 'semibold' | 'bold' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="normal">Normal</option>
                  <option value="medium">Medium</option>
                  <option value="semibold">Semibold</option>
                  <option value="bold">Bold</option>
                </select>
              </div>

              {/* Font Sizes */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title Size
                  </label>
                  <input
                    type="number"
                    value={selectedShape.titleFontSize || 14}
                    onChange={(e) => updateShape(selectedShape.id, { titleFontSize: parseInt(e.target.value) || 14 })}
                    min="8"
                    max="72"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Text Size
                  </label>
                  <input
                    type="number"
                    value={selectedShape.textFontSize || 12}
                    onChange={(e) => updateShape(selectedShape.id, { textFontSize: parseInt(e.target.value) || 12 })}
                    min="8"
                    max="72"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>

              {/* Text Alignment */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Horizontal
                  </label>
                  <select
                    value={selectedShape.textAlign || 'center'}
                    onChange={(e) => updateShape(selectedShape.id, { textAlign: e.target.value as 'left' | 'center' | 'right' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="left">Left</option>
                    <option value="center">Center</option>
                    <option value="right">Right</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Vertical
                  </label>
                  <select
                    value={selectedShape.textVerticalAlign || 'center'}
                    onChange={(e) => updateShape(selectedShape.id, { textVerticalAlign: e.target.value as 'top' | 'center' | 'bottom' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="top">Top</option>
                    <option value="center">Center</option>
                    <option value="bottom">Bottom</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Fill Color */}
            <ColorPicker
              value={selectedShape.color}
              onChange={(color) => updateShape(selectedShape.id, { color })}
              label="Fill Color"
            />

            {/* Border Color */}
            <ColorPicker
              value={selectedShape.borderColor || '#64748b'}
              onChange={(color) => updateShape(selectedShape.id, { borderColor: color })}
              label="Border Color"
            />

            {/* Opacity */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Opacity: {Math.round(selectedShape.opacity * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={selectedShape.opacity * 100}
                onChange={(e) => updateShape(selectedShape.id, { opacity: parseInt(e.target.value) / 100 })}
                className="w-full"
              />
            </div>

            {/* Padding - only for textbox and stickynote */}
            {(selectedShape.type === 'textbox' || selectedShape.type === 'stickynote') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Padding (px)
                </label>
                <input
                  type="number"
                  value={selectedShape.padding ?? 16}
                  onChange={(e) => updateShape(selectedShape.id, { padding: parseInt(e.target.value) || 0 })}
                  min="0"
                  max="50"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Inner spacing around text content
                </p>
              </div>
            )}

            {/* Shadow - only for shapes that support it */}
            {(selectedShape.type === 'textbox' || selectedShape.type === 'stickynote' || selectedShape.type === 'rectangle' || selectedShape.type === 'ellipse') && (
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedShape.shadow ?? false}
                    onChange={(e) => updateShape(selectedShape.id, { shadow: e.target.checked })}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm font-medium text-gray-700">Drop Shadow</span>
                </label>
                <p className="text-xs text-gray-500 mt-1 ml-6">
                  Add a subtle shadow effect
                </p>
              </div>
            )}

            {/* Z-Index */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Z-Index (layer order)
              </label>
              <input
                type="number"
                value={selectedShape.zIndex ?? 1}
                onChange={(e) => updateShape(selectedShape.id, { zIndex: parseInt(e.target.value) || 1 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
              <p className="text-xs text-gray-500 mt-1">
                1-99 = Behind nodes (default: 1), 100+ = In front of nodes
              </p>
            </div>

            {/* Size */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Width
                </label>
                <input
                  type="number"
                  value={selectedShape.size.width}
                  onChange={(e) => updateShape(selectedShape.id, {
                    size: { ...selectedShape.size, width: parseInt(e.target.value) || 100 }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Height
                </label>
                <input
                  type="number"
                  value={selectedShape.size.height}
                  onChange={(e) => updateShape(selectedShape.id, {
                    size: { ...selectedShape.size, height: parseInt(e.target.value) || 60 }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>

            {/* Delete Button */}
            <button
              onClick={() => {
                if (confirm(`Delete this shape?`)) {
                  deleteShape(selectedShape.id);
                }
              }}
              className="w-full px-3 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
            >
              Delete Shape
            </button>
          </div>
        )}
      </div>
    );
  }

  if (!selectedNode) {
    return (
      <div className="h-full bg-gray-50 border-l border-gray-200 p-4">
        <p className="text-sm text-gray-500 text-center mt-8">
          Select a node or shape to view its properties
        </p>
      </div>
    );
  }

  const { step, stepTypeInfo } = selectedNode.data;

  // Helper to filter memory entries based on search
  const filterMemoryEntries = (entries: [string, any][], searchTerm: string): [string, any][] => {
    if (!searchTerm.trim()) return entries;
    const lowerSearch = searchTerm.toLowerCase();
    return entries.filter(([key, field]) => {
      // Safety check: ensure field is an object with required properties
      if (!field || typeof field !== 'object') return false;
      return (
        key.toLowerCase().includes(lowerSearch) ||
        field.type?.toLowerCase().includes(lowerSearch) ||
        field.description?.toLowerCase().includes(lowerSearch)
      );
    });
  };

  // Helper to check if a value is a memory binding
  const isMemoryBinding = (value: any): boolean => {
    return typeof value === 'string' && value.startsWith('{memory.') && value.endsWith('}');
  };

  // Extract memory key and namespace from binding string
  const extractMemoryLocation = (binding: string): { namespace: 'inputs' | 'outputs' | 'intermediate'; key: string } | null => {
    const match = binding.match(/^\{memory\.(.+)\}$/);
    if (!match) return null;

    const key = match[1];

    // Determine namespace
    if (memory.inputs[key]) return { namespace: 'inputs', key };
    if (memory.intermediate[key]) return { namespace: 'intermediate', key };
    if (memory.outputs[key]) return { namespace: 'outputs', key };

    return null;
  };

  // Get value from memory schema for a binding
  const getMemoryValue = (binding: string): any => {
    const location = extractMemoryLocation(binding);
    if (!location) return undefined;
    return memory[location.namespace][location.key]?.default;
  };

  // Set value in memory schema for a binding
  const updateMemoryValue = (binding: string, value: any) => {
    const location = extractMemoryLocation(binding);
    if (location) {
      setMemoryValue(location.namespace, location.key, value);
    }
  };

  // Get all memory fields as binding strings
  const getAllMemoryFields = (): string[] => {
    const fields: string[] = [];
    Object.keys(memory.inputs).forEach((key) => fields.push(`{memory.${key}}`));
    Object.keys(memory.intermediate).forEach((key) => fields.push(`{memory.${key}}`));
    Object.keys(memory.outputs).forEach((key) => fields.push(`{memory.${key}}`));
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

  const handleOutputChange = (outputKey: string, value: string) => {
    updateNode(selectedNodeId!, {
      outputs: {
        ...(step.outputs || {}),
        [outputKey]: value,
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
          <div className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-gray-100 text-gray-700 font-mono">
            {step.id}
          </div>
        </div>

        {/* Inputs */}
        <div>
          <button
            onClick={() => setInputsCollapsed(!inputsCollapsed)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2 hover:text-gray-900"
          >
            {inputsCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
            Inputs
          </button>
          {!inputsCollapsed && (
            <div className="space-y-3">
              {stepTypeInfo.configSchema && Object.keys(stepTypeInfo.configSchema.properties || {}).length > 0 ? (
                Object.entries(stepTypeInfo.configSchema.properties || {}).map(([key, schema]: [string, any]) => {
                  const currentValue = step.config[key] ?? schema.default ?? '';
                  const isBound = isMemoryBinding(currentValue);

                  // Generate a better label from the key or use title from schema
                  const label = schema.title || key.split('_').map((word: string) =>
                    word.charAt(0).toUpperCase() + word.slice(1)
                  ).join(' ');

                  const memoryValue = isBound ? getMemoryValue(currentValue) : undefined;

                  return (
                    <div key={key}>
                      <div className="flex items-center justify-between mb-1">
                        <label className="block text-xs font-medium text-gray-600">
                          {label}
                        </label>
                        {isBound && (
                          <button
                            onClick={() => setBindingDialog({ configKey: key, currentValue })}
                            className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded hover:bg-blue-100 transition-colors"
                            title="Click to change binding"
                          >
                            <Link className="w-3 h-3" />
                            Bound to {currentValue}
                            <Edit2 className="w-3 h-3 ml-0.5" />
                          </button>
                        )}
                      </div>
                      {isBound ? (
                        <div className="mb-2">
                          <label className="block text-xs font-medium text-gray-600 mb-1">Value</label>
                          {schema.type === 'object' || schema.type === 'array' ? (
                            <textarea
                              value={memoryValue !== undefined ? JSON.stringify(memoryValue, null, 2) : ''}
                              onChange={(e) => {
                                try {
                                  const parsed = JSON.parse(e.target.value);
                                  updateMemoryValue(currentValue, parsed);
                                } catch {
                                  // Invalid JSON, keep it as string for now
                                }
                              }}
                              placeholder="Enter JSON value..."
                              rows={3}
                              className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs font-mono"
                            />
                          ) : (
                            <input
                              type="text"
                              value={memoryValue !== undefined ? memoryValue : ''}
                              onChange={(e) => updateMemoryValue(currentValue, e.target.value)}
                              placeholder="Enter value..."
                              className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs"
                            />
                          )}
                        </div>
                      ) : schema.type === 'boolean' ? (
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
                      ) : schema.type === 'number' || schema.type === 'integer' ? (
                        <input
                          type="text"
                          value={currentValue}
                          onChange={(e) => {
                            const val = e.target.value;
                            // If it's a memory binding, keep as string; otherwise parse as number
                            if (val.startsWith('{memory.')) {
                              handleConfigChange(key, val);
                            } else if (val === '') {
                              handleConfigChange(key, '');
                            } else {
                              const parsed = schema.type === 'integer' ? parseInt(val, 10) : parseFloat(val);
                              handleConfigChange(key, isNaN(parsed) ? val : parsed);
                            }
                          }}
                          placeholder={`e.g., ${schema.type === 'integer' ? '30' : '0.7'} or {memory.field_name}`}
                          className={`w-full px-3 py-2 border rounded-md text-sm ${
                            isBound ? 'border-blue-300 bg-blue-50' : 'border-gray-300'
                          }`}
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
                        <input
                          type="text"
                          value={currentValue}
                          onChange={(e) => handleConfigChange(key, e.target.value)}
                          placeholder="Enter value or {memory.field_name}"
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
          )}
        </div>

        {/* Outputs */}
        {stepTypeInfo.outputsSchema?.properties && Object.keys(stepTypeInfo.outputsSchema.properties).length > 0 && (
          <div>
            <button
              onClick={() => setOutputsCollapsed(!outputsCollapsed)}
              className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2 hover:text-gray-900"
            >
              {outputsCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
              Outputs
            </button>
            {!outputsCollapsed && (
              <div className="space-y-3">
                {Object.entries(stepTypeInfo.outputsSchema.properties).map(([outputKey, outputSchema]: [string, any]) => {
                  // Get the memory location from step.outputs, defaulting to outputKey
                  const outputValue = step.outputs?.[outputKey] || `{memory.${outputKey}}`;
                  const isOutputBound = isMemoryBinding(outputValue);
                  const outputMemoryValue = isOutputBound ? getMemoryValue(outputValue) : undefined;

                  // Determine type label
                  const typeLabel = outputSchema.type || 'any';

                  return (
                    <div key={outputKey} className="bg-green-50 border border-green-200 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-green-900">
                            {outputKey}
                          </span>
                          <span className="text-xs text-green-600 bg-green-100 px-2 py-0.5 rounded">
                            {typeLabel}
                          </span>
                        </div>
                        {isOutputBound && (
                          <button
                            onClick={() => setOutputBindingDialog({ outputKey, currentValue: outputValue })}
                            className="flex items-center gap-1 text-xs text-green-600 bg-green-100 px-1.5 py-0.5 rounded hover:bg-green-200 transition-colors"
                            title="Click to change binding"
                          >
                            <Link className="w-3 h-3" />
                            Bound to {outputValue}
                            <Edit2 className="w-3 h-3 ml-0.5" />
                          </button>
                        )}
                      </div>
                      {outputSchema.description && (
                        <p className="text-xs text-green-700 mb-2">
                          {outputSchema.description}
                        </p>
                      )}
                      {isOutputBound && (
                        <div>
                          <label className="block text-xs font-medium text-green-700 mb-1">Value</label>
                          <input
                            type="text"
                            value={outputMemoryValue !== undefined ? outputMemoryValue : ''}
                            onChange={(e) => updateMemoryValue(outputValue, e.target.value)}
                            placeholder="Enter default value..."
                            className="w-full px-2 py-1.5 border border-green-300 rounded text-xs bg-white"
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
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

      {/* Input Binding Dialog */}
      {bindingDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-bold text-gray-900">Select Memory Location</h3>
              <p className="text-xs text-gray-600 mt-1">
                Choose a memory location to bind this input to, or create a new one
              </p>

              {/* Search Input */}
              <div className="mt-3 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={inputDialogSearch}
                  onChange={(e) => setInputDialogSearch(e.target.value)}
                  placeholder="Search memory locations..."
                  className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {/* Inputs Section */}
              <div className="mb-4">
                <button
                  onClick={() => setInputDialogSections(prev => ({ ...prev, inputs: !prev.inputs }))}
                  className="w-full flex items-center justify-between mb-2 p-2 hover:bg-gray-50 rounded transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {inputDialogSections.inputs ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                    <h4 className="text-sm font-semibold text-gray-700">Inputs</h4>
                    <span className="text-xs text-gray-500">
                      ({filterMemoryEntries(Object.entries(memory.inputs), inputDialogSearch).length})
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const key = prompt('Enter new input name:');
                      if (key && !memory.inputs[key]) {
                        setMemoryValue('inputs', key, '');
                      }
                    }}
                    className="text-xs text-blue-600 hover:text-blue-700 px-2 py-1"
                  >
                    + Add
                  </button>
                </button>
                {inputDialogSections.inputs && (
                  <div className="space-y-1 ml-2">
                    {filterMemoryEntries(Object.entries(memory.inputs), inputDialogSearch).map(([key, field]) => {
                      const binding = `{memory.${key}}`;
                      const isCurrentBinding = binding === bindingDialog.currentValue;
                      const stepsUsing = nodes.filter(n => n.type === 'custom' && n.data.step).filter(n => {
                        const configStr = JSON.stringify(n.data.step.config);
                        return configStr.includes(binding);
                      }).map(n => n.data.step.id);

                      return (
                        <button
                          key={key}
                          onClick={() => {
                            handleConfigChange(bindingDialog.configKey, binding);
                            setBindingDialog(null);
                            setInputDialogSearch('');
                          }}
                          className={`w-full text-left px-3 py-2 rounded border text-sm ${
                            isCurrentBinding
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono font-medium">{key}</span>
                            <span className="text-xs text-gray-500">{field.type || 'string'}</span>
                          </div>
                          {stepsUsing.length > 0 && (
                            <p className="text-xs text-gray-600 mt-1">
                              Used by: {stepsUsing.join(', ')}
                            </p>
                          )}
                        </button>
                      );
                    })}
                    {filterMemoryEntries(Object.entries(memory.inputs), inputDialogSearch).length === 0 && (
                      <p className="text-xs text-gray-500 italic text-center py-2">
                        {inputDialogSearch ? 'No matching inputs' : 'No inputs defined'}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Intermediate Section */}
              <div className="mb-4">
                <button
                  onClick={() => setInputDialogSections(prev => ({ ...prev, intermediate: !prev.intermediate }))}
                  className="w-full flex items-center justify-between mb-2 p-2 hover:bg-gray-50 rounded transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {inputDialogSections.intermediate ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                    <h4 className="text-sm font-semibold text-gray-700">Intermediate</h4>
                    <span className="text-xs text-gray-500">
                      ({filterMemoryEntries(Object.entries(memory.intermediate), inputDialogSearch).length})
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const key = prompt('Enter new intermediate variable name:');
                      if (key && !memory.intermediate[key]) {
                        setMemoryValue('intermediate', key, '');
                      }
                    }}
                    className="text-xs text-purple-600 hover:text-purple-700 px-2 py-1"
                  >
                    + Add
                  </button>
                </button>
                {inputDialogSections.intermediate && (
                  <div className="space-y-1 ml-2">
                    {filterMemoryEntries(Object.entries(memory.intermediate), inputDialogSearch).map(([key, field]) => {
                      const binding = `{memory.${key}}`;
                      const isCurrentBinding = binding === bindingDialog.currentValue;
                      const stepsUsing = nodes.filter(n => n.type === 'custom' && n.data.step).filter(n => {
                        const configStr = JSON.stringify(n.data.step.config);
                        return configStr.includes(binding);
                      }).map(n => n.data.step.id);

                      return (
                        <button
                          key={key}
                          onClick={() => {
                            handleConfigChange(bindingDialog.configKey, binding);
                            setBindingDialog(null);
                            setInputDialogSearch('');
                          }}
                          className={`w-full text-left px-3 py-2 rounded border text-sm ${
                            isCurrentBinding
                              ? 'border-purple-500 bg-purple-50'
                              : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono font-medium">{key}</span>
                            <span className="text-xs text-gray-500">{field.type || 'string'}</span>
                          </div>
                          {stepsUsing.length > 0 && (
                            <p className="text-xs text-gray-600 mt-1">
                              Used by: {stepsUsing.join(', ')}
                            </p>
                          )}
                        </button>
                      );
                    })}
                    {filterMemoryEntries(Object.entries(memory.intermediate), inputDialogSearch).length === 0 && (
                      <p className="text-xs text-gray-500 italic text-center py-2">
                        {inputDialogSearch ? 'No matching intermediate variables' : 'No intermediate variables defined'}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Outputs Section */}
              <div>
                <button
                  onClick={() => setInputDialogSections(prev => ({ ...prev, outputs: !prev.outputs }))}
                  className="w-full flex items-center justify-between mb-2 p-2 hover:bg-gray-50 rounded transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {inputDialogSections.outputs ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                    <h4 className="text-sm font-semibold text-gray-700">Outputs</h4>
                    <span className="text-xs text-gray-500">
                      ({filterMemoryEntries(Object.entries(memory.outputs), inputDialogSearch).length})
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const key = prompt('Enter new output name:');
                      if (key && !memory.outputs[key]) {
                        setMemoryValue('outputs', key, '');
                      }
                    }}
                    className="text-xs text-green-600 hover:text-green-700 px-2 py-1"
                  >
                    + Add
                  </button>
                </button>
                {inputDialogSections.outputs && (
                  <div className="space-y-1 ml-2">
                    {filterMemoryEntries(Object.entries(memory.outputs), inputDialogSearch).map(([key, field]) => {
                      const binding = `{memory.${key}}`;
                      const isCurrentBinding = binding === bindingDialog.currentValue;
                      const stepsUsing = nodes.filter(n => n.type === 'custom' && n.data.step).filter(n => {
                        const configStr = JSON.stringify(n.data.step.config);
                        return configStr.includes(binding);
                      }).map(n => n.data.step.id);

                      return (
                        <button
                          key={key}
                          onClick={() => {
                            handleConfigChange(bindingDialog.configKey, binding);
                            setBindingDialog(null);
                            setInputDialogSearch('');
                          }}
                          className={`w-full text-left px-3 py-2 rounded border text-sm ${
                            isCurrentBinding
                              ? 'border-green-500 bg-green-50'
                              : 'border-gray-200 hover:border-green-300 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono font-medium">{key}</span>
                            <span className="text-xs text-gray-500">{field.type || 'string'}</span>
                          </div>
                          {stepsUsing.length > 0 && (
                            <p className="text-xs text-gray-600 mt-1">
                              Used by: {stepsUsing.join(', ')}
                            </p>
                          )}
                        </button>
                      );
                    })}
                    {filterMemoryEntries(Object.entries(memory.outputs), inputDialogSearch).length === 0 && (
                      <p className="text-xs text-gray-500 italic text-center py-2">
                        {inputDialogSearch ? 'No matching outputs' : 'No outputs defined'}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="p-4 border-t border-gray-200 flex gap-2 justify-end">
              <button
                onClick={() => {
                  setBindingDialog(null);
                  setInputDialogSearch('');
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Output Binding Dialog */}
      {outputBindingDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-bold text-gray-900">Select Output Memory Location</h3>
              <p className="text-xs text-gray-600 mt-1">
                Choose where this output should be written, or create a new location
              </p>

              {/* Search Input */}
              <div className="mt-3 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={outputDialogSearch}
                  onChange={(e) => setOutputDialogSearch(e.target.value)}
                  placeholder="Search memory locations..."
                  className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {/* Intermediate Section */}
              <div className="mb-4">
                <button
                  onClick={() => setOutputDialogSections(prev => ({ ...prev, intermediate: !prev.intermediate }))}
                  className="w-full flex items-center justify-between mb-2 p-2 hover:bg-gray-50 rounded transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {outputDialogSections.intermediate ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                    <h4 className="text-sm font-semibold text-gray-700">Intermediate</h4>
                    <span className="text-xs text-gray-500">
                      ({filterMemoryEntries(Object.entries(memory.intermediate), outputDialogSearch).length})
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const key = prompt('Enter new intermediate variable name:');
                      if (key && !memory.intermediate[key]) {
                        setMemoryValue('intermediate', key, '');
                      }
                    }}
                    className="text-xs text-purple-600 hover:text-purple-700 px-2 py-1"
                  >
                    + Add
                  </button>
                </button>
                {outputDialogSections.intermediate && (
                  <div className="space-y-1 ml-2">
                    {filterMemoryEntries(Object.entries(memory.intermediate), outputDialogSearch).map(([key, field]) => {
                      const binding = `{memory.${key}}`;
                      const isCurrentBinding = binding === outputBindingDialog.currentValue;
                      const stepsUsing = nodes.filter(n => n.type === 'custom' && n.data.step).filter(n => {
                        const outputsStr = JSON.stringify(n.data.step.outputs);
                        return outputsStr.includes(binding);
                      }).map(n => n.data.step.id);

                      return (
                        <button
                          key={key}
                          onClick={() => {
                            handleOutputChange(outputBindingDialog.outputKey, binding);
                            setOutputBindingDialog(null);
                            setOutputDialogSearch('');
                          }}
                          className={`w-full text-left px-3 py-2 rounded border text-sm ${
                            isCurrentBinding
                              ? 'border-purple-500 bg-purple-50'
                              : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono font-medium">{key}</span>
                            <span className="text-xs text-gray-500">{field.type || 'string'}</span>
                          </div>
                          {stepsUsing.length > 0 && (
                            <p className="text-xs text-gray-600 mt-1">
                              Written by: {stepsUsing.join(', ')}
                            </p>
                          )}
                        </button>
                      );
                    })}
                    {filterMemoryEntries(Object.entries(memory.intermediate), outputDialogSearch).length === 0 && (
                      <p className="text-xs text-gray-500 italic text-center py-2">
                        {outputDialogSearch ? 'No matching intermediate variables' : 'No intermediate variables defined'}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Outputs Section */}
              <div>
                <button
                  onClick={() => setOutputDialogSections(prev => ({ ...prev, outputs: !prev.outputs }))}
                  className="w-full flex items-center justify-between mb-2 p-2 hover:bg-gray-50 rounded transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {outputDialogSections.outputs ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                    <h4 className="text-sm font-semibold text-gray-700">Outputs</h4>
                    <span className="text-xs text-gray-500">
                      ({filterMemoryEntries(Object.entries(memory.outputs), outputDialogSearch).length})
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const key = prompt('Enter new output name:');
                      if (key && !memory.outputs[key]) {
                        setMemoryValue('outputs', key, '');
                      }
                    }}
                    className="text-xs text-green-600 hover:text-green-700 px-2 py-1"
                  >
                    + Add
                  </button>
                </button>
                {outputDialogSections.outputs && (
                  <div className="space-y-1 ml-2">
                    {filterMemoryEntries(Object.entries(memory.outputs), outputDialogSearch).map(([key, field]) => {
                      const binding = `{memory.${key}}`;
                      const isCurrentBinding = binding === outputBindingDialog.currentValue;
                      const stepsUsing = nodes.filter(n => n.type === 'custom' && n.data.step).filter(n => {
                        const outputsStr = JSON.stringify(n.data.step.outputs);
                        return outputsStr.includes(binding);
                      }).map(n => n.data.step.id);

                      return (
                        <button
                          key={key}
                          onClick={() => {
                            handleOutputChange(outputBindingDialog.outputKey, binding);
                            setOutputBindingDialog(null);
                            setOutputDialogSearch('');
                          }}
                          className={`w-full text-left px-3 py-2 rounded border text-sm ${
                            isCurrentBinding
                              ? 'border-green-500 bg-green-50'
                              : 'border-gray-200 hover:border-green-300 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono font-medium">{key}</span>
                            <span className="text-xs text-gray-500">{field.type || 'string'}</span>
                          </div>
                          {stepsUsing.length > 0 && (
                            <p className="text-xs text-gray-600 mt-1">
                              Written by: {stepsUsing.join(', ')}
                            </p>
                          )}
                        </button>
                      );
                    })}
                    {filterMemoryEntries(Object.entries(memory.outputs), outputDialogSearch).length === 0 && (
                      <p className="text-xs text-gray-500 italic text-center py-2">
                        {outputDialogSearch ? 'No matching outputs' : 'No outputs defined'}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="p-4 border-t border-gray-200 flex gap-2 justify-end">
              <button
                onClick={() => {
                  setOutputBindingDialog(null);
                  setOutputDialogSearch('');
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
