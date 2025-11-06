// Export all editors
export { default as StringEditor } from './StringEditor';
export { default as NumberEditor } from './NumberEditor';
export { default as BooleanEditor } from './BooleanEditor';
export { default as JsonEditor } from './JsonEditor';
export { default as KeyValueEditor } from './KeyValueEditor';
export { default as ColorPickerModal } from './ColorPickerModal';
export { default as TableEditor } from './TableEditor';
export { default as BaseEditorModal } from './BaseEditorModal';

// Export registry functions
export { getEditorForSchema, getEditorForType, getEditorByName, hasEditor } from './EditorRegistry';

// Export types
export type { EditorProps, EditorType, EditorConfig } from './types';
