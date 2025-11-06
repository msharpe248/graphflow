import { useState } from 'react';
import { Edit2, AlertCircle, CheckCircle } from 'lucide-react';
import { EditorProps } from './types';
import BaseEditorModal from './BaseEditorModal';

export default function JsonEditor({ value, onChange, schema }: EditorProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editValue, setEditValue] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleOpenModal = () => {
    // Convert value to formatted JSON string
    try {
      const formatted = JSON.stringify(value, null, 2);
      setEditValue(formatted || '{}');
    } catch (e) {
      setEditValue(typeof value === 'string' ? value : '{}');
    }
    setValidationError(null);
    setIsModalOpen(true);
  };

  const handleTextChange = (newText: string) => {
    setEditValue(newText);

    // Validate JSON
    try {
      JSON.parse(newText);
      setValidationError(null);
    } catch (e) {
      setValidationError(e instanceof Error ? e.message : 'Invalid JSON');
    }
  };

  const handleSave = () => {
    try {
      const parsed = JSON.parse(editValue);
      onChange(parsed);
      setValidationError(null);
    } catch (e) {
      setValidationError(e instanceof Error ? e.message : 'Invalid JSON');
      throw e; // Prevent modal from closing
    }
  };

  const handleFormat = () => {
    try {
      const parsed = JSON.parse(editValue);
      const formatted = JSON.stringify(parsed, null, 2);
      setEditValue(formatted);
      setValidationError(null);
    } catch (e) {
      setValidationError(e instanceof Error ? e.message : 'Invalid JSON - cannot format');
    }
  };

  // Display preview
  const getPreview = () => {
    try {
      const str = JSON.stringify(value);
      if (str.length > 50) {
        return str.substring(0, 47) + '...';
      }
      return str;
    } catch (e) {
      return String(value);
    }
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={getPreview()}
          readOnly
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-700 cursor-default"
          placeholder="{}"/>
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
        title={schema.description || 'Edit JSON'}
      >
        <div className="space-y-4">
          {/* Validation Status */}
          {validationError ? (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-medium text-red-900">Invalid JSON</div>
                <div className="text-xs text-red-700 mt-1">{validationError}</div>
              </div>
            </div>
          ) : editValue && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-md flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div className="text-sm font-medium text-green-900">Valid JSON</div>
            </div>
          )}

          {/* Format Button */}
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleFormat}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Format
            </button>
          </div>

          {/* JSON Editor */}
          <textarea
            value={editValue}
            onChange={(e) => handleTextChange(e.target.value)}
            className="w-full h-96 px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder='{\n  "key": "value"\n}'
            spellCheck={false}
          />

          <div className="text-xs text-gray-500">
            Tip: Use the Format button to prettify your JSON
          </div>
        </div>
      </BaseEditorModal>
    </>
  );
}
