import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as runtime from '@/services/runtime';
import { CreateAgentRequest, CreateRunRequest } from '@/types/runtime';

// Query keys
const keys = {
  health: ['health'],
  agents: ['agents'],
  agent: (id: string) => ['agents', id],
  runs: (agentId: string) => ['agents', agentId, 'runs'],
  run: (agentId: string, runId: string) => ['agents', agentId, 'runs', runId],
  memory: (agentId: string, runId: string) => ['agents', agentId, 'runs', runId, 'memory'],
  debugState: (agentId: string, runId: string) => ['agents', agentId, 'runs', runId, 'debug'],
};

// Health
export const useHealth = () =>
  useQuery({
    queryKey: keys.health,
    queryFn: runtime.getHealth,
    refetchInterval: 5000, // Poll every 5 seconds
  });

// Agents
export const useAgents = () =>
  useQuery({
    queryKey: keys.agents,
    queryFn: runtime.getAgents,
  });

export const useAgent = (agentId: string | null) =>
  useQuery({
    queryKey: keys.agent(agentId!),
    queryFn: () => runtime.getAgent(agentId!),
    enabled: !!agentId,
  });

export const useCreateAgent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateAgentRequest) => runtime.createAgent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: keys.agents });
    },
  });
};

export const useDeleteAgent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (agentId: string) => runtime.deleteAgent(agentId),
    onSuccess: (_, agentId) => {
      // Invalidate the agents list
      queryClient.invalidateQueries({ queryKey: keys.agents });
      // Remove all cached data for this specific agent
      queryClient.removeQueries({ queryKey: keys.agent(agentId) });
      queryClient.removeQueries({ queryKey: keys.runs(agentId) });
    },
  });
};

// Runs
export const useRuns = (agentId: string | null) =>
  useQuery({
    queryKey: keys.runs(agentId!),
    queryFn: () => runtime.getRuns(agentId!),
    enabled: !!agentId,
    refetchInterval: 2000, // Poll every 2 seconds for active runs
  });

export const useRun = (agentId: string | null, runId: string | null) =>
  useQuery({
    queryKey: keys.run(agentId!, runId!),
    queryFn: () => runtime.getRun(agentId!, runId!),
    enabled: !!agentId && !!runId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Poll active runs every second, completed runs don't need polling
      if (data?.status === 'running' || data?.status === 'pending') {
        return 1000;
      }
      return false;
    },
  });

export const useCreateRun = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, data }: { agentId: string; data: CreateRunRequest }) =>
      runtime.createRun(agentId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: keys.runs(variables.agentId) });
    },
  });
};

export const useStopRun = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, runId }: { agentId: string; runId: string }) =>
      runtime.stopRun(agentId, runId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: keys.run(variables.agentId, variables.runId) });
      queryClient.invalidateQueries({ queryKey: keys.runs(variables.agentId) });
    },
  });
};

export const useDeleteRun = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, runId }: { agentId: string; runId: string }) =>
      runtime.deleteRun(agentId, runId),
    onSuccess: (_, variables) => {
      // Invalidate the runs list
      queryClient.invalidateQueries({ queryKey: keys.runs(variables.agentId) });
      // Remove the specific run from cache
      queryClient.removeQueries({ queryKey: keys.run(variables.agentId, variables.runId) });
      // Remove the run's memory from cache
      queryClient.removeQueries({ queryKey: keys.memory(variables.agentId, variables.runId) });
    },
  });
};

// Memory
export const useMemory = (agentId: string | null, runId: string | null) =>
  useQuery({
    queryKey: keys.memory(agentId!, runId!),
    queryFn: () => runtime.getMemory(agentId!, runId!),
    enabled: !!agentId && !!runId,
    refetchInterval: 1000, // Poll memory every second
  });

// Debug Control
export const useDebugState = (agentId: string | null, runId: string | null, isActive: boolean = true) =>
  useQuery({
    queryKey: keys.debugState(agentId!, runId!),
    queryFn: () => runtime.getDebugState(agentId!, runId!),
    enabled: !!agentId && !!runId && isActive,
    refetchInterval: isActive ? 500 : false, // Poll only when active
    retry: 1, // Reduce retries to prevent hanging
  });

export const usePauseRun = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, runId }: { agentId: string; runId: string }) =>
      runtime.pauseRun(agentId, runId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: keys.run(variables.agentId, variables.runId) });
      queryClient.invalidateQueries({ queryKey: keys.debugState(variables.agentId, variables.runId) });
    },
  });
};

export const useResumeRun = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, runId }: { agentId: string; runId: string }) =>
      runtime.resumeRun(agentId, runId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: keys.run(variables.agentId, variables.runId) });
      queryClient.invalidateQueries({ queryKey: keys.debugState(variables.agentId, variables.runId) });
    },
  });
};

export const useStepRun = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, runId }: { agentId: string; runId: string }) =>
      runtime.stepRun(agentId, runId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: keys.run(variables.agentId, variables.runId) });
      queryClient.invalidateQueries({ queryKey: keys.debugState(variables.agentId, variables.runId) });
    },
  });
};

export const useSetBreakpoint = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, runId, stepId }: { agentId: string; runId: string; stepId: string }) =>
      runtime.setBreakpoint(agentId, runId, stepId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: keys.run(variables.agentId, variables.runId) });
      queryClient.invalidateQueries({ queryKey: keys.debugState(variables.agentId, variables.runId) });
    },
  });
};

export const useClearBreakpoint = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, runId, stepId }: { agentId: string; runId: string; stepId: string }) =>
      runtime.clearBreakpoint(agentId, runId, stepId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: keys.run(variables.agentId, variables.runId) });
      queryClient.invalidateQueries({ queryKey: keys.debugState(variables.agentId, variables.runId) });
    },
  });
};

export const useUpdateMemory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      agentId,
      runId,
      namespace,
      key,
      value,
    }: {
      agentId: string;
      runId: string;
      namespace: string;
      key: string;
      value: any;
    }) => runtime.updateMemory(agentId, runId, namespace, key, value),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: keys.memory(variables.agentId, variables.runId) });
    },
  });
};
