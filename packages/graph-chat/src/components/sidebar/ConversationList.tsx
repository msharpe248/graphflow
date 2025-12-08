import { MessageSquare, Trash2, Bug } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import clsx from 'clsx';

export default function ConversationList() {
  const {
    selectedGraphId,
    selectedConversationId,
    selectConversation,
    deleteConversation,
    getConversationsForGraph,
  } = useChatStore();

  if (!selectedGraphId) {
    return null;
  }

  const conversations = getConversationsForGraph(selectedGraphId);

  if (conversations.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground text-sm">
        No conversations yet.
        <br />
        Start a new conversation above.
      </div>
    );
  }

  return (
    <div className="py-2">
      {conversations.map((conversation) => {
        const isSelected = conversation.id === selectedConversationId;
        const isActive = !!conversation.activeRunId;
        const lastMessage = conversation.messages[conversation.messages.length - 1];

        return (
          <div
            key={conversation.id}
            className={clsx(
              "group px-3 py-2 mx-2 rounded-md cursor-pointer transition-colors",
              isSelected ? "bg-muted" : "hover:bg-muted/50"
            )}
          >
            <button
              onClick={() => selectConversation(conversation.id)}
              className="w-full text-left"
            >
              <div className="flex items-start gap-2">
                <MessageSquare className={clsx(
                  "w-4 h-4 mt-0.5 flex-shrink-0",
                  isActive ? "text-blue-500 animate-pulse" : "text-muted-foreground"
                )} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-medium text-sm">
                      {conversation.title}
                    </span>
                    {conversation.debugMode && (
                      <span title="Debug mode enabled">
                        <Bug className="w-3 h-3 text-orange-500 flex-shrink-0" />
                      </span>
                    )}
                  </div>
                  {lastMessage && (
                    <div className="truncate text-xs text-muted-foreground mt-0.5">
                      {lastMessage.role === 'user' ? 'You: ' : ''}
                      {lastMessage.content.substring(0, 50)}
                    </div>
                  )}
                  <div className="text-xs text-muted-foreground mt-1">
                    {formatRelativeTime(conversation.updatedAt)}
                  </div>
                </div>
              </div>
            </button>

            {/* Delete button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteConversation(conversation.id);
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-background opacity-0 group-hover:opacity-100 transition-opacity"
              title="Delete conversation"
            >
              <Trash2 className="w-3 h-3 text-muted-foreground hover:text-red-500" />
            </button>
          </div>
        );
      })}
    </div>
  );
}

function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}
