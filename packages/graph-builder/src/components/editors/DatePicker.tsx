import { EditorProps } from './types';

/**
 * DatePicker - Inline date picker
 *
 * Schema configuration:
 * {
 *   "type": "string",
 *   "x-editor": "date",
 *   "description": "Date in YYYY-MM-DD format"
 * }
 *
 * Value format: "YYYY-MM-DD" (ISO 8601 date format)
 */
export default function DatePicker({ value, onChange, schema }: EditorProps) {
  return (
    <input
      type="date"
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      placeholder={schema.description || 'Select date'}
    />
  );
}
