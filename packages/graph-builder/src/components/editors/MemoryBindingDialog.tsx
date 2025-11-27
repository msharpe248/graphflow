import { useState } from 'react';
import { Search, ChevronDown, ChevronRight, X } from 'lucide-react';
import { useGraphStore } from '@/stores/graphStore';

interface MemoryBindingDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (binding: string) => void;
  currentValue?: string;
  title?: string;
  description?: string;
}

interface SectionState {
  inputs: boolean;
  intermediate: boolean;
  outputs: boolean;
  config: boolean;
  environment: boolean;
  secrets: boolean;
}

export default function MemoryBindingDialog({
  isOpen,
  onClose,
  onSelect,
  currentValue,
  title = 'Select Memory Location',
  description = 'Choose a memory location to bind this value to, or create a new one',
}: MemoryBindingDialogProps) {
  const { memory, setMemoryValue, setMemory, nodes } = useGraphStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [sections, setSections] = useState<SectionState>({
    inputs: true,
    intermediate: true,
    outputs: true,
    config: false,
    environment: false,
    secrets: false,
  });

  // Filter memory entries by search query
  const filterEntries = (entries: [string, any][]): [string, any][] => {
    if (!searchQuery.trim()) return entries;
    const query = searchQuery.toLowerCase();
    return entries.filter(([key, field]) =>
      key.toLowerCase().includes(query) ||
      (field.description && field.description.toLowerCase().includes(query))
    );
  };

  // Get steps using a specific binding
  const getStepsUsing = (binding: string): string[] => {
    return nodes
      .filter((n) => n.type === 'custom' && n.data.step)
      .filter((n) => {
        const configStr = JSON.stringify(n.data.step.config);
        return configStr.includes(binding);
      })
      .map((n) => n.data.step.id);
  };

  const handleSelect = (binding: string) => {
    onSelect(binding);
    onClose();
    setSearchQuery('');
  };

  const handleAddInput = () => {
    const key = prompt('Enter new input name:');
    if (key && !memory.inputs[key]) {
      setMemoryValue('inputs', key, '');
    }
  };

  const handleAddIntermediate = () => {
    const key = prompt('Enter new intermediate variable name:');
    if (key && !memory.intermediate[key]) {
      setMemoryValue('intermediate', key, '');
    }
  };

  const handleAddOutput = () => {
    const key = prompt('Enter new output name:');
    if (key && !memory.outputs[key]) {
      setMemoryValue('outputs', key, '');
    }
  };

  const handleAddConfig = () => {
    const key = prompt('Enter new config name:');
    if (key && !(memory.config || {})[key]) {
      setMemory({
        config: {
          ...(memory.config || {}),
          [key]: { type: 'string', description: '' },
        },
      });
    }
  };

  const handleAddEnvironment = () => {
    const key = prompt('Enter new environment variable name:');
    if (key && !(memory.environment || {})[key]) {
      setMemory({
        environment: {
          ...(memory.environment || {}),
          [key]: { type: 'string', key: key.toUpperCase(), description: '', required: false },
        },
      });
    }
  };

  const handleAddSecret = () => {
    const key = prompt('Enter new secret name:');
    if (key && !(memory.secrets || {})[key]) {
      setMemory({
        secrets: {
          ...(memory.secrets || {}),
          [key]: { provider: 'env', key: key.toUpperCase(), description: '' },
        },
      });
    }
  };

  const toggleSection = (section: keyof SectionState) => {
    setSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  // Render a memory section
  const renderSection = (
    key: keyof SectionState,
    label: string,
    entries: [string, any][],
    bindingPrefix: string,
    onAdd: () => void,
    colorClass: { active: string; hover: string; text: string }
  ) => {
    const filteredEntries = filterEntries(entries);

    return (
      <div className="mb-4">
        <button
          onClick={() => toggleSection(key)}
          className="w-full flex items-center justify-between mb-2 p-2 hover:bg-gray-50 rounded transition-colors"
        >
          <div className="flex items-center gap-2">
            {sections[key] ? (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-500" />
            )}
            <h4 className="text-sm font-semibold text-gray-700">{label}</h4>
            <span className="text-xs text-gray-500">({filteredEntries.length})</span>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAdd();
            }}
            className={`text-xs ${colorClass.text} px-2 py-1`}
          >
            + Add
          </button>
        </button>
        {sections[key] && (
          <div className="space-y-1 ml-2">
            {filteredEntries.map(([fieldKey, field]) => {
              const binding = `{${bindingPrefix}.${fieldKey}}`;
              const isCurrentBinding = binding === currentValue;
              const stepsUsing = getStepsUsing(binding);

              return (
                <button
                  key={fieldKey}
                  onClick={() => handleSelect(binding)}
                  className={`w-full text-left px-3 py-2 rounded border text-sm ${
                    isCurrentBinding
                      ? `${colorClass.active}`
                      : `border-gray-200 ${colorClass.hover}`
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-medium">{fieldKey}</span>
                    <span className="text-xs text-gray-500">
                      {field.type || field.provider || 'string'}
                      {field.key && ` → ${field.key}`}
                    </span>
                  </div>
                  {field.description && (
                    <p className="text-xs text-gray-500 mt-0.5 truncate">{field.description}</p>
                  )}
                  {stepsUsing.length > 0 && (
                    <p className="text-xs text-gray-600 mt-1">Used by: {stepsUsing.join(', ')}</p>
                  )}
                </button>
              );
            })}
            {filteredEntries.length === 0 && (
              <p className="text-xs text-gray-500 italic text-center py-2">
                {searchQuery ? `No matching ${label.toLowerCase()}` : `No ${label.toLowerCase()} defined`}
              </p>
            )}
          </div>
        )}
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-gray-900">{title}</h3>
              <p className="text-xs text-gray-600 mt-1">{description}</p>
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Search Input */}
          <div className="mt-3 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search memory locations..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Inputs Section */}
          {renderSection(
            'inputs',
            'Inputs',
            Object.entries(memory.inputs || {}),
            'memory',
            handleAddInput,
            {
              active: 'border-blue-500 bg-blue-50',
              hover: 'hover:border-blue-300 hover:bg-gray-50',
              text: 'text-blue-600 hover:text-blue-700',
            }
          )}

          {/* Intermediate Section */}
          {renderSection(
            'intermediate',
            'Intermediate',
            Object.entries(memory.intermediate || {}),
            'memory',
            handleAddIntermediate,
            {
              active: 'border-purple-500 bg-purple-50',
              hover: 'hover:border-purple-300 hover:bg-gray-50',
              text: 'text-purple-600 hover:text-purple-700',
            }
          )}

          {/* Outputs Section */}
          {renderSection(
            'outputs',
            'Outputs',
            Object.entries(memory.outputs || {}),
            'memory',
            handleAddOutput,
            {
              active: 'border-green-500 bg-green-50',
              hover: 'hover:border-green-300 hover:bg-gray-50',
              text: 'text-green-600 hover:text-green-700',
            }
          )}

          {/* Config Section */}
          {renderSection(
            'config',
            'Config',
            Object.entries(memory.config || {}),
            'config',
            handleAddConfig,
            {
              active: 'border-amber-500 bg-amber-50',
              hover: 'hover:border-amber-300 hover:bg-gray-50',
              text: 'text-amber-600 hover:text-amber-700',
            }
          )}

          {/* Environment Section */}
          {renderSection(
            'environment',
            'Environment',
            Object.entries(memory.environment || {}),
            'env',
            handleAddEnvironment,
            {
              active: 'border-teal-500 bg-teal-50',
              hover: 'hover:border-teal-300 hover:bg-gray-50',
              text: 'text-teal-600 hover:text-teal-700',
            }
          )}

          {/* Secrets Section */}
          {renderSection(
            'secrets',
            'Secrets',
            Object.entries(memory.secrets || {}),
            'secrets',
            handleAddSecret,
            {
              active: 'border-red-500 bg-red-50',
              hover: 'hover:border-red-300 hover:bg-gray-50',
              text: 'text-red-600 hover:text-red-700',
            }
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 flex gap-2 justify-end">
          <button
            onClick={() => {
              onClose();
              setSearchQuery('');
            }}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
