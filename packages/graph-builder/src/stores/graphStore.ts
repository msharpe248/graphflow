import { create } from 'zustand';
import { Node, Edge, Connection, addEdge, applyNodeChanges, applyEdgeChanges, NodeChange, EdgeChange, MarkerType } from 'reactflow';
import { GraphDefinition, Step, Metadata, MemorySchema, NodeData } from '@/types/graph';
import { usePluginStore } from './pluginStore';
import { validateGraph, ValidationResult } from '@/utils/graphValidator';

interface GraphStore {
  // Graph metadata
  metadata: Metadata;
  memory: MemorySchema;

  // ReactFlow state
  nodes: Node<NodeData>[];
  edges: Edge[];

  // Selected node for properties panel
  selectedNodeId: string | null;

  // Actions
  setMetadata: (metadata: Partial<Metadata>) => void;
  setMemory: (memory: Partial<MemorySchema>) => void;
  setMemoryValue: (namespace: 'inputs' | 'outputs' | 'intermediate', key: string, value: any) => void;

  // Node operations
  addNode: (stepType: string, position: { x: number; y: number }) => void;
  updateNode: (nodeId: string, step: Partial<Step>) => void;
  deleteNode: (nodeId: string) => void;
  setSelectedNode: (nodeId: string | null) => void;

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
}

let nodeIdCounter = 1;

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
  selectedNodeId: null,

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
    set((state) => ({
      memory: {
        ...state.memory,
        [namespace]: {
          ...state.memory[namespace],
          [key]: {
            ...state.memory[namespace][key],
            default: value,
          },
        },
      },
    })),

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
      };
    }),

  setSelectedNode: (nodeId) =>
    set({ selectedNodeId: nodeId }),

  // ReactFlow handlers
  onNodesChange: (changes) =>
    set((state) => ({
      nodes: applyNodeChanges(changes, state.nodes),
    })),

  onEdgesChange: (changes) =>
    set((state) => ({
      edges: applyEdgeChanges(changes, state.edges),
    })),

  onConnect: (connection) =>
    set((state) => {
      const newEdge = {
        ...connection,
        id: `e${connection.source}-${connection.target}`,
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
      };
      return {
        edges: addEdge(newEdge, state.edges),
      };
    }),

  // Graph operations
  loadGraph: (graph) => {
    const nodes: Node<NodeData>[] = graph.steps.map((step, index) => {
      const stepTypeInfo = usePluginStore.getState().getStepType(step.type);
      if (!stepTypeInfo) {
        throw new Error(`Step type "${step.type}" not found`);
      }
      return {
        id: step.id,
        type: 'custom',
        position: { x: 100 + (index % 3) * 250, y: 100 + Math.floor(index / 3) * 150 },
        data: { step, stepTypeInfo },
        deletable: true,
      };
    });

    const edges: Edge[] = graph.edges.map((edge) => ({
      id: edge.id,
      source: edge.from,
      target: edge.to,
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

    set({
      metadata: graph.metadata,
      memory: graph.memory,
      nodes,
      edges,
      selectedNodeId: null,
    });
  },

  exportGraph: () => {
    const state = get();

    const steps: Step[] = state.nodes.map((node) => node.data.step);
    const graphEdges = state.edges.map((edge) => ({
      id: edge.id,
      from: edge.source,
      to: edge.target,
    }));

    return {
      version: '1.0',
      metadata: state.metadata,
      memory: state.memory,
      steps,
      edges: graphEdges,
    };
  },

  clearGraph: () =>
    set({
      metadata: {
        name: 'Untitled Graph',
        description: '',
        version: '1.0',
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
      selectedNodeId: null,
    }),

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
}));
