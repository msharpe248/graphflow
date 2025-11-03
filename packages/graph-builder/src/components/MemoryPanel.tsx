import { useGraphStore } from '@/stores/graphStore';
import { Plus, X, Check, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';

interface MemoryPanelProps {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export default function MemoryPanel({ isCollapsed, setIsCollapsed }: MemoryPanelProps) {
  const { memory, setMemory, nodes } = useGraphStore();
  const [expandedSection, setExpandedSection] = useState<'inputs' | 'outputs' | 'intermediate'>('inputs');

  // Find which steps are using each memory field
  const getStepsUsingMemory = (memoryKey: string): string[] => {
    const stepsUsing: string[] = [];

    nodes.forEach((node) => {
      const { step } = node.data;

      // Check config values for this memory binding
      Object.values(step.config).forEach((value) => {
        if (typeof value === 'string' && value === `{memory.${memoryKey}}`) {
          if (!stepsUsing.includes(step.id)) {
            stepsUsing.push(step.id);
          }
        }
      });

      // Check memory_reads and memory_writes
      if (step.memory_reads?.includes(memoryKey)) {
        if (!stepsUsing.includes(step.id)) {
          stepsUsing.push(step.id);
        }
      }
      if (step.memory_writes?.includes(memoryKey)) {
        if (!stepsUsing.includes(step.id)) {
          stepsUsing.push(step.id);
        }
      }
    });

    return stepsUsing;
  };

  const handleAddField = (namespace: 'inputs' | 'outputs' | 'intermediate') => {
    const key = prompt('Enter memory field name:');
    if (!key) return;

    setMemory({
      [namespace]: {
        ...memory[namespace],
        [key]: {
          type: 'string',
          description: '',
          required: namespace === 'inputs' ? false : undefined,
        },
      },
    });
  };

  const handleRemoveField = (namespace: 'inputs' | 'outputs' | 'intermediate', key: string) => {
    const updated = { ...memory[namespace] };
    delete updated[key];
    setMemory({
      [namespace]: updated,
    });
  };

  const handleUpdateField = (
    namespace: 'inputs' | 'outputs' | 'intermediate',
    key: string,
    updates: any
  ) => {
    setMemory({
      [namespace]: {
        ...memory[namespace],
        [key]: {
          ...memory[namespace][key],
          ...updates,
        },
      },
    });
  };

  const renderField = (namespace: 'inputs' | 'outputs' | 'intermediate', key: string, field: any) => {
    const stepsUsing = getStepsUsingMemory(key);

    return (
      <div key={key} className="bg-white rounded border border-gray-200 p-2 mb-2">
        <div className="flex items-start justify-between mb-1">
          <div className="flex items-center gap-2 flex-1 flex-wrap">
            <code className="text-xs font-mono font-semibold text-gray-900">{key}</code>
            {namespace === 'inputs' && field.required && (
              <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-medium">
                Required
              </span>
            )}
            {stepsUsing.length > 0 && (
              <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-medium">
                Used by: {stepsUsing.join(', ')}
              </span>
            )}
          </div>
          <button
            onClick={() => handleRemoveField(namespace, key)}
            className="text-gray-400 hover:text-red-600 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-600 mb-1">
          <select
            value={field.type}
            onChange={(e) => handleUpdateField(namespace, key, { type: e.target.value })}
            className="px-1.5 py-0.5 border border-gray-300 rounded text-xs"
          >
            <option value="string">string</option>
            <option value="number">number</option>
            <option value="boolean">boolean</option>
            <option value="object">object</option>
            <option value="array">array</option>
          </select>

          {namespace === 'inputs' && (
            <label className="flex items-center gap-1 cursor-pointer">
              <input
                type="checkbox"
                checked={field.required || false}
                onChange={(e) => handleUpdateField(namespace, key, { required: e.target.checked })}
                className="rounded border-gray-300 w-3 h-3"
              />
              <span className="text-xs">Required</span>
            </label>
          )}
        </div>

        <input
          type="text"
          value={field.default !== undefined ? field.default : ''}
          onChange={(e) => handleUpdateField(namespace, key, { default: e.target.value })}
          placeholder="Default value (optional)..."
          className="w-full px-2 py-1 text-xs border border-gray-200 rounded"
        />
      </div>
    );
  };

  const renderSection = (
    namespace: 'inputs' | 'outputs' | 'intermediate',
    title: string,
    description: string
  ) => {
    const isExpanded = expandedSection === namespace;
    const fields = Object.entries(memory[namespace]);
    const requiredCount = fields.filter(([_, f]) => f.required).length;

    return (
      <div className="mb-3">
        <button
          onClick={() => setExpandedSection(isExpanded ? null as any : namespace)}
          className="w-full flex items-center justify-between p-2 hover:bg-gray-50 rounded transition-colors"
        >
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-500" />
            )}
            <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
            <span className="text-xs text-gray-500">
              ({fields.length}{namespace === 'inputs' && requiredCount > 0 ? `, ${requiredCount} required` : ''})
            </span>
          </div>
          <Plus
            className="w-4 h-4 text-gray-500 hover:text-gray-700"
            onClick={(e) => {
              e.stopPropagation();
              handleAddField(namespace);
            }}
          />
        </button>

        {isExpanded && (
          <div className="mt-2 px-2">
            <p className="text-xs text-gray-600 mb-2">{description}</p>
            {fields.length > 0 ? (
              <div className="space-y-1">
                {fields.map(([key, field]) => renderField(namespace, key, field))}
              </div>
            ) : (
              <p className="text-xs text-gray-500 text-center py-3 italic">
                No {namespace} defined. Click + to add.
              </p>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 border-l border-gray-200">
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="p-3 border-b border-gray-200 bg-white hover:bg-gray-50 transition-colors flex items-center gap-2 text-left"
      >
        {isCollapsed ? (
          <ChevronRight className="w-4 h-4 text-gray-500 flex-shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-500 flex-shrink-0" />
        )}
        <h2 className="text-sm font-bold text-gray-900">Memory Schema</h2>
      </button>

      {!isCollapsed && (
        <>
          <div className="flex-1 overflow-y-auto p-3">
            {renderSection(
              'inputs',
              'Inputs',
              'Values provided when the graph starts execution (via API or CLI)'
            )}
            {renderSection(
              'intermediate',
              'Intermediate',
              'Temporary values used during graph execution'
            )}
            {renderSection(
              'outputs',
              'Outputs',
              'Final results returned when the graph completes'
            )}
          </div>

          <div className="p-3 border-t border-gray-200 bg-blue-50">
            <div className="flex items-start gap-2">
              <Check className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs text-blue-900 font-medium">Memory Bindings</p>
                <p className="text-xs text-blue-700 mt-1">
                  Reference memory in config fields using <code className="bg-blue-100 px-1 rounded">{'{memory.field_name}'}</code>
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
