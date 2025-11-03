// TypeScript types matching GraphFlow graph definition

export interface FieldDefinition {
  type: string;
  description?: string;
  default?: any;
  required?: boolean;
  items?: FieldDefinition;
  properties?: Record<string, FieldDefinition>;
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
  tags?: string[];
  author?: string;
}

export interface Step {
  id: string;
  type: string;
  config: Record<string, any>;
  memory_reads?: string[];
  memory_writes?: string[];
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
