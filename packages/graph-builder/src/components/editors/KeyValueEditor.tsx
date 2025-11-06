import { useState } from 'react';
import { Edit2, Plus, Trash2 } from 'lucide-react';
import { EditorProps } from './types';
import BaseEditorModal from './BaseEditorModal';

interface KeyValuePair {
  key: string;
  value: string;
}

export default function KeyValueEditor({ value, onChange, schema }: EditorProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [pairs, setPairs] = useState<KeyValuePair[]>([]);

  const handleOpenModal = () => {
    // Convert object to key-value pairs
    const initialPairs: KeyValuePair[] = [];
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      Object.entries(value).forEach(([k, v]) => {
        initialPairs.push({ key: k, value: String(v) });
      });
    }

    // Always have at least one empty row
    if (initialPairs.length === 0) {
      initialPairs.push({ key: '', value: '' });
    }

    setPairs(initialPairs);
    setIsModalOpen(true);
  };

  const handleAddRow = () => {
    setPairs([...pairs, { key: '', value: '' }]);
  };

  const handleRemoveRow = (index: number) => {
    setPairs(pairs.filter((_, i) => i !== index));
  };

  const handleKeyChange = (index: number, newKey: string) => {
    const updated = [...pairs];
    updated[index].key = newKey;
    setPairs(updated);
  };

  const handleValueChange = (index: number, newValue: string) => {
    const updated = [...pairs];
    updated[index].value = newValue;
    setPairs(updated);
  };

  const handleSave = () => {
    // Convert pairs back to object
    const obj: Record<string, string> = {};
    pairs.forEach(({ key, value }) => {
      if (key.trim()) {  // Only include pairs with non-empty keys
        obj[key.trim()] = value;
      }
    });
    onChange(obj);
  };

  // Display preview
  const getPreview = () => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      return '{}';
    }
    const count = Object.keys(value).length;
    if (count === 0) return '{}';
    if (count === 1) {
      const [key] = Object.keys(value);
      return `{ ${key}: ... }`;
    }
    return `{ ${count} entries }`;
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={getPreview()}
          readOnly
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-700 cursor-default"
          placeholder="{}"
        />
        <button
          type="button"
          onClick={handleOpenModal}
          className="px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors flex items-center gap-1.5"
        >
          <Edit2 className="w-4 h-4" />
          Edit
        </button>
      </div>

      <BaseEditorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        title={schema.description || 'Edit Key-Value Pairs'}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Add key-value pairs. Empty keys will be ignored.
            </p>
            <button
              type="button"
              onClick={handleAddRow}
              className="px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors flex items-center gap-1.5"
            >
              <Plus className="w-4 h-4" />
              Add Row
            </button>
          </div>

          {/* Table */}
          <div className="border border-gray-300 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Key
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Value
                  </th>
                  <th className="px-4 py-2 w-16"></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {pairs.map((pair, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-2">
                      <input
                        type="text"
                        value={pair.key}
                        onChange={(e) => handleKeyChange(index, e.target.value)}
                        placeholder="key"
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-4 py-2">
                      <input
                        type="text"
                        value={pair.value}
                        onChange={(e) => handleValueChange(index, e.target.value)}
                        placeholder="value"
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-4 py-2 text-center">
                      <button
                        type="button"
                        onClick={() => handleRemoveRow(index)}
                        className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                        aria-label="Remove row"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {pairs.length === 0 && (
            <div className="text-center py-8 text-sm text-gray-500">
              No entries. Click "Add Row" to start.
            </div>
          )}
        </div>
      </BaseEditorModal>
    </>
  );
}
