import { useChatStore } from '@/stores/chatStore';
import ChatHeader from './ChatHeader';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import { MessageSquare } from 'lucide-react';

export default function ChatContainer() {
  const { selectedConversationId, selectedGraphId, getSelectedGraph, getSelectedConversation } = useChatStore();

  const selectedGraph = getSelectedGraph();
  const selectedConversation = getSelectedConversation();

  // No graph selected
  if (!selectedGraphId) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        <div className="text-center">
          <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <h2 className="text-lg font-medium mb-2">Welcome to GraphFlow Chat</h2>
          <p className="text-sm">
            Add a graph from the sidebar to start chatting.
          </p>
        </div>
      </div>
    );
  }

  // Graph selected but no conversation
  if (!selectedConversationId || !selectedConversation) {
    return (
      <div className="flex-1 flex flex-col">
        <ChatHeader graph={selectedGraph!} conversation={null} />
        <div className="flex-1 flex items-center justify-center text-muted-foreground">
          <div className="text-center">
            <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <h2 className="text-lg font-medium mb-2">No conversation selected</h2>
            <p className="text-sm">
              Create a new conversation from the sidebar to start chatting.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Full chat view
  return (
    <div className="flex-1 flex flex-col h-full">
      <ChatHeader graph={selectedGraph!} conversation={selectedConversation} />
      <MessageList conversation={selectedConversation} />
      <ChatInput conversation={selectedConversation} graph={selectedGraph!} />
    </div>
  );
}
