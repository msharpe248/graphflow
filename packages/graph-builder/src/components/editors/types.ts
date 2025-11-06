// Common types for all editors

export interface EditorProps {
  value: any;
  onChange: (value: any) => void;
  schema: Record<string, any>;
  isMemoryBound?: boolean;
  onToggleBinding?: () => void;
}

export type EditorType = 'string' | 'number' | 'boolean' | 'json' | 'keyvalue' | 'color' | 'markdown';

export interface EditorConfig {
  component: React.ComponentType<EditorProps>;
  displayMode: 'inline' | 'modal';
}
