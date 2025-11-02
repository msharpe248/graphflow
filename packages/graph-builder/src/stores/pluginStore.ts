import { create } from 'zustand';
import { StepTypeInfo } from '@/types/graph';

interface PluginStore {
  // State
  stepTypes: Record<string, StepTypeInfo>;
  isLoading: boolean;
  error: string | null;
  lastFetched: number | null;

  // Actions
  fetchStepTypes: () => Promise<void>;
  getStepType: (type: string) => StepTypeInfo | undefined;
  getStepTypesByCategory: () => Record<string, StepTypeInfo[]>;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const usePluginStore = create<PluginStore>((set, get) => ({
  // Initial state
  stepTypes: {},
  isLoading: false,
  error: null,
  lastFetched: null,

  // Fetch step types from API
  fetchStepTypes: async () => {
    set({ isLoading: true, error: null });

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/steps`);

      if (!response.ok) {
        throw new Error(`Failed to fetch step types: ${response.statusText}`);
      }

      const steps = await response.json();

      // Convert array to record
      const stepTypesRecord: Record<string, StepTypeInfo> = {};

      for (const step of steps) {
        stepTypesRecord[step.type] = {
          type: step.type,
          category: step.category,
          label: step.label,
          description: step.description,
          color: getColorForCategory(step.category),
          icon: getIconForCategory(step.category),
          configSchema: step.config_schema,
          uiComponent: step.ui_component,
        };
      }

      set({
        stepTypes: stepTypesRecord,
        isLoading: false,
        lastFetched: Date.now(),
      });
    } catch (error) {
      console.error('Error fetching step types:', error);
      set({
        error: error instanceof Error ? error.message : 'Unknown error',
        isLoading: false,
      });
    }
  },

  // Get a specific step type
  getStepType: (type: string) => {
    return get().stepTypes[type];
  },

  // Get step types grouped by category
  getStepTypesByCategory: () => {
    const grouped: Record<string, StepTypeInfo[]> = {
      control: [],
      ai: [],
      data: [],
      transform: [],
      general: [],
    };

    const stepTypes = get().stepTypes;

    Object.values(stepTypes).forEach((stepType) => {
      const category = stepType.category || 'general';
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(stepType);
    });

    return grouped;
  },
}));

// Helper function to get color for category
function getColorForCategory(category: string): string {
  const colorMap: Record<string, string> = {
    control: '#10b981',
    ai: '#8b5cf6',
    data: '#3b82f6',
    transform: '#f59e0b',
    general: '#6b7280',
  };
  return colorMap[category] || colorMap.general;
}

// Helper function to get icon for category
function getIconForCategory(category: string): string {
  const iconMap: Record<string, string> = {
    control: 'Play',
    ai: 'Sparkles',
    data: 'Database',
    transform: 'Code',
    general: 'Box',
  };
  return iconMap[category] || iconMap.general;
}
