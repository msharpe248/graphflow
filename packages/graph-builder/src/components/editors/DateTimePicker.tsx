import { EditorProps } from './types';

/**
 * DateTimePicker - Inline datetime picker
 *
 * Schema configuration:
 * {
 *   "type": "string",
 *   "x-editor": "datetime",
 *   "description": "Date and time in ISO 8601 format"
 * }
 *
 * Value format: "YYYY-MM-DDTHH:MM" (ISO 8601 datetime-local format)
 */
export default function DateTimePicker({ value, onChange, schema }: EditorProps) {
  return (
    <input
      type="datetime-local"
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      placeholder={schema.description || 'Select date and time'}
    />
  );
}
