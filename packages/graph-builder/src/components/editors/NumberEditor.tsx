import { useState, useEffect } from 'react';
import { Plus, Minus } from 'lucide-react';
import { EditorProps } from './types';

export default function NumberEditor({ value, onChange, schema }: EditorProps) {
  const [localValue, setLocalValue] = useState<string>(
    value !== undefined && value !== null ? String(value) : ''
  );

  useEffect(() => {
    setLocalValue(value !== undefined && value !== null ? String(value) : '');
  }, [value]);

  const handleChange = (newValue: string) => {
    setLocalValue(newValue);

    // Parse and validate
    if (newValue === '' || newValue === '-' || newValue === '.') {
      // Allow empty, negative sign, or decimal point temporarily
      return;
    }

    const parsed = parseFloat(newValue);
    if (!isNaN(parsed)) {
      onChange(parsed);
    }
  };

  const handleBlur = () => {
    // On blur, ensure we have a valid number
    const parsed = parseFloat(localValue);
    if (isNaN(parsed)) {
      setLocalValue(value !== undefined && value !== null ? String(value) : '0');
      onChange(0);
    } else {
      onChange(parsed);
    }
  };

  const increment = () => {
    const current = parseFloat(localValue) || 0;
    const step = schema.type === 'integer' ? 1 : 0.1;
    const newValue = current + step;
    setLocalValue(String(newValue));
    onChange(newValue);
  };

  const decrement = () => {
    const current = parseFloat(localValue) || 0;
    const step = schema.type === 'integer' ? 1 : 0.1;
    const newValue = current - step;
    setLocalValue(String(newValue));
    onChange(newValue);
  };

  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        onClick={decrement}
        className="p-1.5 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
        aria-label="Decrease"
      >
        <Minus className="w-4 h-4" />
      </button>

      <input
        type="text"
        value={localValue}
        onChange={(e) => handleChange(e.target.value)}
        onBlur={handleBlur}
        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-center"
        placeholder="0"
      />

      <button
        type="button"
        onClick={increment}
        className="p-1.5 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
        aria-label="Increase"
      >
        <Plus className="w-4 h-4" />
      </button>
    </div>
  );
}
