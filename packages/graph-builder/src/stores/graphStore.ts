import { create } from 'zustand';
import { Node, Edge, Connection, addEdge, applyNodeChanges, applyEdgeChanges, NodeChange, EdgeChange, MarkerType, Position } from 'reactflow';
import { GraphDefinition, Step, Metadata, MemorySchema, NodeData, Shape } from '@/types/graph';
import { usePluginStore } from './pluginStore';
import { validateGraph, ValidationResult } from '@/utils/graphValidator';

interface GraphStore {
  // Graph metadata
  metadata: Metadata;
  memory: MemorySchema;

  // ReactFlow state
  nodes: Node<NodeData>[];
  edges: Edge[];

  // Shapes (for visual annotations)
  shapes: Shape[];

  // Selected node/shape for properties panel
  selectedNodeId: string | null;
  selectedShapeId: string | null;

  // Revision tracking - stores JSON of last saved state
  lastSavedState: string | null;

  // Actions
  setMetadata: (metadata: Partial<Metadata>) => void;
  setMemory: (memory: Partial<MemorySchema>) => void;
  setMemoryValue: (namespace: 'inputs' | 'outputs' | 'intermediate', key: string, value: any) => void;

  // Node operations
  addNode: (stepType: string, position: { x: number; y: number }) => void;
  updateNode: (nodeId: string, step: Partial<Step>) => void;
  deleteNode: (nodeId: string) => void;
  setSelectedNode: (nodeId: string | null) => void;

  // Shape operations
  addShape: (shapeType: 'rectangle' | 'ellipse', position: { x: number; y: number }) => void;
  updateShape: (shapeId: string, shape: Partial<Shape>) => void;
  deleteShape: (shapeId: string) => void;
  setSelectedShape: (shapeId: string | null) => void;

  // Edge operations
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;

  // Graph operations
  loadGraph: (graph: GraphDefinition) => void;
  exportGraph: () => GraphDefinition;
  clearGraph: () => void;

  // Validation
  validateGraph: () => ValidationResult;

  // Agent linking
  linkToAgent: (agentId: string) => void;
  unlinkAgent: () => void;

  // Revision management
  incrementRevision: () => void;
}

let nodeIdCounter = 1;
let shapeIdCounter = 1;

// Helper function to normalize JSON Schema types to backend memory types
function normalizeMemoryType(schemaType: string | undefined): string {
  if (!schemaType) return 'string';
  // Backend expects: 'number', 'string', 'array', 'boolean', 'any', 'object'
  // JSON Schema can have 'integer' which needs to map to 'number'
  if (schemaType === 'integer') return 'number';
  return schemaType;
}

// Helper function to find all memory bindings in use
function findUsedMemoryBindings(nodes: Node<NodeData>[]): Set<string> {
  const used = new Set<string>();

  // Recursive function to scan any value for {memory.field} patterns
  const scanValue = (value: any) => {
    if (typeof value === 'string') {
      const pattern = /\{memory\.([^}]+)\}/g;
      let match;
      while ((match = pattern.exec(value)) !== null) {
        used.add(match[1]);
      }
    } else if (typeof value === 'object' && value !== null) {
      Object.values(value).forEach(scanValue);
    }
  };

  nodes.forEach((node) => {
    // Skip shape nodes - they don't have step data
    if (node.type === 'shape' || !node.data.step) return;

    const { step } = node.data;
    // Scan config for {memory.field} patterns
    scanValue(step.config);
    // Scan outputs for {memory.field} patterns
    scanValue(step.outputs);
  });

  return used;
}

