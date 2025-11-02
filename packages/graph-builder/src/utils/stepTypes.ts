import { StepTypeInfo } from '@/types/graph';

// All available step types with their metadata
export const STEP_TYPES: Record<string, StepTypeInfo> = {
  start: {
    type: 'start',
    category: 'control',
    label: 'Start',
    description: 'Entry point for the graph',
    color: '#10b981', // green
    icon: 'Play',
    configSchema: {},
  },
  output: {
    type: 'output',
    category: 'control',
    label: 'Output',
    description: 'Map intermediate values to outputs',
    color: '#ef4444', // red
    icon: 'CheckCircle',
    configSchema: {
      mappings: {
        type: 'object',
        description: 'Map intermediate keys to output keys',
      },
    },
  },
  llm: {
    type: 'llm',
    category: 'ai',
    label: 'LLM',
    description: 'Call LLM with optional tools and structured output',
    color: '#8b5cf6', // purple
    icon: 'Sparkles',
    configSchema: {
      provider: {
        type: 'string',
        enum: ['openrouter', 'openai', 'anthropic', 'ollama'],
        default: 'openrouter',
      },
      model: {
        type: 'string',
        description: 'Model name',
      },
      system_prompt: {
        type: 'string',
        description: 'System prompt',
      },
      user_prompt: {
        type: 'string',
        description: 'User prompt template',
      },
      temperature: {
        type: 'number',
        default: 0.7,
      },
      tools: {
        type: 'array',
        description: 'Available tools',
      },
      output_schema: {
        type: 'object',
        description: 'Structured output schema',
      },
    },
  },
  http: {
    type: 'http',
    category: 'data',
    label: 'HTTP',
    description: 'Make HTTP request',
    color: '#3b82f6', // blue
    icon: 'Globe',
    configSchema: {
      method: {
        type: 'string',
        enum: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
        default: 'GET',
      },
      url: {
        type: 'string',
        description: 'URL template',
      },
      headers: {
        type: 'object',
        description: 'Request headers',
      },
      body: {
        type: 'object',
        description: 'Request body',
      },
    },
  },
  transform: {
    type: 'transform',
    category: 'transform',
    label: 'Transform',
    description: 'Execute Python code for data transformation',
    color: '#f59e0b', // amber
    icon: 'Code',
    configSchema: {
      code: {
        type: 'string',
        description: 'Python code to execute',
      },
    },
  },
  conditional: {
    type: 'conditional',
    category: 'control',
    label: 'Conditional',
    description: 'Branch based on condition',
    color: '#06b6d4', // cyan
    icon: 'GitBranch',
    configSchema: {
      condition: {
        type: 'string',
        description: 'Python expression that evaluates to boolean',
      },
    },
  },
  join: {
    type: 'join',
    category: 'control',
    label: 'Join',
    description: 'Wait for multiple branches to complete',
    color: '#14b8a6', // teal
    icon: 'GitMerge',
    configSchema: {
      wait_for_all: {
        type: 'boolean',
        default: true,
        description: 'Wait for all incoming edges',
      },
    },
  },
  loop: {
    type: 'loop',
    category: 'control',
    label: 'Loop',
    description: 'Iterate over a collection',
    color: '#ec4899', // pink
    icon: 'RefreshCw',
    configSchema: {
      collection_key: {
        type: 'string',
        description: 'Memory key containing the collection',
      },
      item_key: {
        type: 'string',
        description: 'Key to store current item',
      },
      max_iterations: {
        type: 'number',
        default: 100,
        description: 'Maximum iterations',
      },
    },
  },
  db_query: {
    type: 'db_query',
    category: 'data',
    label: 'DB Query',
    description: 'Execute database query',
    color: '#6366f1', // indigo
    icon: 'Database',
    configSchema: {
      connection_string: {
        type: 'string',
        description: 'Database connection string',
      },
      query: {
        type: 'string',
        description: 'SQL query template',
      },
      parameters: {
        type: 'object',
        description: 'Query parameters',
      },
    },
  },
  human_input: {
    type: 'human_input',
    category: 'ai',
    label: 'Human Input',
    description: 'Wait for human input',
    color: '#f97316', // orange
    icon: 'User',
    configSchema: {
      prompt: {
        type: 'string',
        description: 'Prompt to show to human',
      },
      input_schema: {
        type: 'object',
        description: 'Expected input schema',
      },
      timeout_seconds: {
        type: 'number',
        description: 'Timeout in seconds',
      },
    },
  },
};

// Get step types grouped by category
export function getStepTypesByCategory() {
  const grouped: Record<string, StepTypeInfo[]> = {
    control: [],
    ai: [],
    data: [],
    transform: [],
    general: [],
  };

  Object.values(STEP_TYPES).forEach((stepType) => {
    grouped[stepType.category].push(stepType);
  });

  return grouped;
}
