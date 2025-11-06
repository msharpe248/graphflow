import { EditorProps } from './types';

export default function BooleanEditor({ value, onChange }: EditorProps) {
  return (
    <div className="flex items-center">
      <input
        type="checkbox"
        checked={value === true}
        onChange={(e) => onChange(e.target.checked)}
        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
      />
    </div>
  );
}
