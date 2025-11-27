import { useState } from 'react';
import { ChevronDown, ChevronUp, Info, AlertCircle, Link, Edit2 } from 'lucide-react';
import { ToolPropertyMapping } from '@/types/tool';
import { getEditorForSchema } from './EditorRegistry';
import { useGraphStore } from '@/stores/graphStore';
import MemoryBindingDialog from './MemoryBindingDialog';

interface PropertyMappingCardProps {
  mapping: ToolPropertyMapping;
  schema: Record<string, any>;
  onChange: (updates: Partial<ToolPropertyMapping>) => void;
  error?: string;
  toolName?: string; // Used to generate memory binding names
  stepId?: string; // Parent step ID for generating memory bindings
}

export default function PropertyMappingCard({
  mapping,
  schema,
  onChange,
  error,
  toolName,
  stepId,
}: PropertyMappingCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showBindingDialog, setShowBindingDialog] = useState(false);
  const { memory, setMemoryValue } = useGraphStore();

  // Determine if current runtime_value is a memory binding
  const isMemoryBinding = (value: string | undefined): boolean => {
    if (!value) return false;
    return (
      value.startsWith('{memory.') ||
      value.startsWith('{config.') ||
      value.startsWith('{env.') ||
      value.startsWith('{secrets.')
    );
  };

  const isBound = isMemoryBinding(mapping.runtime_value);

  // Parse constant value from runtime_value (when not a binding)
  const getConstantValue = (): any => {
    if (!mapping.runtime_value || isBound) {
      return schema.default ?? '';
    }
    // Try to parse as JSON for non-string types
    if (schema.type === 'number' || schema.type === 'integer') {
      const num = parseFloat(mapping.runtime_value);
      return isNaN(num) ? (schema.default ?? 0) : num;
    }
    if (schema.type === 'boolean') {
      return mapping.runtime_value === 'true';
    }
    if (schema.type === 'array' || schema.type === 'object') {
      try {
        return JSON.parse(mapping.runtime_value);
      } catch {
        return schema.default ?? (schema.type === 'array' ? [] : {});
      }
    }
    return mapping.runtime_value;
  };

  const handleVisibilityChange = (visibility: 'llm' | 'runtime') => {
    if (visibility === 'runtime' && toolName && stepId) {
      // Auto-create a memory binding when switching to runtime
      // Pattern: {memory.stepId.toolName.property} to match Properties Panel
      const memoryKey = `${stepId}.${toolName}.${mapping.source_property}`;
      const binding = `{memory.${memoryKey}}`;

      // Create the memory location if it doesn't exist
      if (!memory.intermediate[memoryKey]) {
        setMemoryValue('intermediate', memoryKey, {
          type: schema.type || 'string',
          description: `Runtime value for ${toolName}.${mapping.source_property}`,
          default: schema.default,
        });
      }

      onChange({ visibility, runtime_value: binding });
    } else {
      onChange({ visibility });
    }
  };

  const handleConstantValueChange = (value: any) => {
    // Convert value to string for storage
    let stringValue: string;
    if (typeof value === 'object') {
      stringValue = JSON.stringify(value);
    } else if (typeof value === 'boolean') {
      stringValue = value ? 'true' : 'false';
    } else {
      stringValue = String(value);
    }
    onChange({ runtime_value: stringValue });
  };

  const handleMemoryBindingSelect = (binding: string) => {
    onChange({ runtime_value: binding });
  };

  const handleClearBinding = () => {
    onChange({ runtime_value: '' });
  };

  // Get the appropriate editor component for constant values
  const renderValueEditor = () => {
    const editorConfig = getEditorForSchema(schema);
    const EditorComponent = editorConfig.component;

    return (
      <EditorComponent
        value={getConstantValue()}
        onChange={handleConstantValueChange}
        schema={schema}
      />
    );
  };

  return (
    <div
      className={`border rounded-lg transition-all ${
        error ? 'border-red-300 bg-red-50' : 'border-gray-200 bg-white'
      }`}
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-3 flex items-center justify-between text-left hover:bg-gray-50 rounded-t-lg transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-900">{mapping.source_property}</span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${
              mapping.visibility === 'llm'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            {mapping.visibility === 'llm' ? 'LLM' : 'Runtime'}
          </span>
          {schema.type && <span className="text-xs text-gray-400">({schema.type})</span>}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-3 pb-3 space-y-3 border-t border-gray-100">
          {/* Visibility Toggle */}
          <div className="pt-3">
            <label className="block text-xs font-medium text-gray-500 mb-2">
              Who controls this property?
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => handleVisibilityChange('llm')}
                className={`flex-1 px-3 py-2 text-sm rounded-md border transition-all ${
                  mapping.visibility === 'llm'
                    ? 'bg-blue-50 border-blue-500 text-blue-700 font-medium'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                LLM Controls
              </button>
              <button
                onClick={() => handleVisibilityChange('runtime')}
                className={`flex-1 px-3 py-2 text-sm rounded-md border transition-all ${
                  mapping.visibility === 'runtime'
                    ? 'bg-gray-100 border-gray-400 text-gray-700 font-medium'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                Runtime Provides
              </button>
            </div>
          </div>

          {/* LLM Configuration */}
          {mapping.visibility === 'llm' && (
            <div className="space-y-3 pt-2">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Parameter Name (shown to LLM)
                </label>
                <input
                  type="text"
                  value={mapping.llm_parameter_name || ''}
                  onChange={(e) => onChange({ llm_parameter_name: e.target.value })}
                  placeholder={mapping.source_property}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {mapping.llm_parameter_name !== mapping.source_property &&
                  mapping.llm_parameter_name && (
                    <p className="mt-1 text-xs text-gray-400 flex items-center gap-1">
                      <Info className="w-3 h-3" />
                      Original: {mapping.source_property}
                    </p>
                  )}
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Description (shown to LLM)
                </label>
                <textarea
                  value={mapping.llm_description || ''}
                  onChange={(e) => onChange({ llm_description: e.target.value })}
                  placeholder={schema.description || `Value for ${mapping.source_property}`}
                  rows={2}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {schema.description && mapping.llm_description !== schema.description && (
                  <p className="mt-1 text-xs text-gray-400 flex items-center gap-1">
                    <Info className="w-3 h-3" />
                    Default: {schema.description}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <label className="block text-xs font-medium text-gray-500 mb-1">Type</label>
                  <select
                    value={mapping.llm_schema?.type || 'string'}
                    onChange={(e) =>
                      onChange({
                        llm_schema: { ...mapping.llm_schema, type: e.target.value },
                      })
                    }
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="string">string</option>
                    <option value="number">number</option>
                    <option value="integer">integer</option>
                    <option value="boolean">boolean</option>
                    <option value="array">array</option>
                    <option value="object">object</option>
                  </select>
                </div>

                <div className="pt-5">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={mapping.required !== false}
                      onChange={(e) => onChange({ required: e.target.checked })}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Required</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Runtime Configuration - matches Properties Panel layout */}
          {mapping.visibility === 'runtime' && (
            <div className="space-y-3 pt-2">
              {/* Binding Row - like Properties Panel */}
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-gray-600">
                  Runtime Value
                </label>
                {isBound ? (
                  <button
                    onClick={() => setShowBindingDialog(true)}
                    className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded hover:bg-blue-100 transition-colors"
                    title="Click to change binding"
                  >
                    <Link className="w-3 h-3" />
                    Bound to {mapping.runtime_value}
                    <Edit2 className="w-3 h-3 ml-0.5" />
                  </button>
                ) : (
                  <button
                    onClick={() => setShowBindingDialog(true)}
                    className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded hover:bg-blue-100 transition-colors"
                    title="Click to bind to memory"
                  >
                    <Link className="w-3 h-3" />
                    Bind to memory...
                    <Edit2 className="w-3 h-3 ml-0.5" />
                  </button>
                )}
              </div>

              {/* Value Editor - always shown */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Value</label>
                {renderValueEditor()}
                {isBound && (
                  <p className="mt-1 text-xs text-gray-400">
                    This value will be overridden by the memory binding at runtime.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 pt-1">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}

          {/* Schema Info */}
          {schema.description && (
            <div className="pt-2 border-t border-gray-100">
              <p className="text-xs text-gray-400 flex items-start gap-1">
                <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
                <span>
                  <strong>Step default:</strong> {schema.description}
                  {schema.default !== undefined && (
                    <span className="ml-1">(default: {JSON.stringify(schema.default)})</span>
                  )}
                </span>
              </p>
            </div>
          )}
        </div>
      )}

      {/* Memory Binding Dialog */}
      <MemoryBindingDialog
        isOpen={showBindingDialog}
        onClose={() => setShowBindingDialog(false)}
        onSelect={handleMemoryBindingSelect}
        currentValue={mapping.runtime_value}
        title="Select Memory Location"
        description="Choose a memory location to bind this runtime value to, or create a new one"
      />
    </div>
  );
}
