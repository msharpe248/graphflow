import { useState } from 'react';
import { Edit2, Plus, Trash2 } from 'lucide-react';
import { EditorProps } from './types';
import BaseEditorModal from './BaseEditorModal';

interface TableColumn {
  key: string;
  label: string;
  placeholder?: string;
}

interface TableEditorConfig {
  columns: TableColumn[];
  initialRows?: number;
  addRowLabel?: string;
  emptyMessage?: string;
}

/**
 * TableEditor - Modal editor for tabular data
 *
 * Schema configuration via x-editor-config:
 * {
 *   "type": "object",
 *   "x-editor": "table",
 *   "x-editor-config": {
 *     "columns": [
 *       { "key": "name", "label": "Header Name", "placeholder": "Content-Type" },
 *       { "key": "value", "label": "Value", "placeholder": "application/json" }
 *     ],
 *     "initialRows": 3,
 *     "addRowLabel": "Add Header",
 *     "emptyMessage": "No headers defined"
 *   }
 * }
 */
export default function TableEditor({ value, onChange, schema }: EditorProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Get editor config from schema
  const editorConfig: TableEditorConfig = schema['x-editor-config'] || {
    columns: [
      { key: 'key', label: 'Key', placeholder: 'key' },
      { key: 'value', label: 'Value', placeholder: 'value' }
    ],
    initialRows: 1,
    addRowLabel: 'Add Row',
    emptyMessage: 'No rows defined'
  };

  // Parse value - can be object (for key-value like headers) or array of objects
  const parseValue = (): Record<string, any>[] => {
    if (!value) return [];

    if (Array.isArray(value)) {
      return value;
    }

    if (typeof value === 'object' && value !== null) {
      // Convert object to array of rows
      // For headers: {"Content-Type": "application/json"} -> [{name: "Content-Type", value: "application/json"}]
      return Object.entries(value).map(([key, val]) => ({
        [editorConfig.columns[0]?.key || 'key']: key,
        [editorConfig.columns[1]?.key || 'value']: val
      }));
    }

    return [];
  };

  // Format value for display
  const formatValue = (): string => {
    const rows = parseValue();
    if (rows.length === 0) return editorConfig.emptyMessage || 'No data';

    // Show count of rows
    return `${rows.length} row${rows.length === 1 ? '' : 's'}`;
  };

  const [tempRows, setTempRows] = useState<Record<string, any>[]>([]);

  const handleOpenModal = () => {
    const rows = parseValue();

    // If no rows and initialRows is set, create empty rows
    if (rows.length === 0 && editorConfig.initialRows) {
      const emptyRows = Array.from({ length: editorConfig.initialRows }, () => {
        const row: Record<string, any> = {};
        editorConfig.columns.forEach(col => {
          row[col.key] = '';
        });
        return row;
      });
      setTempRows(emptyRows);
    } else {
      setTempRows(rows);
    }

    setIsModalOpen(true);
  };

  const handleSave = () => {
    // Filter out completely empty rows
    const nonEmptyRows = tempRows.filter(row => {
      return editorConfig.columns.some(col => {
        const val = row[col.key];
        return val !== undefined && val !== null && val !== '';
      });
    });

    // Convert back to original format
    // If original was an object, convert back to object
    if (typeof value === 'object' && !Array.isArray(value)) {
      const obj: Record<string, any> = {};
      nonEmptyRows.forEach(row => {
        const keyCol = editorConfig.columns[0];
        const valueCol = editorConfig.columns[1];
        const key = row[keyCol.key];
        const val = row[valueCol.key];
        if (key) {
          obj[key] = val;
        }
      });
      onChange(obj);
    } else {
      // Keep as array
      onChange(nonEmptyRows);
    }
  };

  const handleAddRow = () => {
    const newRow: Record<string, any> = {};
    editorConfig.columns.forEach(col => {
      newRow[col.key] = '';
    });
    setTempRows([...tempRows, newRow]);
  };

  const handleRemoveRow = (index: number) => {
    setTempRows(tempRows.filter((_, i) => i !== index));
  };

  const handleCellChange = (rowIndex: number, columnKey: string, cellValue: string) => {
    const updated = [...tempRows];
    updated[rowIndex] = {
      ...updated[rowIndex],
      [columnKey]: cellValue
    };
    setTempRows(updated);
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <div className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm text-gray-700">
          {formatValue()}
        </div>
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
        title={schema.description || 'Edit Table'}
      >
        <div className="space-y-4">
          {/* Table */}
          <div className="border border-gray-300 rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-100 border-b border-gray-300">
                    {editorConfig.columns.map((col) => (
                      <th
                        key={col.key}
                        className="px-3 py-2 text-left text-xs font-semibold text-gray-700"
                      >
                        {col.label}
                      </th>
                    ))}
                    <th className="px-3 py-2 w-12"></th>
                  </tr>
                </thead>
                <tbody>
                  {tempRows.length === 0 ? (
                    <tr>
                      <td
                        colSpan={editorConfig.columns.length + 1}
                        className="px-3 py-8 text-center text-sm text-gray-500 italic"
                      >
                        {editorConfig.emptyMessage || 'No rows defined. Click "Add Row" to get started.'}
                      </td>
                    </tr>
                  ) : (
                    tempRows.map((row, rowIndex) => (
                      <tr key={rowIndex} className="border-b border-gray-200 hover:bg-gray-50">
                        {editorConfig.columns.map((col) => (
                          <td key={col.key} className="px-3 py-2">
                            <input
                              type="text"
                              value={row[col.key] || ''}
                              onChange={(e) => handleCellChange(rowIndex, col.key, e.target.value)}
                              placeholder={col.placeholder || col.label}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </td>
                        ))}
                        <td className="px-3 py-2">
                          <button
                            type="button"
                            onClick={() => handleRemoveRow(rowIndex)}
                            className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                            title="Delete row"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Add Row Button */}
          <button
            type="button"
            onClick={handleAddRow}
            className="w-full px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            {editorConfig.addRowLabel || 'Add Row'}
          </button>

          {/* Help text */}
          <p className="text-xs text-gray-500">
            Empty rows will be automatically removed when you save.
          </p>
        </div>
      </BaseEditorModal>
    </>
  );
}
