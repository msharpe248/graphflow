import { create } from 'zustand';
import { StepTypeInfo } from '@/types/graph';
import { useSettingsStore } from './settingsStore';

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
  getStepTypesByPlugin: () => Record<string, StepTypeInfo[]>;
}

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
      const apiBaseUrl = useSettingsStore.getState().getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/v1/steps`);

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
          plugin: step.plugin,
          plugin_version: step.plugin_version,
          color: getColorForStep(step.category, step.plugin),
          icon: getIconForStep(step.category, step.plugin),
          configSchema: step.config_schema,
          inputsSchema: step.inputs_schema,
          outputsSchema: step.outputs_schema,
          uiComponent: step.ui_component,
          can_be_tool: step.can_be_tool,
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

  // Get step types grouped by plugin
  getStepTypesByPlugin: () => {
    const grouped: Record<string, StepTypeInfo[]> = {};
    const stepTypes = get().stepTypes;

    Object.values(stepTypes).forEach((stepType) => {
      // Use the plugin field from the step metadata
      let plugin = stepType.plugin;

      // If plugin field is missing or empty, fall back to parsing namespace
      if (!plugin) {
        const parts = stepType.type.split('.');
        plugin = parts.length > 1 ? parts[0] : 'built-in';
      }

      if (!grouped[plugin]) {
        grouped[plugin] = [];
      }
      grouped[plugin].push(stepType);
    });

    return grouped;
  },
}));

// Plugin-specific color overrides
const pluginColorMap: Record<string, string> = {
  json: '#f97316',   // orange - JSON braces
  yaml: '#a855f7',   // purple - config files
  csv: '#22c55e',    // green - spreadsheet/table
  text: '#14b8a6',   // teal - text manipulation
  http: '#3b82f6',   // blue - network/web
};

// Plugin-specific icon overrides
const pluginIconMap: Record<string, string> = {
  json: 'Braces',      // { } curly braces
  yaml: 'FileCode',    // config file
  csv: 'Table',        // spreadsheet/table
  text: 'Type',        // text/typography
  http: 'Globe',       // network/web
};

// Category color defaults
const categoryColorMap: Record<string, string> = {
  control: '#10b981',
  ai: '#8b5cf6',
  data: '#3b82f6',
  transform: '#f59e0b',
  general: '#6b7280',
};

// Category icon defaults
const categoryIconMap: Record<string, string> = {
  control: 'Play',
  ai: 'Sparkles',
  data: 'Database',
  transform: 'Code',
  general: 'Box',
};

// Helper function to get color for step (plugin-specific or category default)
function getColorForStep(category: string, plugin?: string): string {
  // Check plugin-specific color first
  if (plugin && pluginColorMap[plugin]) {
    return pluginColorMap[plugin];
  }
  // Fall back to category color
  return categoryColorMap[category] || categoryColorMap.general;
}

// Helper function to get icon for step (plugin-specific or category default)
function getIconForStep(category: string, plugin?: string): string {
  // Check plugin-specific icon first
  if (plugin && pluginIconMap[plugin]) {
    return pluginIconMap[plugin];
  }
  // Fall back to category icon
  return categoryIconMap[category] || categoryIconMap.general;
}
