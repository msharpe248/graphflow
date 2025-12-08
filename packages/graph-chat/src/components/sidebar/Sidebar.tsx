import { useState } from 'react';
import { Plus, Upload } from 'lucide-react';
import GraphSelector from './GraphSelector';
import ConversationList from './ConversationList';
import AddGraphModal from '@/components/modals/AddGraphModal';
import { useChatStore } from '@/stores/chatStore';

export default function Sidebar() {
  const [showAddGraph, setShowAddGraph] = useState(false);
  const { selectedGraphId, activeGraphs, createConversation } = useChatStore();

  const handleNewConversation = () => {
    if (selectedGraphId) {
      createConversation(selectedGraphId);
    }
  };

  return (
    <>
      <aside className="w-72 border-r border-border bg-muted/30 flex flex-col">
        {/* Header with Add Graph button */}
        <div className="p-3 border-b border-border">
          <button
            onClick={() => setShowAddGraph(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Upload className="w-4 h-4" />
            Add Graph
          </button>
        </div>

        {/* Graph selector */}
        <div className="border-b border-border">
          <GraphSelector />
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {/* New conversation button */}
          {selectedGraphId && (
            <div className="p-3 border-b border-border">
              <button
                onClick={handleNewConversation}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-border rounded-md hover:bg-muted transition-colors"
              >
                <Plus className="w-4 h-4" />
                New Conversation
              </button>
            </div>
          )}

          {/* Conversations */}
          <div className="flex-1 overflow-y-auto">
            {selectedGraphId ? (
              <ConversationList />
            ) : (
              <div className="p-4 text-center text-muted-foreground text-sm">
                {activeGraphs.length === 0
                  ? 'Add a graph to start chatting'
                  : 'Select a graph to see conversations'}
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Add Graph Modal */}
      {showAddGraph && (
        <AddGraphModal onClose={() => setShowAddGraph(false)} />
      )}
    </>
  );
}
