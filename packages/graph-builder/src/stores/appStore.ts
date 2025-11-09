import { create } from 'zustand';

export type View = 'builder' | 'runtime';

interface RuntimeContext {
  agentId?: string;
  runId?: string;
}

interface AppStore {
  activeView: View;
  runtimeContext: RuntimeContext | null;
  showDataFlowEdges: boolean;

  // View switching
  setActiveView: (view: View, context?: RuntimeContext) => void;
  switchToBuilder: () => void;
  switchToRuntime: (context?: RuntimeContext) => void;

  // Clear runtime context
  clearRuntimeContext: () => void;

  // Data flow visualization
  setShowDataFlowEdges: (show: boolean) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  activeView: 'builder',
  runtimeContext: null,
  showDataFlowEdges: false,

  setActiveView: (view, context) =>
    set({
      activeView: view,
      runtimeContext: context || null,
    }),

  switchToBuilder: () =>
    set({
      activeView: 'builder',
      runtimeContext: null,
    }),

  switchToRuntime: (context) =>
    set({
      activeView: 'runtime',
      runtimeContext: context || null,
    }),

  clearRuntimeContext: () =>
    set({
      runtimeContext: null,
    }),

  setShowDataFlowEdges: (show) =>
    set({
      showDataFlowEdges: show,
    }),
}));
