import { GraphDefinition } from './graph';

// Message in a conversation
export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant' | 'error' | 'system';
  content: string;
  timestamp: Date;
  runId?: string;  // Associated run ID for assistant/error messages
}

// A conversation with a graph
export interface Conversation {
  id: string;                // Also used as session_id for runtime
  graphId: string;           // Agent ID in runtime
  title: string;             // First message preview or "New conversation"
  createdAt: Date;
  updatedAt: Date;
  debugMode: boolean;        // Per-conversation debug toggle
  messages: Message[];
  activeRunId?: string;      // Currently executing run (null when idle)
}

// A graph that's been added to the chat UI
export interface ActiveGraph {
  agentId: string;
  name: string;
  description?: string;
  graphDefinition: GraphDefinition;
}

// Utility function to check if a graph is eligible for chat
export function isGraphChatEligible(graphDefinition: GraphDefinition): boolean {
  const { memory } = graphDefinition;
  const hasQueryInput = 'query' in (memory?.inputs || {});
  const hasQueryResponseOutput = 'query_response' in (memory?.outputs || {});
  return hasQueryInput && hasQueryResponseOutput;
}

// Generate a unique ID
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

// Create a title from the first message content
export function createConversationTitle(content: string): string {
  const maxLength = 50;
  if (content.length <= maxLength) {
    return content;
  }
  return content.substring(0, maxLength - 3) + '...';
}
