interface ColorPickerProps {
  value: string;
  onChange: (color: string) => void;
  label: string;
}

// Muted color palette - soft, professional colors that won't distract
const PRESET_COLORS = [
  // Grays
  '#94a3b8', // slate-400
  '#64748b', // slate-500
  '#475569', // slate-600

  // Blues
  '#93c5fd', // blue-300
  '#60a5fa', // blue-400
  '#3b82f6', // blue-500

  // Greens
  '#86efac', // green-300
  '#4ade80', // green-400
  '#22c55e', // green-500

  // Yellows/Ambers
  '#fcd34d', // yellow-300
  '#fbbf24', // yellow-400
  '#fbbf24', // yellow-400

  // Reds/Pinks
  '#fca5a5', // red-300
  '#f87171', // red-400
  '#ef4444', // red-500

  // Purples
  '#c4b5fd', // violet-300
  '#a78bfa', // violet-400
  '#8b5cf6', // violet-500

  // Oranges
  '#fdba74', // orange-300
  '#fb923c', // orange-400
  '#f97316', // orange-500
];

export default function ColorPicker({ value, onChange, label }: ColorPickerProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>

      {/* Preset colors */}
      <div className="grid grid-cols-6 gap-2 mb-3">
        {PRESET_COLORS.map((color) => (
          <button
            key={color}
            type="button"
            onClick={() => onChange(color)}
            className={`w-8 h-8 rounded border-2 transition-all ${
              value === color ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-300 hover:border-gray-400'
            }`}
            style={{ backgroundColor: color }}
            title={color}
          />
        ))}
      </div>

      {/* Manual input */}
      <div className="flex gap-2">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-12 h-10 rounded border border-gray-300 cursor-pointer"
        />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="#000000"
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
        />
      </div>
    </div>
  );
}
