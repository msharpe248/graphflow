import { Bug, ExternalLink } from 'lucide-react';
import { ActiveGraph, Conversation } from '@/types/chat';
import { useChatStore } from '@/stores/chatStore';
import clsx from 'clsx';

interface ChatHeaderProps {
  graph: ActiveGraph;
  conversation: Conversation | null;
}

export default function ChatHeader({ graph, conversation }: ChatHeaderProps) {
  const { setDebugMode } = useChatStore();

  const handleDebugToggle = () => {
    if (conversation) {
      setDebugMode(conversation.id, !conversation.debugMode);
    }
  };

  const openInRuntime = () => {
    // Open the runtime UI with the agent context
    window.open(`http://localhost:3000?view=runtime&agentId=${graph.agentId}`, '_blank');
  };

  return (
    <div className="h-14 px-4 border-b border-border flex items-center justify-between bg-background">
      {/* Graph info */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="min-w-0">
          <h2 className="font-medium truncate">{graph.name}</h2>
          {graph.description && (
            <p className="text-xs text-muted-foreground truncate">{graph.description}</p>
          )}
        </div>
      </div>

      {/* Actions */}
      {conversation && (
        <div className="flex items-center gap-2">
          {/* Debug mode toggle */}
          <button
            onClick={handleDebugToggle}
            className={clsx(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors",
              conversation.debugMode
                ? "bg-orange-100 text-orange-700 hover:bg-orange-200"
                : "hover:bg-muted text-muted-foreground"
            )}
            title={conversation.debugMode ? "Debug mode enabled" : "Enable debug mode"}
          >
            <Bug className="w-4 h-4" />
            <span>Debug</span>
          </button>

          {/* Open in Runtime */}
          {conversation.debugMode && (
            <button
              onClick={openInRuntime}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm hover:bg-muted text-muted-foreground transition-colors"
              title="Open in Runtime UI"
            >
              <ExternalLink className="w-4 h-4" />
              <span>Runtime</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}
