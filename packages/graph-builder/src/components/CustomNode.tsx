import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import * as Icons from 'lucide-react';
import { X } from 'lucide-react';
import { NodeData } from '@/types/graph';
import { useGraphStore } from '@/stores/graphStore';
import { useAppStore } from '@/stores/appStore';

function CustomNode({ id, data, selected }: NodeProps<NodeData>) {
  const { step, stepTypeInfo } = data;
  const setSelectedNode = useGraphStore((state) => state.setSelectedNode);
  const deleteNode = useGraphStore((state) => state.deleteNode);
  const showDataFlowEdges = useAppStore((state) => state.showDataFlowEdges);

  const handleClick = () => {
    setSelectedNode(id);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    deleteNode(id);
  };

  // Get the icon component
  const IconComponent = stepTypeInfo.icon
    ? (Icons as any)[stepTypeInfo.icon]
    : null;

  return (
    <div
      onClick={handleClick}
      className={`
        px-4 py-3 rounded-lg border-2 bg-white shadow-md
        min-w-[160px] max-w-[200px]
        cursor-pointer transition-all relative group
        ${selected ? 'border-primary ring-2 ring-primary/20' : 'border-gray-300 hover:border-gray-400'}
      `}
      style={{
        borderLeftColor: stepTypeInfo.color,
        borderLeftWidth: '4px',
      }}
    >
      {/* Delete button - appears on hover */}
      <button
        onClick={handleDelete}
        className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center hover:bg-red-600 z-10"
        title="Delete node"
      >
        <X className="w-3 h-3" />
      </button>
      {/* Handles */}
      {step.type !== 'start' && (
        <Handle
          type="target"
          position={Position.Top}
          id="top"
          className="!w-3 !h-3 !bg-gray-400"
        />
      )}
      {step.type !== 'output' && (
        <Handle
          type="source"
          position={Position.Bottom}
          id="bottom"
          className="!w-3 !h-3 !bg-gray-400"
        />
      )}

      {/* Data flow handles - always in DOM but only visible when data flow view is enabled */}
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        className={`!w-2 !h-2 !bg-purple-500 ${!showDataFlowEdges ? '!opacity-0 !pointer-events-none' : ''}`}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        className={`!w-2 !h-2 !bg-purple-500 ${!showDataFlowEdges ? '!opacity-0 !pointer-events-none' : ''}`}
      />

      {/* Node content */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          {IconComponent && (
            <IconComponent
              className="w-4 h-4 flex-shrink-0"
              style={{ color: stepTypeInfo.color }}
            />
          )}
          <div className="text-xs font-semibold text-gray-500 uppercase">
            {stepTypeInfo.label}
          </div>
        </div>
        <div className="text-sm font-medium text-gray-900 truncate">
          {step.id}
        </div>
        {step.config && Object.keys(step.config).length > 0 && (
          <div className="text-xs text-gray-500 truncate">
            {Object.keys(step.config).length} config{Object.keys(step.config).length > 1 ? 's' : ''}
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(CustomNode);
