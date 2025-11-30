import { useState } from 'react';
import { Plus, Trash2, Edit2, Package, Wrench, Server } from 'lucide-react';
import { EditorProps } from './types';
import {
  ToolEntry,
  ToolDefinition,
  MCPTool,
  isMappedStepTool,
  isMCPTool,
  createMappedStepTool,
} from '@/types/tool';
import ToolBuilderModal from './ToolBuilderModal';
import MCPBuilderModal from './MCPBuilderModal';

export default function ToolEditor({ value, onChange, stepId }: EditorProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isMCPModalOpen, setIsMCPModalOpen] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  // Ensure value is always an array
  const tools: ToolEntry[] = Array.isArray(value) ? value : [];

  // Open modal for creating new tool
  const handleCreate = () => {
    setEditingIndex(null);
    setIsModalOpen(true);
  };

  // Open MCP modal
  const handleCreateMCP = () => {
    setIsMCPModalOpen(true);
  };

  // Edit an existing tool
  const handleEdit = (index: number) => {
    const tool = tools[index];
    if (isMappedStepTool(tool)) {
      setEditingIndex(index);
      setIsModalOpen(true);
    }
    // TODO: Support editing MCP tools
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

  // Save MCP tools from modal
  const handleSaveMCPTools = (mcpTools: MCPTool[]) => {
    onChange([...tools, ...mcpTools]);
  };

  // Get display info for a tool entry
  const getToolInfo = (entry: ToolEntry): { name: string; description: string; type: 'step' | 'mcp' | 'function' } => {
    if (isMappedStepTool(entry)) {
      return {
        name: entry.definition.name,
        description: entry.definition.description,
        type: 'step',
      };
    }
    if (isMCPTool(entry)) {
      return {
        name: entry.definition.name,
        description: entry.definition.description || `MCP: ${entry.definition.mcp_tool_name}`,
        type: 'mcp',
      };
    }
    return { name: 'Unknown', description: '', type: 'function' };
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
            const isMCP = info.type === 'mcp';
            return (
              <div
                key={index}
                className={`p-3 border rounded-lg hover:border-gray-300 transition-colors ${
                  isMCP ? 'bg-purple-50/50 border-purple-200' : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-2 flex-1 min-w-0">
                    {isMCP ? (
                      <Server className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                    ) : (
                      <Package className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    )}
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
                    {!isMCP && (
                      <button
                        onClick={() => handleEdit(index)}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                        title="Edit tool"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                    )}
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

      {/* Add Buttons */}
      <div className="flex gap-2">
        <button
          onClick={handleCreate}
          className="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Tool
        </button>
        <button
          onClick={handleCreateMCP}
          className="flex-1 px-3 py-2 text-sm font-medium text-purple-700 bg-purple-50 border border-purple-300 rounded-md hover:bg-purple-100 transition-colors flex items-center justify-center gap-2"
        >
          <Server className="w-4 h-4" />
          Add MCP
        </button>
      </div>

      {/* Tool Builder Modal */}
      <ToolBuilderModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveTool}
        initialTool={getEditingTool()}
        title={editingIndex !== null ? 'Edit Tool' : 'Create Tool'}
        stepId={stepId}
      />

      {/* MCP Builder Modal */}
      <MCPBuilderModal
        isOpen={isMCPModalOpen}
        onClose={() => setIsMCPModalOpen(false)}
        onSave={handleSaveMCPTools}
        stepId={stepId}
      />
    </div>
  );
}