export const useGraphStore = create<GraphStore>((set, get) => ({
  // Initial state
  metadata: {
    name: 'Untitled Graph',
    description: '',
    version: '1.0',
    revision: 1,
    tags: [],
  },
  memory: {
    inputs: {},
    outputs: {},
    intermediate: {},
    secrets: {},
    config: {},
    environment: {},
  },
  nodes: [],
  edges: [],
  shapes: [],
  selectedNodeId: null,
  selectedShapeId: null,
  lastSavedState: null,

  // Metadata actions
  setMetadata: (metadata) =>
    set((state) => ({
      metadata: { ...state.metadata, ...metadata },
    })),

  setMemory: (memory) =>
    set((state) => ({
      memory: { ...state.memory, ...memory },
    })),

  setMemoryValue: (namespace, key, value) =>
    set((state) => {
      const existingField = state.memory[namespace][key];
      const newField = existingField
        ? {
            ...existingField,
            default: value,
          }
        : {
            type: 'string',
            description: '',
            default: value,
            required: false,
          };

      console.log('[graphStore] setMemoryValue:', { namespace, key, value, existingField, newField });

      return {
        memory: {
          ...state.memory,
          [namespace]: {
            ...state.memory[namespace],
            [key]: newField,
          },
        },
      };
    }),

  // Node operations
  addNode: (stepType, position) => {
    const stepTypeInfo = usePluginStore.getState().getStepType(stepType);
    if (!stepTypeInfo) return;

    const id = `${stepType}_${nodeIdCounter++}`;

    // Auto-create memory fields and bindings for config properties
    const config: Record<string, any> = {};
    const newMemoryFields: Record<string, any> = {};

    if (stepTypeInfo.configSchema?.properties) {
      Object.entries(stepTypeInfo.configSchema.properties).forEach(([key, schema]: [string, any]) => {
        // Create memory field for this config property
        const memoryKey = `${id}.${key}`;
        newMemoryFields[memoryKey] = {
          type: normalizeMemoryType(schema.type),
          description: schema.description || `${key} for ${id}`,
          required: false,
          default: schema.default,
        };

        // Auto-bind config to memory location
        config[key] = `{memory.${memoryKey}}`;
      });
    }

    // Auto-create outputs object with memory bindings
    const outputs: Record<string, string> = {};

    if (stepTypeInfo.outputsSchema?.properties) {
      Object.entries(stepTypeInfo.outputsSchema.properties).forEach(([outputKey, outputSchema]: [string, any]) => {
        // Create memory field for this output
        const memoryKey = `${id}.${outputKey}`;
        newMemoryFields[memoryKey] = {
          type: normalizeMemoryType((outputSchema as any).type),
          description: (outputSchema as any).description || `${outputKey} output from ${id}`,
          required: false,
        };

        // Auto-bind output to memory location
        outputs[outputKey] = `{memory.${memoryKey}}`;
      });
    }

    const step: Step = {
      id,
      type: stepType,
      config,
      outputs,
    };

    const newNode: Node<NodeData> = {
      id,
      type: 'custom',
      position,
      data: {
        step,
        stepTypeInfo,
      },
      deletable: true,
      zIndex: 100,
    };

    set((state) => ({
      nodes: [...state.nodes, newNode],
      memory: {
        ...state.memory,
        intermediate: {
          ...state.memory.intermediate,
          ...newMemoryFields,
        },
      },
      metadata: {
        ...state.metadata,
      },
    }));
  },

  updateNode: (nodeId, stepUpdate) =>
    set((state) => {
      // Update the node
      const updatedNodes = state.nodes.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: {
              ...node.data,
              step: { ...node.data.step, ...stepUpdate },
            },
          };
        }
        return node;
      });

      // Find all memory bindings still in use
      const usedBindings = findUsedMemoryBindings(updatedNodes);

      // Clean up unused memory fields from intermediate namespace
      // (only auto-created fields that match pattern <step_id>.<config_key>)
      const cleanedIntermediate: Record<string, any> = {};
      Object.entries(state.memory.intermediate).forEach(([key, value]) => {
        // Keep the field if it's used OR if it doesn't match auto-created pattern
        if (usedBindings.has(key) || !key.includes('.')) {
          cleanedIntermediate[key] = value;
        }
      });

      return {
        nodes: updatedNodes,
        memory: {
          ...state.memory,
          intermediate: cleanedIntermediate,
        },
        metadata: {
          ...state.metadata,
        },
      };
    }),

  deleteNode: (nodeId) =>
    set((state) => {
      // Remove the node and its edges
      const updatedNodes = state.nodes.filter((n) => n.id !== nodeId);
      const updatedEdges = state.edges.filter((e) => e.source !== nodeId && e.target !== nodeId);

      // Find all memory bindings still in use
      const usedBindings = findUsedMemoryBindings(updatedNodes);

      // Clean up unused memory fields from intermediate namespace
      const cleanedIntermediate: Record<string, any> = {};
      Object.entries(state.memory.intermediate).forEach(([key, value]) => {
        // Keep the field if it's used OR if it doesn't match auto-created pattern
        if (usedBindings.has(key) || !key.includes('.')) {
          cleanedIntermediate[key] = value;
        }
      });

      return {
        nodes: updatedNodes,
        edges: updatedEdges,
        selectedNodeId: state.selectedNodeId === nodeId ? null : state.selectedNodeId,
        memory: {
          ...state.memory,
          intermediate: cleanedIntermediate,
        },
        metadata: {
          ...state.metadata,
        },
      };
    }),

  setSelectedNode: (nodeId) =>
    set({ selectedNodeId: nodeId, selectedShapeId: null }),

  // Shape operations
  addShape: (shapeType, position) => {
    const id = `shape_${shapeIdCounter++}`;

    // Type-specific defaults
    const defaults = shapeType === 'textbox' ? {
      size: { width: 400, height: 300 },
      color: '#ffffff',
      borderColor: '#d1d5db',
      opacity: 1.0,
      padding: 16,
      shadow: false,
    } : shapeType === 'stickynote' ? {
      size: { width: 250, height: 250 },
      color: '#fef08a',  // yellow-200
      borderColor: '#fde047',  // yellow-300
      opacity: 0.95,
      padding: 12,
      shadow: true,
    } : {
      size: { width: 300, height: 200 },
      color: '#93c5fd',  // Muted blue-300
      borderColor: '#64748b',  // Slate-500
      opacity: 0.3,
      padding: 16,
      shadow: false,
    };

    const newShape: Shape = {
      id,
      type: shapeType,
      position,
      ...defaults,
      zIndex: 1,         // Behind steps (steps are at 100) but above background
      textAlign: 'center',
      textVerticalAlign: 'center',
      titleFontSize: shapeType === 'textbox' || shapeType === 'stickynote' ? 16 : 14,
      textFontSize: 12,
      textColor: '#1f2937',  // Dark gray for visibility
      fontWeight: 'semibold',
    };

    // Create as a ReactFlow node
    const newNode: Node = {
      id,
      type: 'shape',
      position,
      data: { shape: newShape },
      deletable: true,
      connectable: false,  // Shapes can't be connected
      zIndex: 1,
    };

    console.log('[graphStore] Adding shape as node:', newNode);

    set((state) => ({
      nodes: [...state.nodes, newNode],
      shapes: [...state.shapes, newShape],
      selectedShapeId: id,
      selectedNodeId: null,
      metadata: {
        ...state.metadata,
      },
    }));
  },

  updateShape: (shapeId, shapeUpdate) =>
    set((state) => ({
      shapes: state.shapes.map((shape) =>
        shape.id === shapeId ? { ...shape, ...shapeUpdate } : shape
      ),
      nodes: state.nodes.map((node) =>
        node.id === shapeId
          ? {
              ...node,
              data: {
                ...node.data,
                shape: { ...node.data.shape, ...shapeUpdate },
              },
              // Update node z-index if shape z-index changed
              ...(shapeUpdate.zIndex !== undefined && { zIndex: shapeUpdate.zIndex }),
            }
          : node
      ),
      metadata: {
        ...state.metadata,
      },
    })),

  deleteShape: (shapeId) =>
    set((state) => ({
      shapes: state.shapes.filter((s) => s.id !== shapeId),
      nodes: state.nodes.filter((n) => n.id !== shapeId),
      selectedShapeId: state.selectedShapeId === shapeId ? null : state.selectedShapeId,
      metadata: {
        ...state.metadata,
      },
    })),

  setSelectedShape: (shapeId) =>
    set({ selectedShapeId: shapeId, selectedNodeId: null }),

  // ReactFlow handlers
  onNodesChange: (changes) =>
    set((state) => {
      const updatedNodes = applyNodeChanges(changes, state.nodes);

      // Sync position changes back to shapes
      const updatedShapes = state.shapes.map((shape) => {
        const node = updatedNodes.find((n) => n.id === shape.id);
        if (node && node.position) {
          return { ...shape, position: node.position };
        }
        return shape;
      });

      return {
        nodes: updatedNodes,
        shapes: updatedShapes,
      };
    }),

  onEdgesChange: (changes) =>
    set((state) => {
      // Check if any edge is being removed
      const hasRemoval = changes.some((change) => change.type === 'remove');
      return {
        edges: applyEdgeChanges(changes, state.edges),
        ...(hasRemoval && {
          metadata: {
            ...state.metadata,
          },
        }),
      };
    }),

  onConnect: (connection) =>
    set((state) => {
      const newEdge = {
        ...connection,
        id: `e${connection.source}-${connection.target}`,
        type: 'default',
        sourceHandle: connection.sourceHandle || 'bottom',
        targetHandle: connection.targetHandle || 'top',
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
        deletable: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 25,
          height: 25,
          color: '#374151',
        },
        style: {
          strokeWidth: 2,
          stroke: '#374151',
        },
      };
      return {
        edges: addEdge(newEdge, state.edges),
        metadata: {
          ...state.metadata,
        },
      };
    }),

  // Graph operations
  loadGraph: (graph) => {
    const stepNodes: Node<NodeData>[] = graph.steps.map((step, index) => {
      const stepTypeInfo = usePluginStore.getState().getStepType(step.type);
      if (!stepTypeInfo) {
        throw new Error(`Step type "${step.type}" not found`);
      }
      return {
        id: step.id,
        type: 'custom',
        position: step.position || { x: 100 + (index % 3) * 250, y: 100 + Math.floor(index / 3) * 150 },
        data: { step, stepTypeInfo },
        deletable: true,
        zIndex: 100,
      };
    });

    // Update nodeIdCounter to avoid conflicts with loaded step IDs
    graph.steps.forEach((step) => {
      const match = step.id.match(/^step_(\d+)$/);
      if (match) {
        const num = parseInt(match[1], 10);
        if (num >= nodeIdCounter) {
          nodeIdCounter = num + 1;
        }
      }
    });

    // Convert shapes to ReactFlow nodes with default values for new properties
    const shapesWithDefaults: Shape[] = (graph.shapes || []).map((shape) => ({
      ...shape,
      textAlign: shape.textAlign || 'center',
      textVerticalAlign: shape.textVerticalAlign || 'center',
      titleFontSize: shape.titleFontSize || 14,
      textFontSize: shape.textFontSize || 12,
      textColor: shape.textColor || '#1f2937',
      fontWeight: shape.fontWeight || 'semibold',
      shadow: shape.shadow ?? false,
      padding: shape.padding ?? 16,
    }));

    // Update shapeIdCounter to avoid conflicts with loaded shape IDs
    shapesWithDefaults.forEach((shape) => {
      const match = shape.id.match(/^shape_(\d+)$/);
      if (match) {
        const num = parseInt(match[1], 10);
        if (num >= shapeIdCounter) {
          shapeIdCounter = num + 1;
        }
      }
    });

    const shapeNodes: Node[] = shapesWithDefaults.map((shape) => ({
      id: shape.id,
      type: 'shape',
      position: shape.position,
      data: { shape },
      deletable: true,
      connectable: false,
      zIndex: shape.zIndex || 1,
    }));

    const edges: Edge[] = graph.edges.map((edge) => ({
      id: edge.id,
      source: edge.from,
      target: edge.to,
      sourceHandle: 'bottom',
      targetHandle: 'top',
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
      type: 'default',
      deletable: true,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 25,
        height: 25,
        color: '#374151',
      },
      style: {
        strokeWidth: 2,
        stroke: '#374151',
      },
    }));

    // Store the loaded graph as the last saved state
    const loadedGraph = {
      version: graph.version,
      metadata: graph.metadata,
      memory: graph.memory,
      steps: graph.steps,
      edges: graph.edges,
      shapes: shapesWithDefaults.length > 0 ? shapesWithDefaults : undefined,
    };

    set({
      metadata: graph.metadata,
      memory: graph.memory,
      nodes: [...stepNodes, ...shapeNodes],
      edges,
      shapes: shapesWithDefaults,
      selectedNodeId: null,
      selectedShapeId: null,
      lastSavedState: JSON.stringify(loadedGraph),
    });
  },

  exportGraph: () => {
    const state = get();

    // Filter out shape nodes - only export step nodes
    const steps: Step[] = state.nodes
      .filter((node) => node.type === 'custom' && node.data.step)
      .map((node) => ({
        ...node.data.step,
        position: node.position,
      }));
    const graphEdges = state.edges.map((edge) => ({
      id: edge.id,
      from: edge.source,
      to: edge.target,
    }));

    const currentGraph: GraphDefinition = {
      version: '1.0',
      metadata: state.metadata,
      memory: state.memory,
      steps,
      edges: graphEdges,
      shapes: state.shapes.length > 0 ? state.shapes : undefined,
    };

    // Check if state has changed since last save
    const currentStateJSON = JSON.stringify(currentGraph);
    const hasChangedSinceLastSave = state.lastSavedState !== null && currentStateJSON !== state.lastSavedState;

    // Only increment revision if there were changes since last save
    if (hasChangedSinceLastSave) {
      currentGraph.metadata = {
        ...currentGraph.metadata,
        revision: (currentGraph.metadata.revision || 1) + 1,
      };
    }

    // Update last saved state and metadata
    set({
      lastSavedState: JSON.stringify(currentGraph),
      metadata: currentGraph.metadata,
    });

    return currentGraph;
  },

  clearGraph: () => {
    set({
      metadata: {
        name: 'Untitled Graph',
        description: '',
        version: '1.0',
        revision: 1,
        tags: [],
      },
      memory: {
        inputs: {},
        outputs: {},
        intermediate: {},
        secrets: {},
      },
      nodes: [],
      edges: [],
      shapes: [],
      selectedNodeId: null,
      selectedShapeId: null,
      lastSavedState: null,
    });
  },

  // Validation
  validateGraph: () => {
    const state = get();
    const graph = state.exportGraph();
    return validateGraph(graph, state.nodes);
  },

  // Agent linking
  linkToAgent: (agentId: string) =>
    set((state) => ({
      metadata: {
        ...state.metadata,
        linkedAgentId: agentId,
      },
    })),

  unlinkAgent: () =>
    set((state) => ({
      metadata: {
        ...state.metadata,
        linkedAgentId: undefined,
      },
    })),

  // Revision management
  incrementRevision: () =>
    set((state) => ({
      metadata: {
        ...state.metadata,
      },
    })),
}));
