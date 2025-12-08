import { ChevronDown, X, MessageSquare } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '@/stores/chatStore';
import clsx from 'clsx';

export default function GraphSelector() {
  const { activeGraphs, selectedGraphId, selectGraph, removeGraph, getConversationsForGraph } = useChatStore();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedGraph = activeGraphs.find((g) => g.agentId === selectedGraphId);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (activeGraphs.length === 0) {
    return (
      <div className="p-3 text-sm text-muted-foreground text-center">
        No graphs loaded
      </div>
    );
  }

  return (
    <div className="p-3 relative" ref={dropdownRef}>
      {/* Selected graph display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between gap-2 px-3 py-2 border border-border rounded-md hover:bg-muted transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          <MessageSquare className="w-4 h-4 text-muted-foreground flex-shrink-0" />
          <span className="truncate">
            {selectedGraph?.name || 'Select a graph'}
          </span>
        </div>
        <ChevronDown className={clsx(
          "w-4 h-4 text-muted-foreground transition-transform flex-shrink-0",
          isOpen && "rotate-180"
        )} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute left-3 right-3 top-full mt-1 bg-background border border-border rounded-md shadow-lg z-50 max-h-64 overflow-y-auto">
          {activeGraphs.map((graph) => {
            const conversationCount = getConversationsForGraph(graph.agentId).length;
            const isSelected = graph.agentId === selectedGraphId;

            return (
              <div
                key={graph.agentId}
                className={clsx(
                  "flex items-center justify-between gap-2 px-3 py-2 hover:bg-muted cursor-pointer group",
                  isSelected && "bg-muted"
                )}
              >
                <button
                  onClick={() => {
                    selectGraph(graph.agentId);
                    setIsOpen(false);
                  }}
                  className="flex-1 flex items-center gap-2 text-left min-w-0"
                >
                  <MessageSquare className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-medium">{graph.name}</div>
                    {graph.description && (
                      <div className="truncate text-xs text-muted-foreground">
                        {graph.description}
                      </div>
                    )}
                  </div>
                  {conversationCount > 0 && (
                    <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                      {conversationCount}
                    </span>
                  )}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeGraph(graph.agentId);
                  }}
                  className="p-1 rounded hover:bg-background opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Remove graph"
                >
                  <X className="w-3 h-3 text-muted-foreground" />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
