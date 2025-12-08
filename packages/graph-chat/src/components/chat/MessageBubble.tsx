import { User, Bot, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message } from '@/types/chat';
import clsx from 'clsx';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isError = message.role === 'error';
  const isSystem = message.role === 'system';

  return (
    <div className={clsx(
      "flex gap-3",
      isUser && "justify-end"
    )}>
      {/* Avatar for non-user messages */}
      {!isUser && (
        <div className={clsx(
          "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
          isError ? "bg-red-100" : isSystem ? "bg-gray-100" : "bg-primary/10"
        )}>
          {isError ? (
            <AlertCircle className="w-4 h-4 text-red-600" />
          ) : (
            <Bot className="w-4 h-4 text-primary" />
          )}
        </div>
      )}

      {/* Message content */}
      <div className={clsx(
        "max-w-[80%] rounded-2xl px-4 py-2",
        isUser && "bg-primary text-primary-foreground",
        !isUser && !isError && "bg-muted",
        isError && "bg-red-50 border border-red-200 text-red-800"
      )}>
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {/* Timestamp */}
        <div className={clsx(
          "text-xs mt-1",
          isUser ? "text-primary-foreground/70" : "text-muted-foreground"
        )}>
          {formatTime(message.timestamp)}
        </div>
      </div>

      {/* Avatar for user messages */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
          <User className="w-4 h-4 text-primary-foreground" />
        </div>
      )}
    </div>
  );
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
