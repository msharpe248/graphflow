import { Agent, AgentRun, CreateAgentRequest, CreateRunRequest, MemoryState, HealthCheck, DebugState } from '@/types/runtime';

const API_BASE = '/api/v1';

// Helper for API calls
async function apiCall<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error: ${response.status} - ${error}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Health
export const getHealth = (): Promise<HealthCheck> =>
  apiCall('/health');

// Agents
export const getAgents = (): Promise<Agent[]> =>
  apiCall('/agents');

export const getAgent = (agentId: string): Promise<Agent> =>
  apiCall(`/agents/${agentId}`);

export const createAgent = (data: CreateAgentRequest): Promise<Agent> =>
  apiCall('/agents', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const deleteAgent = (agentId: string): Promise<void> =>
  apiCall(`/agents/${agentId}`, { method: 'DELETE' });

// Runs
export const getRuns = (agentId: string): Promise<AgentRun[]> =>
  apiCall(`/agents/${agentId}/runs`);

export const getRun = (agentId: string, runId: string): Promise<AgentRun> =>
  apiCall(`/agents/${agentId}/runs/${runId}`);

export const createRun = (agentId: string, data: CreateRunRequest): Promise<AgentRun> =>
  apiCall(`/agents/${agentId}/runs`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const stopRun = (agentId: string, runId: string): Promise<AgentRun> =>
  apiCall(`/agents/${agentId}/runs/${runId}/stop`, {
    method: 'POST',
  });

export const deleteRun = (agentId: string, runId: string): Promise<void> =>
  apiCall(`/agents/${agentId}/runs/${runId}`, { method: 'DELETE' });

// Memory
export const getMemory = (agentId: string, runId: string): Promise<MemoryState> =>
  apiCall(`/agents/${agentId}/runs/${runId}/memory`);

export const getMemoryKey = (agentId: string, runId: string, key: string): Promise<any> =>
  apiCall(`/agents/${agentId}/runs/${runId}/memory/${key}`);

// Debug Control
export const pauseRun = (agentId: string, runId: string): Promise<void> =>
  apiCall(`/agents/${agentId}/runs/${runId}/debug/pause`, {
    method: 'POST',
  });

export const resumeRun = (agentId: string, runId: string): Promise<void> =>
  apiCall(`/agents/${agentId}/runs/${runId}/debug/resume`, {
    method: 'POST',
  });

export const stepRun = (agentId: string, runId: string): Promise<void> =>
  apiCall(`/agents/${agentId}/runs/${runId}/debug/step`, {
    method: 'POST',
  });

export const setBreakpoint = (agentId: string, runId: string, stepId: string): Promise<void> =>
  apiCall(`/agents/${agentId}/runs/${runId}/debug/breakpoints`, {
    method: 'POST',
    body: JSON.stringify({ step_id: stepId }),
  });

export const clearBreakpoint = (agentId: string, runId: string, stepId: string): Promise<void> =>
  apiCall(`/agents/${agentId}/runs/${runId}/debug/breakpoints/${stepId}`, {
    method: 'DELETE',
  });

export const updateMemory = (
  agentId: string,
  runId: string,
  namespace: string,
  key: string,
  value: any
): Promise<void> =>
  apiCall(`/agents/${agentId}/runs/${runId}/debug/memory`, {
    method: 'PUT',
    body: JSON.stringify({ namespace, key, value }),
  });

export const getDebugState = (agentId: string, runId: string): Promise<DebugState> =>
  apiCall(`/agents/${agentId}/runs/${runId}/debug/state`);

// Session History
export interface SessionHistory {
  session_id: string;
  history: Record<string, any[]>;  // step_id -> list of messages
}

export const getSessionHistory = (sessionId: string): Promise<SessionHistory> =>
  apiCall(`/sessions/${sessionId}/history`);
