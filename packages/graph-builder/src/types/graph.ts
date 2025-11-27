// TypeScript types matching GraphFlow graph definition

export interface FieldDefinition {
  type: string;
  description?: string;
  default?: any;
  required?: boolean;
  items?: FieldDefinition;
  properties?: Record<string, FieldDefinition>;
}

export interface Shape {
  id: string;
  type: 'rectangle' | 'ellipse' | 'textbox' | 'stickynote';
  position: { x: number; y: number };
  size: { width: number; height: number };
  title?: string;
  text?: string;
  color: string;
  borderColor?: string;
  opacity: number;
  zIndex?: number;
  textAlign?: 'left' | 'center' | 'right';
  textVerticalAlign?: 'top' | 'center' | 'bottom';
  titleFontSize?: number;
  textFontSize?: number;
  textColor?: string;
  fontWeight?: 'normal' | 'medium' | 'semibold' | 'bold';
  shadow?: boolean;
  padding?: number;
}

export interface SecretDefinition {
  provider: string; // 'env', 'vault', 'aws_secrets'
  key: string;
  description?: string;
}

export interface ConfigDefinition {
  type: string; // 'string', 'number', 'boolean'
  description?: string;
}

export interface EnvironmentDefinition {
  type: string; // 'string', 'number', 'boolean'
  key: string; // Environment variable name
  description?: string;
  required?: boolean;
}

export interface MemorySchema {
  inputs: Record<string, FieldDefinition>;
  outputs: Record<string, FieldDefinition>;
  intermediate: Record<string, FieldDefinition>;
  secrets?: Record<string, SecretDefinition>;
  config?: Record<string, ConfigDefinition>;
  environment?: Record<string, EnvironmentDefinition>;
}

export interface Metadata {
  name: string;
  description: string;
  version?: string;
  revision?: number;
  tags?: string[];
  author?: string;
  linkedAgentId?: string;
}

export interface Step {
  id: string;
  type: string;
  config: Record<string, any>;
  outputs?: Record<string, string>;
  description?: string;
  position?: { x: number; y: number };
}

export interface Edge {
  id: string;
  from: string;
  to: string;
  condition?: string;
}

export interface GraphDefinition {
  version: string;
  metadata: Metadata;
  memory: MemorySchema;
  steps: Step[];
  edges: Edge[];
  shapes?: Shape[];
}

// Step type categories
export type StepCategory =
  | 'control'
  | 'ai'
  | 'data'
  | 'transform'
  | 'general';

export interface StepTypeInfo {
  type: string;
  category: StepCategory;
  label: string;
  description: string;
  plugin?: string;
  plugin_version?: string;
  icon?: string;
  color?: string;
  configSchema?: Record<string, any>;
  inputsSchema?: Record<string, any>;
  outputsSchema?: Record<string, any>;
  uiComponent?: string;
  /** Whether this step type can be used as a tool by LLM steps */
  can_be_tool?: boolean;
}

// ReactFlow node types
export interface NodeData {
  step: Step;
  stepTypeInfo: StepTypeInfo;
}
