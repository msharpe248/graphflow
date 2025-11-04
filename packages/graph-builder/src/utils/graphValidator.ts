import { GraphDefinition, Step, NodeData } from '@/types/graph';
import { Node } from 'reactflow';

export interface ValidationError {
  type: 'error';
  field: string;
  message: string;
  stepId?: string;
  suggestion?: string;
}

export interface ValidationWarning {
  type: 'warning';
  field: string;
  message: string;
  stepId?: string;
  suggestion?: string;
}

export type ValidationIssue = ValidationError | ValidationWarning;

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  hasIssues: boolean;
}

const MEMORY_PATTERN = /\{memory\.([^}]+)\}/g;

/**
 * Extract memory keys from a value (string, object, or array)
 */
function extractMemoryReferences(value: any): string[] {
  const refs: string[] = [];

  if (typeof value === 'string') {
    const matches = value.matchAll(MEMORY_PATTERN);
    for (const match of matches) {
      refs.push(match[1]);
    }
  } else if (typeof value === 'object' && value !== null) {
    Object.values(value).forEach(v => {
      refs.push(...extractMemoryReferences(v));
    });
  }

  return refs;
}

/**
 * Check if a value is a valid memory binding
 */
function isValidMemoryBinding(value: string): boolean {
  if (typeof value !== 'string') return false;
  return value.startsWith('{memory.') && value.endsWith('}');
}

/**
 * Validate a single step's configuration
 */
function validateStep(
  step: Step,
  stepTypeInfo: any,
  allMemoryKeys: Set<string>
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  // Check required config fields
  if (stepTypeInfo.configSchema?.properties) {
    const required = stepTypeInfo.configSchema.required || [];
    const properties = stepTypeInfo.configSchema.properties;

    for (const fieldKey of required) {
      const value = step.config[fieldKey];
      const schema = properties[fieldKey];

      if (value === undefined || value === null || value === '') {
        issues.push({
          type: 'error',
          field: `config.${fieldKey}`,
          message: `Required field "${fieldKey}" is not set`,
          stepId: step.id,
          suggestion: schema.description || `Please provide a value for ${fieldKey}`
        });
      }
    }
  }

  // Check that config memory references exist
  const configRefs = extractMemoryReferences(step.config);
  for (const ref of configRefs) {
    if (!allMemoryKeys.has(ref)) {
      issues.push({
        type: 'error',
        field: 'config',
        message: `Config references unknown memory key: {memory.${ref}}`,
        stepId: step.id,
        suggestion: `Create this memory field in the Memory panel or fix the reference`
      });
    }
  }

  // Check outputs are properly configured
  if (stepTypeInfo.outputsSchema?.properties) {
    const outputKeys = Object.keys(stepTypeInfo.outputsSchema.properties);

    for (const outputKey of outputKeys) {
      const outputValue = step.outputs?.[outputKey];

      if (!outputValue) {
        issues.push({
          type: 'error',
          field: `outputs.${outputKey}`,
          message: `Output "${outputKey}" has no memory location assigned`,
          stepId: step.id,
          suggestion: `Assign a memory location like {memory.${step.id}.${outputKey}}`
        });
      } else if (!isValidMemoryBinding(outputValue)) {
        issues.push({
          type: 'error',
          field: `outputs.${outputKey}`,
          message: `Output "${outputKey}" has invalid format: ${outputValue}`,
          stepId: step.id,
          suggestion: `Use {memory.variable} syntax`
        });
      } else {
        // Extract the memory key and check if it exists
        const match = outputValue.match(/\{memory\.([^}]+)\}/);
        if (match && !allMemoryKeys.has(match[1])) {
          issues.push({
            type: 'warning',
            field: `outputs.${outputKey}`,
            message: `Output references memory key that doesn't exist yet: ${match[1]}`,
            stepId: step.id,
            suggestion: `This will be auto-created, but you may want to define it in Memory panel`
          });
        }
      }
    }
  }

  return issues;
}

/**
 * Validate the entire graph
 */
export function validateGraph(
  graph: GraphDefinition,
  nodes: Node<NodeData>[]
): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationWarning[] = [];

  // Build set of all memory keys
  const allMemoryKeys = new Set<string>();
  Object.keys(graph.memory.inputs).forEach(k => allMemoryKeys.add(k));
  Object.keys(graph.memory.outputs).forEach(k => allMemoryKeys.add(k));
  Object.keys(graph.memory.intermediate).forEach(k => allMemoryKeys.add(k));

  // Basic graph structure validation
  if (!graph.steps || graph.steps.length === 0) {
    errors.push({
      type: 'error',
      field: 'graph',
      message: 'Graph has no steps',
      suggestion: 'Add at least one step from the Step Palette'
    });
    return {
      isValid: false,
      errors,
      warnings,
      hasIssues: true
    };
  }

  if (!graph.metadata.name || graph.metadata.name.trim() === '' || graph.metadata.name === 'Untitled Graph') {
    warnings.push({
      type: 'warning',
      field: 'metadata.name',
      message: 'Graph has no name or uses default name',
      suggestion: 'Set a descriptive name in Settings'
    });
  }

  // Validate each step
  for (const step of graph.steps) {
    const node = nodes.find(n => n.id === step.id);
    if (!node) {
      errors.push({
        type: 'error',
        field: 'steps',
        message: `Step ${step.id} has no corresponding node`,
        stepId: step.id
      });
      continue;
    }

    const stepTypeInfo = node.data.stepTypeInfo;
    const issues = validateStep(step, stepTypeInfo, allMemoryKeys);

    issues.forEach(issue => {
      if (issue.type === 'error') {
        errors.push(issue as ValidationError);
      } else {
        warnings.push(issue as ValidationWarning);
      }
    });
  }

  // Check for disconnected nodes (warning only)
  if (graph.steps.length > 1 && graph.edges.length === 0) {
    warnings.push({
      type: 'warning',
      field: 'edges',
      message: 'Graph has multiple steps but no connections',
      suggestion: 'Steps will execute in arbitrary order without edges'
    });
  }

  // Check that graph inputs are used somewhere
  const allConfigRefs = new Set<string>();
  graph.steps.forEach(step => {
    extractMemoryReferences(step.config).forEach(ref => allConfigRefs.add(ref));
  });

  Object.keys(graph.memory.inputs).forEach(inputKey => {
    if (!allConfigRefs.has(inputKey)) {
      warnings.push({
        type: 'warning',
        field: `memory.inputs.${inputKey}`,
        message: `Input "${inputKey}" is defined but not used by any step`,
        suggestion: 'Remove unused input or reference it in a step config'
      });
    }
  });

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    hasIssues: errors.length > 0 || warnings.length > 0
  };
}

/**
 * Format validation issues for display
 */
export function formatValidationIssue(issue: ValidationIssue): string {
  let message = issue.message;
  if (issue.stepId) {
    message = `[${issue.stepId}] ${message}`;
  }
  if (issue.suggestion) {
    message += `\n  → ${issue.suggestion}`;
  }
  return message;
}
