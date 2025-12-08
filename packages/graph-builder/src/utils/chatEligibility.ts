import { GraphDefinition } from '@/types/graph';
import { MemorySchema } from '@/types/graph';

/**
 * Check if a graph is eligible for chat mode.
 * A graph is eligible if it has a 'query' input and 'query_response' output.
 */
export function isGraphChatEligible(graphDefinition: GraphDefinition): boolean {
  const { memory } = graphDefinition;
  return isMemoryChatEligible(memory);
}

/**
 * Check if a memory schema is eligible for chat mode.
 */
export function isMemoryChatEligible(memory: MemorySchema): boolean {
  const hasQueryInput = 'query' in (memory?.inputs || {});
  const hasQueryResponseOutput = 'query_response' in (memory?.outputs || {});
  return hasQueryInput && hasQueryResponseOutput;
}

/**
 * Get the chat URL for an agent
 */
export function getChatUrl(agentId: string): string {
  return `http://localhost:3001?agentId=${agentId}`;
}

/**
 * Open the chat UI with a specific agent
 */
export function openChatWithAgent(agentId: string): void {
  window.open(getChatUrl(agentId), '_blank');
}
