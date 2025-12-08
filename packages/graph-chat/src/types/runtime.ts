// Types for runtime API

export interface Agent {
  id: string;
  name: string;
  description?: string;
  framework: 'pydantic_ai' | 'langgraph';
  graph_definition: any;  // GraphDefinition from @/types/graph
  created_at: string;
  updated_at: string;
}

export interface AgentRun {
  id: string;
  agent_id: string;
  session_id?: string;        // Session ID for conversation history
  status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped';
  inputs: Record<string, any>;
  outputs?: Record<string, any>;
  error?: string;
  execution_log?: ExecutionLogEntry[];
  started_at: string;        // Always present, set when run is created
  completed_at?: string;      // Optional, set when run finishes
  // Debug mode fields
  debug_mode?: boolean;
  current_step_id?: string;
  breakpoints?: string[];
  step_execution_counts?: Record<string, number>;
  debug_state?: 'before_start' | 'before_step' | 'after_step' | 'completed';
}

export interface ExecutionLogEntry {
  timestamp: string;
  operation: 'read' | 'write' | 'tool_call';
  key: string;
  namespace: string;
  value?: any;
  step_id?: string;
  step_label?: string;
}

export interface MemoryState {
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  intermediate: Record<string, any>;
  config?: Record<string, any>;
  environment?: Record<string, any>;
  secrets?: Record<string, any>;
  execution_log?: ExecutionLogEntry[];
  // Index signature for dynamic namespace access
  [key: string]: Record<string, any> | ExecutionLogEntry[] | undefined;
}

export interface CreateAgentRequest {
  name: string;
  description?: string;
  framework: 'pydantic_ai' | 'langgraph';
  graph_definition: any;
}

export interface CreateRunRequest {
  inputs: Record<string, any>;
  session_id?: string;        // Optional session ID (auto-generated if not provided)
  debug_mode?: boolean;
  breakpoints?: string[];
}

export interface HealthCheck {
  status: string;
  active_runs: number;
}

export interface DebugState {
  current_step_id?: string;
  breakpoints: string[];
  step_execution_counts: Record<string, number>;
  status: 'running' | 'paused' | 'completed';
}

export interface DebugEvent {
  type: 'step_started' | 'step_completed' | 'paused' | 'resumed' | 'breakpoint_added' | 'breakpoint_removed' | 'memory_updated';
  step_id?: string;
  timestamp: string;
  execution_count?: number;
  reason?: 'breakpoint' | 'step' | 'user';
  namespace?: string;
  key?: string;
  value?: any;
}
