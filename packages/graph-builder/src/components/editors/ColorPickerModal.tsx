import { useState } from 'react';
import { Edit2 } from 'lucide-react';
import { EditorProps } from './types';
import BaseEditorModal from './BaseEditorModal';

// Muted color palette - soft, professional colors
const PRESET_COLORS = [
  // Grays
  '#94a3b8', '#64748b', '#475569',
  // Blues
  '#93c5fd', '#60a5fa', '#3b82f6',
  // Greens
  '#86efac', '#4ade80', '#22c55e',
  // Yellows/Ambers
  '#fcd34d', '#fbbf24', '#f59e0b',
  // Reds/Pinks
  '#fca5a5', '#f87171', '#ef4444',
  // Purples
  '#c4b5fd', '#a78bfa', '#8b5cf6',
  // Oranges
  '#fdba74', '#fb923c', '#f97316',
  // Common
  '#ffffff', '#000000',
];

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

      <BaseEditorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        title={schema.description || 'Pick Color'}
      >
        <div className="space-y-6">
          {/* Preview */}
          <div className="flex items-center gap-4">
            <div
              className="w-24 h-24 rounded-lg border-2 border-gray-300 shadow-inner"
              style={{ backgroundColor: tempColor }}
            />
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Current Color
              </label>
              <div className="text-2xl font-mono font-semibold text-gray-900">
                {tempColor}
              </div>
            </div>
          </div>

          {/* Preset colors */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Preset Colors
            </label>
            <div className="grid grid-cols-10 gap-2">
              {PRESET_COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setTempColor(color)}
                  className={`w-10 h-10 rounded-lg border-2 transition-all ${
                    tempColor === color
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
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Manual Entry
            </label>
            <div className="flex gap-3">
              <input
                type="color"
                value={tempColor}
                onChange={(e) => setTempColor(e.target.value)}
                className="w-16 h-12 rounded border border-gray-300 cursor-pointer"
              />
              <input
                type="text"
                value={tempColor}
                onChange={(e) => setTempColor(e.target.value)}
                placeholder="#000000"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Enter a hex color code (e.g., #3b82f6) or use the color picker
            </p>
          </div>
        </div>
      </BaseEditorModal>
    </>
  );
}
