import { useState } from 'react';
import { Edit2 } from 'lucide-react';
import { EditorProps } from './types';
import BaseEditorModal from './BaseEditorModal';

// Color palette organized as vertical towers with 5 shades each
// Each array represents a vertical tower from light to dark
const COLOR_TOWERS = [
  // Grays
  ['#f1f5f9', '#cbd5e1', '#94a3b8', '#64748b', '#475569'],
  // Blues
  ['#dbeafe', '#93c5fd', '#60a5fa', '#3b82f6', '#2563eb'],
  // Greens
  ['#d1fae5', '#86efac', '#4ade80', '#22c55e', '#16a34a'],
  // Yellows
  ['#fef3c7', '#fde68a', '#fcd34d', '#fbbf24', '#f59e0b'],
  // Reds
  ['#fee2e2', '#fca5a5', '#f87171', '#ef4444', '#dc2626'],
  // Purples
  ['#ede9fe', '#c4b5fd', '#a78bfa', '#8b5cf6', '#7c3aed'],
  // Oranges
  ['#fed7aa', '#fdba74', '#fb923c', '#f97316', '#ea580c'],
  // Pinks
  ['#fce7f3', '#f9a8d4', '#f472b6', '#ec4899', '#db2777'],
];

// Special colors shown separately
const SPECIAL_COLORS = ['#ffffff', '#000000'];

export default function ColorPickerModal({ value, onChange, schema }: EditorProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [tempColor, setTempColor] = useState(value || '#000000');

  const handleOpenModal = () => {
    setTempColor(value || '#000000');
    setIsModalOpen(true);
  };

  const handleSave = () => {
    onChange(tempColor);
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder="#000000"
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <div
          className="w-10 h-10 rounded border-2 border-gray-300"
          style={{ backgroundColor: value || '#000000' }}
        />
        <button
          type="button"
          onClick={handleOpenModal}
          className="px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors flex items-center gap-1.5"
        >
          <Edit2 className="w-4 h-4" />
          Pick
        </button>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setIsModalOpen(false)}>
          <div
            className="bg-white rounded-lg shadow-xl w-auto max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-base font-semibold text-gray-900">{schema.description || 'Text Color'}</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 hover:bg-gray-100 rounded-md transition-colors"
              >
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-4 space-y-4">
              {/* Preview */}
              <div className="flex items-center gap-3">
                <div
                  className="w-16 h-16 rounded-lg border-2 border-gray-300 shadow-inner flex-shrink-0"
                  style={{ backgroundColor: tempColor }}
                />
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Current Color
                  </label>
                  <div className="text-base font-mono font-semibold text-gray-900">
                    {tempColor}
                  </div>
                </div>
              </div>

              {/* Preset colors - vertical towers */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-2">
                  Preset Colors
                </label>
                <div className="flex gap-1.5">
                  {COLOR_TOWERS.map((tower, towerIndex) => (
                    <div key={towerIndex} className="flex flex-col gap-1">
                      {tower.map((color) => (
                        <button
                          key={color}
                          type="button"
                          onClick={() => setTempColor(color)}
                          className={`w-8 h-8 rounded border-2 transition-all ${
                            tempColor.toLowerCase() === color.toLowerCase()
                              ? 'border-blue-500 ring-2 ring-blue-200 scale-110'
                              : 'border-gray-300 hover:border-gray-400 hover:scale-105'
                          }`}
                          style={{ backgroundColor: color }}
                          title={color}
                        />
                      ))}
                    </div>
                  ))}
                </div>

                {/* Special colors - white and black */}
                <div className="flex gap-1.5 mt-2 pt-2 border-t border-gray-200">
                  {SPECIAL_COLORS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setTempColor(color)}
                      className={`w-8 h-8 rounded border-2 transition-all ${
                        tempColor.toLowerCase() === color.toLowerCase()
                          ? 'border-blue-500 ring-2 ring-blue-200 scale-110'
                          : 'border-gray-300 hover:border-gray-400 hover:scale-105'
                      }`}
                      style={{ backgroundColor: color }}
                      title={color}
                    />
                  ))}
                </div>
              </div>

              {/* Manual input */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-2">
                  Manual Entry
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={tempColor}
                    onChange={(e) => setTempColor(e.target.value)}
                    className="w-10 h-10 rounded border border-gray-300 cursor-pointer"
                  />
                  <input
                    type="text"
                    value={tempColor}
                    onChange={(e) => setTempColor(e.target.value)}
                    placeholder="#000000"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1.5">
                  Enter a hex color code (e.g., #3b82f6) or use the color picker
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-gray-200 flex justify-end gap-2">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => { handleSave(); setIsModalOpen(false); }}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
