import { useState, useRef, useEffect } from 'react';
import { Send, Square } from 'lucide-react';
import { ActiveGraph, Conversation } from '@/types/chat';
import { useChat } from '@/hooks/useChat';

interface ChatInputProps {
  conversation: Conversation;
  graph: ActiveGraph;
}

export default function ChatInput({ conversation, graph }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, stopRun, isSending } = useChat();

  const isWaiting = !!conversation.activeRunId;

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  }, [message]);

  const handleSubmit = async () => {
    if (!message.trim() || isSending || isWaiting) return;

    const query = message.trim();
    setMessage('');

    await sendMessage(conversation.id, graph.agentId, query, conversation.debugMode);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleStop = () => {
    if (conversation.activeRunId) {
      stopRun(graph.agentId, conversation.activeRunId);
    }
  };

  return (
    <div className="border-t border-border bg-background p-4">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              disabled={isSending || isWaiting}
              rows={1}
              className="w-full px-4 py-3 pr-12 border border-border rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          {isWaiting ? (
            <button
              onClick={handleStop}
              className="flex-shrink-0 w-12 h-12 rounded-xl bg-red-500 text-white flex items-center justify-center hover:bg-red-600 transition-colors"
              title="Stop"
            >
              <Square className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!message.trim() || isSending}
              className="flex-shrink-0 w-12 h-12 rounded-xl bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Send"
            >
              <Send className="w-5 h-5" />
            </button>
          )}
        </div>

        <p className="text-xs text-muted-foreground mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
