/**
 * TypeScript types for LLM tool definitions.
 * These types mirror the backend models in graphflow_core/models/tool.py
 */

/**
 * Visibility mode for a property mapping.
 * - 'llm': Property is exposed to the LLM as a tool parameter
 * - 'runtime': Property is hidden from LLM, provided by memory/constant
 */
export type PropertyVisibility = 'llm' | 'runtime';

/**
 * Defines how a step property is mapped when used as a tool.
 */
export interface ToolPropertyMapping {
  /** Property key from the source step's config schema */
  source_property: string;

  /** Who controls this property */
  visibility: PropertyVisibility;

  /** If visibility='runtime': constant value or memory binding like {memory.api_key} */
  runtime_value?: string;

  /** If visibility='llm': parameter name exposed to LLM (defaults to source_property) */
  llm_parameter_name?: string;

  /** If visibility='llm': description shown to LLM for this parameter */
  llm_description?: string;

  /** If visibility='llm': JSON schema for this parameter (type, enum, etc.) */
  llm_schema?: Record<string, any>;

  /** If visibility='llm': whether this parameter is required */
  required?: boolean;
}

/**
 * Defines a tool that wraps an existing step for LLM use.
 */
export interface ToolDefinition {
  /** Unique identifier for this tool */
  id: string;

  /** Tool name visible to LLM (e.g., 'search_web', 'get_user') */
  name: string;

  /** Tool description for LLM explaining when/how to use it */
  description: string;

  /** Step type to wrap (e.g., 'http.HTTPGetStep', 'db_query') */
  source_step_type: string;

  /** How each step property is handled */
  property_mappings: ToolPropertyMapping[];

  /** Which output from the step to return to LLM */
  output_key?: string;

  /** Optional Python expression to transform output */
  output_transform?: string;
}

/**
 * A tool entry that wraps a step with inline definition.
 * Stored directly in the LLM step's tools array.
 */
export interface MappedStepTool {
  type: 'mapped_step';
  definition: ToolDefinition;
}

/**
 * A tool entry that uses a direct function definition (OpenAI format).
 * Allows users to define tools manually without mapping to steps.
 */
export interface FunctionTool {
  type: 'function';
  /** OpenAI-style function definition */
  function: {
    name: string;
    description: string;
    parameters: {
      type: 'object';
      properties: Record<string, any>;
      required?: string[];
    };
  };
}

/**
 * Union type for all tool entry types in an LLM step's tools array.
 */
export type ToolEntry = MappedStepTool | FunctionTool;

/**
 * Helper to check if a tool entry is a mapped step tool.
 */
export function isMappedStepTool(entry: ToolEntry): entry is MappedStepTool {
  return entry.type === 'mapped_step';
}

/**
 * Helper to check if a tool entry is a function tool.
 */
export function isFunctionTool(entry: ToolEntry): entry is FunctionTool {
  return entry.type === 'function';
}

/**
 * Get LLM-controlled parameters from a tool definition.
 */
export function getLLMParameters(tool: ToolDefinition): ToolPropertyMapping[] {
  return tool.property_mappings.filter(m => m.visibility === 'llm');
}

/**
 * Get runtime-provided parameters from a tool definition.
 */
export function getRuntimeParameters(tool: ToolDefinition): ToolPropertyMapping[] {
  return tool.property_mappings.filter(m => m.visibility === 'runtime');
}

/**
 * Convert a tool definition to OpenAI function schema format.
 */
export function toOpenAIFunctionSchema(tool: ToolDefinition): Record<string, any> {
  const properties: Record<string, any> = {};
  const required: string[] = [];

  for (const mapping of getLLMParameters(tool)) {
    const paramName = mapping.llm_parameter_name || mapping.source_property;

    // Build parameter schema
    const paramSchema = mapping.llm_schema || { type: 'string' };
    if (mapping.llm_description) {
      paramSchema.description = mapping.llm_description;
    }

    properties[paramName] = paramSchema;

    if (mapping.required !== false) {
      required.push(paramName);
    }
  }

  return {
    type: 'function',
    function: {
      name: tool.name,
      description: tool.description,
      parameters: {
        type: 'object',
        properties,
        required,
      },
    },
  };
}

/**
 * Create a new empty tool definition with defaults.
 */
export function createEmptyToolDefinition(id?: string): ToolDefinition {
  return {
    id: id || `tool_${Date.now()}`,
    name: '',
    description: '',
    source_step_type: '',
    property_mappings: [],
    output_key: 'result',
  };
}

/**
 * Create a mapped step tool from a definition.
 */
export function createMappedStepTool(definition: ToolDefinition): MappedStepTool {
  return {
    type: 'mapped_step',
    definition,
  };
}
