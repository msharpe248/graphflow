import { Agent, AgentRun, CreateAgentRequest, CreateRunRequest, MemoryState, HealthCheck } from '@/types/runtime';

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
