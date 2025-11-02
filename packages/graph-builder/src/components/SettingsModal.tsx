import { useState } from 'react';
import { X } from 'lucide-react';
import { useGraphStore } from '@/stores/graphStore';
import { FieldDefinition } from '@/types/graph';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { metadata, memory, setMetadata, setMemory } = useGraphStore();
  const [activeTab, setActiveTab] = useState<'metadata' | 'memory'>('metadata');

  if (!isOpen) return null;

  const handleAddField = (namespace: 'inputs' | 'outputs' | 'intermediate') => {
    const key = prompt('Enter field name:');
    if (!key) return;

    const field: FieldDefinition = {
      type: 'string',
      description: '',
    };

    setMemory({
      [namespace]: {
        ...memory[namespace],
        [key]: field,
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
    field: Partial<FieldDefinition>
  ) => {
    setMemory({
      [namespace]: {
        ...memory[namespace],
        [key]: {
          ...memory[namespace][key],
          ...field,
        },
      },
    });
  };

  const renderMemorySection = (
    namespace: 'inputs' | 'outputs' | 'intermediate',
    title: string
  ) => (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-gray-700">{title}</h4>
        <button
          onClick={() => handleAddField(namespace)}
          className="px-3 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded transition-colors"
        >
          Add Field
        </button>
      </div>

      <div className="space-y-3">
        {Object.entries(memory[namespace]).map(([key, field]) => (
          <div key={key} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-start justify-between mb-2">
              <div className="font-medium text-sm text-gray-900">{key}</div>
              <button
                onClick={() => handleRemoveField(namespace, key)}
                className="text-red-600 hover:text-red-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Type</label>
                <select
                  value={field.type}
                  onChange={(e) =>
                    handleUpdateField(namespace, key, { type: e.target.value })
                  }
                  className="w-full px-2 py-1 text-xs border border-gray-300 rounded"
                >
                  <option value="string">string</option>
                  <option value="number">number</option>
                  <option value="boolean">boolean</option>
                  <option value="object">object</option>
                  <option value="array">array</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-gray-600 mb-1">Required</label>
                <input
                  type="checkbox"
                  checked={field.required || false}
                  onChange={(e) =>
                    handleUpdateField(namespace, key, { required: e.target.checked })
                  }
                  className="rounded border-gray-300"
                />
              </div>
            </div>

            <div className="mt-2">
              <label className="block text-xs text-gray-600 mb-1">Description</label>
              <input
                type="text"
                value={field.description || ''}
                onChange={(e) =>
                  handleUpdateField(namespace, key, { description: e.target.value })
                }
                className="w-full px-2 py-1 text-xs border border-gray-300 rounded"
                placeholder="Field description"
              />
            </div>
          </div>
        ))}

        {Object.keys(memory[namespace]).length === 0 && (
          <p className="text-xs text-gray-500 text-center py-4">
            No fields defined. Click "Add Field" to create one.
          </p>
        )}
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Graph Settings</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <div className="flex gap-4 px-4">
            <button
              onClick={() => setActiveTab('metadata')}
              className={`
                py-3 px-2 border-b-2 font-medium text-sm transition-colors
                ${
                  activeTab === 'metadata'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }
              `}
            >
              Metadata
            </button>
            <button
              onClick={() => setActiveTab('memory')}
              className={`
                py-3 px-2 border-b-2 font-medium text-sm transition-colors
                ${
                  activeTab === 'memory'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }
              `}
            >
              Memory Schema
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'metadata' ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Graph Name
                </label>
                <input
                  type="text"
                  value={metadata.name}
                  onChange={(e) => setMetadata({ name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={metadata.description}
                  onChange={(e) => setMetadata({ description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Version
                </label>
                <input
                  type="text"
                  value={metadata.version || '1.0'}
                  onChange={(e) => setMetadata({ version: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={metadata.tags?.join(', ') || ''}
                  onChange={(e) =>
                    setMetadata({
                      tags: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="ai, research, automation"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Author
                </label>
                <input
                  type="text"
                  value={metadata.author || ''}
                  onChange={(e) => setMetadata({ author: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
          ) : (
            <div>
              {renderMemorySection('inputs', 'Input Fields')}
              {renderMemorySection('outputs', 'Output Fields')}
              {renderMemorySection('intermediate', 'Intermediate Fields')}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity font-medium"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
