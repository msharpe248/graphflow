import { useCallback, useRef } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  ReactFlowProvider,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useGraphStore } from '@/stores/graphStore';
import CustomNode from './CustomNode';
import ShapeNode from './ShapeNode';

const nodeTypes = {
  custom: CustomNode,
  shape: ShapeNode,
};

function GraphCanvasInner() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const reactFlowInstance = useReactFlow();
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
  } = useGraphStore();

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      if (!reactFlowBounds) return;

      // Check if it's a step
      const stepType = event.dataTransfer.getData('application/reactflow');
      if (stepType) {
        // Convert screen coordinates to flow coordinates for nodes
        const position = reactFlowInstance.project({
          x: event.clientX - reactFlowBounds.left,
          y: event.clientY - reactFlowBounds.top,
        });
        addNode(stepType, position);
        return;
      }

      // Check if it's a shape
      const shapeType = event.dataTransfer.getData('application/shape');
      if (shapeType && (shapeType === 'rectangle' || shapeType === 'ellipse')) {
        // Use pixel coordinates directly for shapes (no projection)
        const position = {
          x: event.clientX - reactFlowBounds.left,
          y: event.clientY - reactFlowBounds.top,
        };
        console.log('[GraphCanvas] Dropping shape:', shapeType, 'at position:', position);
        useGraphStore.getState().addShape(shapeType, position);
        return;
      }
    },
    [addNode, reactFlowInstance]
  );

  return (
    <div ref={reactFlowWrapper} className="h-full w-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={nodeTypes}
        className="bg-gray-50"
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        elevateNodesOnSelect={false}
      >
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            return node.data.stepTypeInfo?.color || '#94a3b8';
          }}
          className="!bg-white !border !border-gray-300"
        />
      </ReactFlow>
    </div>
  );
}

export default function GraphCanvas() {
  return (
    <ReactFlowProvider>
      <GraphCanvasInner />
    </ReactFlowProvider>
  );
}
