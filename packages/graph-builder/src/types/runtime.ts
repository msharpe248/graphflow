// Types for runtime API

export interface Agent {
  id: string;
  name: string;
  description?: string;
  framework: 'pydantic_ai' | 'langgraph';
  graph_definition: any;
  created_at: string;
  updated_at: string;
}

export interface AgentRun {
  id: string;
  agent_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped';
  inputs: Record<string, any>;
  outputs?: Record<string, any>;
  error?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface MemoryState {
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  intermediate: Record<string, any>;
}

export interface CreateAgentRequest {
  name: string;
  description?: string;
  framework: 'pydantic_ai' | 'langgraph';
  graph_definition: any;
}

export interface CreateRunRequest {
  inputs: Record<string, any>;
}

export interface HealthCheck {
  status: string;
  active_runs: number;
}
