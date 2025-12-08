import { useEffect, useRef } from 'react';
import { Conversation } from '@/types/chat';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

interface MessageListProps {
  conversation: Conversation;
}

export default function MessageList({ conversation }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversation.messages.length, conversation.activeRunId]);

  const isWaiting = !!conversation.activeRunId;

  if (conversation.messages.length === 0 && !isWaiting) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        <div className="text-center max-w-md px-4">
          <p className="text-lg mb-2">Start a conversation</p>
          <p className="text-sm">
            Type your message below to chat with this graph.
            Your message will be sent as the <code className="bg-muted px-1 rounded">query</code> input.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto chat-messages px-4 py-4"
    >
      <div className="max-w-3xl mx-auto space-y-4">
        {conversation.messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isWaiting && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
