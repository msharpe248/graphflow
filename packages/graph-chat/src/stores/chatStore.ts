import { create } from 'zustand';
import {
  Message,
  Conversation,
  ActiveGraph,
  generateId,
  createConversationTitle
} from '@/types/chat';

interface ChatStore {
  // State
  activeGraphs: ActiveGraph[];
  conversations: Conversation[];
  selectedGraphId: string | null;
  selectedConversationId: string | null;

  // Graph actions
  addGraph: (graph: ActiveGraph) => void;
  removeGraph: (agentId: string) => void;
  selectGraph: (agentId: string | null) => void;
  getGraph: (agentId: string) => ActiveGraph | undefined;

  // Conversation actions
  createConversation: (graphId: string, debugMode?: boolean) => string;
  selectConversation: (conversationId: string | null) => void;
  deleteConversation: (conversationId: string) => void;
  setDebugMode: (conversationId: string, enabled: boolean) => void;
  getConversation: (conversationId: string) => Conversation | undefined;
  getConversationsForGraph: (graphId: string) => Conversation[];

  // Message actions
  addMessage: (conversationId: string, message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (messageId: string, updates: Partial<Message>) => void;
  setActiveRunId: (conversationId: string, runId: string | null) => void;

  // Derived state helpers
  getSelectedGraph: () => ActiveGraph | undefined;
  getSelectedConversation: () => Conversation | undefined;
}

export const useChatStore = create<ChatStore>()((set, get) => ({
  // Initial state
  activeGraphs: [],
  conversations: [],
  selectedGraphId: null,
  selectedConversationId: null,

  // Graph actions
  addGraph: (graph) => {
    set((state) => {
      // Don't add duplicates
      if (state.activeGraphs.some((g) => g.agentId === graph.agentId)) {
        return state;
      }
      return {
        activeGraphs: [...state.activeGraphs, graph],
        // Auto-select the first graph
        selectedGraphId: state.selectedGraphId || graph.agentId,
      };
    });
  },

  removeGraph: (agentId) => {
    set((state) => {
      const newGraphs = state.activeGraphs.filter((g) => g.agentId !== agentId);
      // Remove all conversations for this graph
      const newConversations = state.conversations.filter((c) => c.graphId !== agentId);

      // Update selection if needed
      let newSelectedGraphId = state.selectedGraphId;
      let newSelectedConversationId = state.selectedConversationId;

      if (state.selectedGraphId === agentId) {
        newSelectedGraphId = newGraphs.length > 0 ? newGraphs[0].agentId : null;
        newSelectedConversationId = null;
      }

      // Check if selected conversation was removed
      if (newSelectedConversationId && !newConversations.some((c) => c.id === newSelectedConversationId)) {
        newSelectedConversationId = null;
      }

      return {
        activeGraphs: newGraphs,
        conversations: newConversations,
        selectedGraphId: newSelectedGraphId,
        selectedConversationId: newSelectedConversationId,
      };
    });
  },

  selectGraph: (agentId) => {
    set((state) => {
      // When selecting a new graph, clear conversation selection
      // unless there's a conversation for this graph
      let newConversationId = null;
      if (agentId) {
        const graphConversations = state.conversations.filter((c) => c.graphId === agentId);
        if (graphConversations.length > 0) {
          // Select the most recent conversation
          newConversationId = graphConversations.sort(
            (a, b) => b.updatedAt.getTime() - a.updatedAt.getTime()
          )[0].id;
        }
      }

      return {
        selectedGraphId: agentId,
        selectedConversationId: newConversationId,
      };
    });
  },

  getGraph: (agentId) => {
    return get().activeGraphs.find((g) => g.agentId === agentId);
  },

  // Conversation actions
  createConversation: (graphId, debugMode = false) => {
    const id = generateId();
    const now = new Date();

    const newConversation: Conversation = {
      id,
      graphId,
      title: 'New conversation',
      createdAt: now,
      updatedAt: now,
      debugMode,
      messages: [],
      activeRunId: undefined,
    };

    set((state) => ({
      conversations: [...state.conversations, newConversation],
      selectedConversationId: id,
    }));

    return id;
  },

  selectConversation: (conversationId) => {
    set((state) => {
      // Also select the graph if not already selected
      const conversation = state.conversations.find((c) => c.id === conversationId);
      const newGraphId = conversation ? conversation.graphId : state.selectedGraphId;

      return {
        selectedConversationId: conversationId,
        selectedGraphId: newGraphId,
      };
    });
  },

  deleteConversation: (conversationId) => {
    set((state) => {
      const newConversations = state.conversations.filter((c) => c.id !== conversationId);

      // Update selection if the deleted conversation was selected
      let newSelectedConversationId = state.selectedConversationId;
      if (state.selectedConversationId === conversationId) {
        // Find another conversation for the same graph
        const deletedConv = state.conversations.find((c) => c.id === conversationId);
        if (deletedConv) {
          const sameGraphConvs = newConversations.filter((c) => c.graphId === deletedConv.graphId);
          newSelectedConversationId = sameGraphConvs.length > 0 ? sameGraphConvs[0].id : null;
        } else {
          newSelectedConversationId = null;
        }
      }

      return {
        conversations: newConversations,
        selectedConversationId: newSelectedConversationId,
      };
    });
  },

  setDebugMode: (conversationId, enabled) => {
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === conversationId ? { ...c, debugMode: enabled } : c
      ),
    }));
  },

  getConversation: (conversationId) => {
    return get().conversations.find((c) => c.id === conversationId);
  },

  getConversationsForGraph: (graphId) => {
    return get().conversations
      .filter((c) => c.graphId === graphId)
      .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
  },

  // Message actions
  addMessage: (conversationId, message) => {
    const id = generateId();
    const now = new Date();

    const newMessage: Message = {
      ...message,
      id,
      timestamp: now,
    };

    set((state) => ({
      conversations: state.conversations.map((c) => {
        if (c.id !== conversationId) return c;

        const updatedMessages = [...c.messages, newMessage];

        // Update title from first user message
        let title = c.title;
        if (c.messages.length === 0 && message.role === 'user') {
          title = createConversationTitle(message.content);
        }

        return {
          ...c,
          messages: updatedMessages,
          updatedAt: now,
          title,
        };
      }),
    }));
  },

  updateMessage: (messageId, updates) => {
    set((state) => ({
      conversations: state.conversations.map((c) => ({
        ...c,
        messages: c.messages.map((m) =>
          m.id === messageId ? { ...m, ...updates } : m
        ),
      })),
    }));
  },

  setActiveRunId: (conversationId, runId) => {
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === conversationId ? { ...c, activeRunId: runId ?? undefined } : c
      ),
    }));
  },

  // Derived state helpers
  getSelectedGraph: () => {
    const state = get();
    if (!state.selectedGraphId) return undefined;
    return state.activeGraphs.find((g) => g.agentId === state.selectedGraphId);
  },

  getSelectedConversation: () => {
    const state = get();
    if (!state.selectedConversationId) return undefined;
    return state.conversations.find((c) => c.id === state.selectedConversationId);
  },
}));
