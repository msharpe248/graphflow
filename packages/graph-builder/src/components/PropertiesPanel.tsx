import { useGraphStore } from '@/stores/graphStore';
import { Step } from '@/types/graph';
import { X } from 'lucide-react';

export default function PropertiesPanel() {
  const { nodes, selectedNodeId, setSelectedNode, updateNode, deleteNode } = useGraphStore();

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

  const handleConfigChange = (key: string, value: any) => {
    updateNode(selectedNodeId!, {
      config: {
        ...step.config,
        [key]: value,
      },
    });
  };

  const handleMemoryReadsChange = (value: string) => {
    updateNode(selectedNodeId!, {
      memory_reads: value.split(',').map((s) => s.trim()).filter(Boolean),
    });
  };

  const handleMemoryWritesChange = (value: string) => {
    updateNode(selectedNodeId!, {
      memory_writes: value.split(',').map((s) => s.trim()).filter(Boolean),
    });
  };

  const handleDelete = () => {
    if (confirm(`Delete step "${step.id}"?`)) {
      deleteNode(selectedNodeId!);
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50 border-l border-gray-200">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-900">Properties</h2>
        <button
          onClick={() => setSelectedNode(null)}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="p-4 space-y-6">
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

        {/* Memory reads */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Memory Reads
          </label>
          <input
            type="text"
            value={step.memory_reads?.join(', ') || ''}
            onChange={(e) => handleMemoryReadsChange(e.target.value)}
            placeholder="key1, key2, key3"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
          <p className="text-xs text-gray-500 mt-1">Comma-separated memory keys to read</p>
        </div>

        {/* Memory writes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Memory Writes
          </label>
          <input
            type="text"
            value={step.memory_writes?.join(', ') || ''}
            onChange={(e) => handleMemoryWritesChange(e.target.value)}
            placeholder="key1, key2, key3"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
          <p className="text-xs text-gray-500 mt-1">Comma-separated memory keys to write</p>
        </div>

        {/* Config */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Configuration
          </label>
          <div className="space-y-3">
            {stepTypeInfo.configSchema && Object.keys(stepTypeInfo.configSchema).length > 0 ? (
              Object.entries(stepTypeInfo.configSchema).map(([key, schema]: [string, any]) => (
                <div key={key}>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    {key}
                  </label>
                  {schema.type === 'boolean' ? (
                    <input
                      type="checkbox"
                      checked={step.config[key] ?? schema.default ?? false}
                      onChange={(e) => handleConfigChange(key, e.target.checked)}
                      className="rounded border-gray-300"
                    />
                  ) : schema.enum ? (
                    <select
                      value={step.config[key] ?? schema.default ?? ''}
                      onChange={(e) => handleConfigChange(key, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                      <option value="">Select...</option>
                      {schema.enum.map((opt: string) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </select>
                  ) : schema.type === 'number' ? (
                    <input
                      type="number"
                      value={step.config[key] ?? schema.default ?? ''}
                      onChange={(e) => handleConfigChange(key, parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  ) : schema.type === 'object' || schema.type === 'array' ? (
                    <textarea
                      value={
                        step.config[key]
                          ? JSON.stringify(step.config[key], null, 2)
                          : ''
                      }
                      onChange={(e) => {
                        try {
                          const parsed = JSON.parse(e.target.value);
                          handleConfigChange(key, parsed);
                        } catch {
                          // Invalid JSON, don't update
                        }
                      }}
                      placeholder={schema.type === 'object' ? '{}' : '[]'}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
                    />
                  ) : (
                    <textarea
                      value={step.config[key] ?? schema.default ?? ''}
                      onChange={(e) => handleConfigChange(key, e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  )}
                  {schema.description && (
                    <p className="text-xs text-gray-500 mt-1">{schema.description}</p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-xs text-gray-500">No configuration required</p>
            )}
          </div>
        </div>

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
    </div>
  );
}
