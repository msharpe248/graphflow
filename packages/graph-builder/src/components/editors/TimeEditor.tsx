import { EditorProps } from './types';

/**
 * TimeEditor - Inline time picker
 *
 * Schema configuration:
 * {
 *   "type": "string",
 *   "x-editor": "time",
 *   "description": "Time in HH:MM format"
 * }
 *
 * Value format: "HH:MM" (24-hour format)
 */
export default function TimeEditor({ value, onChange, schema }: EditorProps) {
  return (
    <input
      type="time"
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      placeholder={schema.description || 'Select time'}
    />
  );
}
