import { useState } from 'react';
import { Plus, Trash2, Edit2, Package, Wrench } from 'lucide-react';
import { EditorProps } from './types';
import {
  ToolEntry,
  ToolDefinition,
  isMappedStepTool,
  createMappedStepTool,
} from '@/types/tool';
import ToolBuilderModal from './ToolBuilderModal';

export default function ToolEditor({ value, onChange, stepId }: EditorProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  // Ensure value is always an array
  const tools: ToolEntry[] = Array.isArray(value) ? value : [];

  // Open modal for creating new tool
  const handleCreate = () => {
    setEditingIndex(null);
    setIsModalOpen(true);
  };

  // Edit an existing tool
  const handleEdit = (index: number) => {
    const tool = tools[index];
    if (isMappedStepTool(tool)) {
      setEditingIndex(index);
      setIsModalOpen(true);
    }
  };

  // Remove a tool
  const handleRemove = (index: number) => {
    const newTools = tools.filter((_, i) => i !== index);
    onChange(newTools);
  };

  // Save tool from modal
  const handleSaveTool = (definition: ToolDefinition) => {
    if (editingIndex !== null) {
      // Update existing tool
      const newTools = [...tools];
      newTools[editingIndex] = createMappedStepTool(definition);
      onChange(newTools);
    } else {
      // Add new tool
      const newTool = createMappedStepTool(definition);
      onChange([...tools, newTool]);
    }
  };

  // Get display info for a tool entry
  const getToolInfo = (entry: ToolEntry): { name: string; description: string } => {
    if (isMappedStepTool(entry)) {
      return {
        name: entry.definition.name,
        description: entry.definition.description,
      };
    }
    return { name: 'Unknown', description: '' };
  };

  // Get the tool definition for editing
  const getEditingTool = (): ToolDefinition | undefined => {
    if (editingIndex === null) return undefined;
    const tool = tools[editingIndex];
    if (isMappedStepTool(tool)) {
      return tool.definition;
    }
    return undefined;
  };

  return (
    <div className="space-y-2">
      {/* Tool List */}
      {tools.length > 0 && (
        <div className="space-y-2">
          {tools.map((entry, index) => {
            const info = getToolInfo(entry);
            return (
              <div
                key={index}
                className="p-3 bg-gray-50 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-2 flex-1 min-w-0">
                    <Package className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <span className="font-medium text-gray-900 text-sm truncate block">
                        {info.name || 'Unnamed tool'}
                      </span>
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                        {info.description || 'No description'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1 ml-2">
                    <button
                      onClick={() => handleEdit(index)}
                      className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                      title="Edit tool"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleRemove(index)}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Remove tool"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty State */}
      {tools.length === 0 && (
        <div className="p-4 bg-gray-50 border border-dashed border-gray-300 rounded-lg text-center">
          <Wrench className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p className="text-sm text-gray-500">No tools configured</p>
          <p className="text-xs text-gray-400 mt-1">
            Add tools to enable LLM function calling
          </p>
        </div>
      )}

      {/* Add Tool Button */}
      <button
        onClick={handleCreate}
        className="w-full px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
      >
        <Plus className="w-4 h-4" />
        Add Tool
      </button>

      {/* Tool Builder Modal */}
      <ToolBuilderModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveTool}
        initialTool={getEditingTool()}
        title={editingIndex !== null ? 'Edit Tool' : 'Create Tool'}
        stepId={stepId}
      />
    </div>
  );
}
