import { useState, useCallback } from 'react';
import { useChatStore } from '@/stores/chatStore';
import * as runtime from '@/services/runtime';

// Polling interval in milliseconds
const POLL_INTERVAL = 1000;

// Maximum polling attempts (5 minutes at 1s intervals)
const MAX_POLL_ATTEMPTS = 300;

export function useChat() {
  const [isSending, setIsSending] = useState(false);
  const { addMessage, setActiveRunId, getConversation } = useChatStore();

  const sendMessage = useCallback(async (
    conversationId: string,
    agentId: string,
    query: string,
    debugMode: boolean
  ) => {
    setIsSending(true);

    try {
      // 1. Add user message immediately
      addMessage(conversationId, {
        conversationId,
        role: 'user',
        content: query,
      });

      // 2. Start the run
      const run = await runtime.createRun(agentId, {
        inputs: { query },
        session_id: conversationId,
        debug_mode: debugMode,
      });

      // 3. Set active run ID
      setActiveRunId(conversationId, run.id);

      // 4. Poll for completion
      let attempts = 0;
      let currentRun = run;

      while (attempts < MAX_POLL_ATTEMPTS) {
        // Check if conversation still exists (might be deleted)
        const conversation = getConversation(conversationId);
        if (!conversation) {
          break;
        }

        // Check if the active run ID changed (user stopped or started new run)
        if (conversation.activeRunId !== run.id) {
          break;
        }

        // Get updated run status
        currentRun = await runtime.getRun(agentId, run.id);

        if (currentRun.status === 'completed') {
          // Extract the response
          const response = currentRun.outputs?.query_response;

          addMessage(conversationId, {
            conversationId,
            role: 'assistant',
            content: response || 'No response received.',
            runId: run.id,
          });

          setActiveRunId(conversationId, null);
          break;
        }

        if (currentRun.status === 'failed') {
          addMessage(conversationId, {
            conversationId,
            role: 'error',
            content: currentRun.error || 'An error occurred while processing your request.',
            runId: run.id,
          });

          setActiveRunId(conversationId, null);
          break;
        }

        if (currentRun.status === 'stopped') {
          addMessage(conversationId, {
            conversationId,
            role: 'system',
            content: 'Run was stopped.',
            runId: run.id,
          });

          setActiveRunId(conversationId, null);
          break;
        }

        // Continue polling for pending/running status
        await sleep(POLL_INTERVAL);
        attempts++;
      }

      // Handle timeout
      if (attempts >= MAX_POLL_ATTEMPTS) {
        addMessage(conversationId, {
          conversationId,
          role: 'error',
          content: 'Request timed out. The graph is taking too long to respond.',
          runId: run.id,
        });

        setActiveRunId(conversationId, null);
      }
    } catch (error) {
      // Handle network or API errors
      const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred.';

      addMessage(conversationId, {
        conversationId,
        role: 'error',
        content: errorMessage,
      });

      setActiveRunId(conversationId, null);
    } finally {
      setIsSending(false);
    }
  }, [addMessage, setActiveRunId, getConversation]);

  const stopRun = useCallback(async (agentId: string, runId: string) => {
    try {
      await runtime.stopRun(agentId, runId);
    } catch (error) {
      console.error('Failed to stop run:', error);
    }
  }, []);

  return {
    sendMessage,
    stopRun,
    isSending,
  };
}

// Helper function for polling delay
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
