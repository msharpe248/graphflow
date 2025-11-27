import { EditorConfig } from './types';
import StringEditor from './StringEditor';
import SelectEditor from './SelectEditor';
import NumberEditor from './NumberEditor';
import BooleanEditor from './BooleanEditor';
import JsonEditor from './JsonEditor';
import KeyValueEditor from './KeyValueEditor';
import ColorPickerModal from './ColorPickerModal';
import TableEditor from './TableEditor';
import MarkdownEditor from './MarkdownEditor';
import DatePicker from './DatePicker';
import TimeEditor from './TimeEditor';
import DateTimePicker from './DateTimePicker';
import ToolEditor from './ToolEditor';

// Registry of all available editors
const EDITOR_REGISTRY: Record<string, EditorConfig> = {
  'string': {
    component: StringEditor,
    displayMode: 'inline',
  },
  'select': {
    component: SelectEditor,
    displayMode: 'inline',
  },
  'number': {
    component: NumberEditor,
    displayMode: 'inline',
  },
  'boolean': {
    component: BooleanEditor,
    displayMode: 'inline',
  },
  'json': {
    component: JsonEditor,
    displayMode: 'modal',
  },
  'keyvalue': {
    component: KeyValueEditor,
    displayMode: 'modal',
  },
  'color': {
    component: ColorPickerModal,
    displayMode: 'modal',
  },
  'table': {
    component: TableEditor,
    displayMode: 'modal',
  },
  'markdown': {
    component: MarkdownEditor,
    displayMode: 'modal',
  },
  'date': {
    component: DatePicker,
    displayMode: 'inline',
  },
  'time': {
    component: TimeEditor,
    displayMode: 'inline',
  },
  'datetime': {
    component: DateTimePicker,
    displayMode: 'inline',
  },
  'tools': {
    component: ToolEditor,
    displayMode: 'inline',
  },
};

/**
 * Get the appropriate editor based only on JSON Schema type
 * Used for Memory Panel where we want consistent type-based editing
 *
 * Priority:
 * 1. type field inference (boolean -> checkbox, number -> spinner)
 * 2. Default to JSON editor for unknown/complex types
 */
export function getEditorForType(schema: Record<string, any>): EditorConfig {
  const type = schema.type;

  if (type === 'boolean') {
    return EDITOR_REGISTRY['boolean'];
  }

  if (type === 'number' || type === 'integer') {
    return EDITOR_REGISTRY['number'];
  }

  if (type === 'string' && schema.enum) {
    // For string enums, use select editor with dropdown + typeahead
    return EDITOR_REGISTRY['select'];
  }

  if (type === 'string') {
    return EDITOR_REGISTRY['string'];
  }

  // Default to JSON editor for object, array, and unknown types
  return EDITOR_REGISTRY['json'];
}

/**
 * Get the appropriate editor for a given field schema
 * Used for Step Properties where plugins can specify custom editors
 *
 * Priority:
 * 1. x-editor field (explicit editor from plugin)
 * 2. type field inference (boolean -> checkbox, number -> spinner)
 * 3. Default to JSON editor for unknown/complex types
 */
export function getEditorForSchema(schema: Record<string, any>): EditorConfig {
  // 1. Check for explicit x-editor declaration
  const explicitEditor = schema['x-editor'];
  if (explicitEditor && EDITOR_REGISTRY[explicitEditor]) {
    return EDITOR_REGISTRY[explicitEditor];
  }

  // 2. Fall back to type-based inference
  return getEditorForType(schema);
}

/**
 * Get editor by name (for direct lookup)
 */
export function getEditorByName(name: string): EditorConfig | undefined {
  return EDITOR_REGISTRY[name];
}

/**
 * Check if an editor exists
 */
export function hasEditor(name: string): boolean {
  return name in EDITOR_REGISTRY;
}
