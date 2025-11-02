import { create } from 'zustand';
import { Node, Edge, Connection, addEdge, applyNodeChanges, applyEdgeChanges, NodeChange, EdgeChange } from 'reactflow';
import { GraphDefinition, Step, Metadata, MemorySchema, NodeData } from '@/types/graph';
import { usePluginStore } from './pluginStore';

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
}

let nodeIdCounter = 1;

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

  // Node operations
  addNode: (stepType, position) => {
    const stepTypeInfo = usePluginStore.getState().getStepType(stepType);
    if (!stepTypeInfo) return;

    const id = `${stepType}_${nodeIdCounter++}`;
    const step: Step = {
      id,
      type: stepType,
      config: {},
      memory_reads: [],
      memory_writes: [],
    };

    const newNode: Node<NodeData> = {
      id,
      type: 'custom',
      position,
      data: {
        step,
        stepTypeInfo,
      },
    };

    set((state) => ({
      nodes: [...state.nodes, newNode],
    }));
  },

  updateNode: (nodeId, stepUpdate) =>
    set((state) => ({
      nodes: state.nodes.map((node) => {
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
      }),
    })),

  deleteNode: (nodeId) =>
    set((state) => ({
      nodes: state.nodes.filter((n) => n.id !== nodeId),
      edges: state.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
      selectedNodeId: state.selectedNodeId === nodeId ? null : state.selectedNodeId,
    })),

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
        markerEnd: {
          type: 'arrowclosed',
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
      return {
        id: step.id,
        type: 'custom',
        position: { x: 100 + (index % 3) * 250, y: 100 + Math.floor(index / 3) * 150 },
        data: { step, stepTypeInfo },
      };
    });

    const edges: Edge[] = graph.edges.map((edge) => ({
      id: edge.id,
      source: edge.from,
      target: edge.to,
      type: 'default',
      markerEnd: {
        type: 'arrowclosed',
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
}));
