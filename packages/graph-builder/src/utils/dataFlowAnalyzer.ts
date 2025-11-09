import { Node, Edge, Position, MarkerType } from 'reactflow';
import { NodeData, MemorySchema } from '../types/graph';

/**
 * Extracts memory binding from a value like "{memory.field}", "{config.field}", etc.
 * Returns the full namespaced key like "memory.field" or "config.ui_url"
 */
function extractMemoryBinding(value: any): string | null {
  if (typeof value !== 'string') return null;
  const match = value.match(/^\{(memory|config|env|secrets)\.(.+)\}$/);
  if (match) {
    return `${match[1]}.${match[2]}`; // Return "namespace.field"
  }
  return null;
}

/**
 * Recursively scans an object for memory bindings and calls the callback for each found
 */
function scanForMemoryBindings(
  obj: any,
  callback: (memoryKey: string) => void
): void {
  if (typeof obj === 'string') {
    const memoryKey = extractMemoryBinding(obj);
    if (memoryKey) {
      callback(memoryKey);
    }
  } else if (Array.isArray(obj)) {
    obj.forEach((item) => scanForMemoryBindings(item, callback));
  } else if (obj && typeof obj === 'object') {
    Object.values(obj).forEach((value) => scanForMemoryBindings(value, callback));
  }
}

/**
 * Computes data flow edges based on memory dependencies between steps
 *
 * @param nodes - Array of React Flow nodes
 * @param memorySchema - Memory schema to identify input fields
 * @returns Array of data flow edges showing memory dependencies
 */
export function computeDataFlowEdges(nodes: Node<NodeData>[], memorySchema: MemorySchema): Edge[] {
  const dataFlowEdges: Edge[] = [];

  // Find the start node
  const startNode = nodes.find(
    (node) => node.type === 'custom' && node.data.step.type === 'start'
  );

  // Get all input memory field names
  const inputFields = new Set(Object.keys(memorySchema.inputs || {}));

  // Map of memory location -> node id that writes to it
  const memoryWriters = new Map<string, string>();

  // Map of memory location -> Set of node ids that read from it
  const memoryReaders = new Map<string, Set<string>>();

  // First pass: find all memory writers (outputs)
  nodes.forEach((node) => {
    if (node.type !== 'custom') return;

    const outputs = node.data.step.outputs || {};
    Object.values(outputs).forEach((memoryBinding) => {
      const memoryKey = extractMemoryBinding(memoryBinding);
      if (memoryKey) {
        // Store the node that writes to this memory location
        memoryWriters.set(memoryKey, node.id);
      }
    });
  });

  // Second pass: find memory readers (config inputs) and create edges
  nodes.forEach((node) => {
    if (node.type !== 'custom') return;

    const config = node.data.step.config || {};
    const nodeMemoryReaders = new Set<string>(); // Track unique memory keys this node reads

    scanForMemoryBindings(config, (memoryKey) => {
      // Track all readers for this memory location
      if (!memoryReaders.has(memoryKey)) {
        memoryReaders.set(memoryKey, new Set());
      }
      memoryReaders.get(memoryKey)!.add(node.id);
      nodeMemoryReaders.add(memoryKey);
    });

    // Create edges from writers to this reader
    nodeMemoryReaders.forEach((memoryKey) => {
      const writerNodeId = memoryWriters.get(memoryKey);

      // Only create edge if:
      // 1. There's a writer for this memory location
      // 2. The writer is a different node (no self-loops)
      if (writerNodeId && writerNodeId !== node.id) {
        dataFlowEdges.push({
          id: `dataflow-${writerNodeId}-${node.id}-${memoryKey}`,
          source: writerNodeId,
          sourceHandle: 'right',
          target: node.id,
          targetHandle: 'left',
          type: 'dataflow',
          data: { memoryKey },
          animated: false,
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20,
            color: '#8b5cf6',
          },
          style: {
            stroke: '#8b5cf6',
            strokeDasharray: '8,4',
            strokeWidth: 2,
          },
        } as Edge);
      }
    });
  });

  // Third pass: create implicit edges from start node for input fields
  // that are read but not written by any step
  if (startNode) {
    inputFields.forEach((inputField) => {
      const readers = memoryReaders.get(inputField);
      const hasWriter = memoryWriters.has(inputField);

      // If this input field is read by steps but not written by any step,
      // create edges from start node to all readers
      if (readers && !hasWriter) {
        readers.forEach((readerNodeId) => {
          // Don't create edge to start node itself
          if (readerNodeId !== startNode.id) {
            dataFlowEdges.push({
              id: `dataflow-start-${readerNodeId}-${inputField}`,
              source: startNode.id,
              sourceHandle: 'right',
              target: readerNodeId,
              targetHandle: 'left',
              type: 'dataflow',
              data: { memoryKey: inputField },
              animated: false,
              sourcePosition: Position.Right,
              targetPosition: Position.Left,
              markerEnd: {
                type: MarkerType.ArrowClosed,
                width: 20,
                height: 20,
                color: '#8b5cf6',
              },
              style: {
                stroke: '#8b5cf6',
                strokeDasharray: '8,4',
                strokeWidth: 2,
              },
            } as Edge);
          }
        });
      }
    });
  }

  return dataFlowEdges;
}
