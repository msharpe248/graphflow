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
  type: 'rectangle' | 'ellipse';
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
}

export interface SecretDefinition {
  source: string;
  key: string;
  description?: string;
}

export interface MemorySchema {
  inputs: Record<string, FieldDefinition>;
  outputs: Record<string, FieldDefinition>;
  intermediate: Record<string, FieldDefinition>;
  secrets?: Record<string, SecretDefinition>;
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
  icon?: string;
  color?: string;
  configSchema?: Record<string, any>;
  inputsSchema?: Record<string, any>;
  outputsSchema?: Record<string, any>;
  uiComponent?: string;
}

// ReactFlow node types
export interface NodeData {
  step: Step;
  stepTypeInfo: StepTypeInfo;
}
