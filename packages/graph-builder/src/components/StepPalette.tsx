import { useState, useEffect, useMemo, useCallback } from 'react';
import * as Icons from 'lucide-react';
import { Search, ChevronDown, ChevronRight, Layers, Package, Square, Circle, Shapes, FileText, StickyNote, ChevronsUpDown, ChevronsDownUp } from 'lucide-react';
import { StepTypeInfo } from '@/types/graph';
import { usePluginStore } from '@/stores/pluginStore';

interface StepPaletteProps {
  onDragStart: (event: React.DragEvent, stepType: string) => void;
  onShapeDragStart: (event: React.DragEvent, shapeType: 'rectangle' | 'ellipse' | 'textbox' | 'stickynote') => void;
}

type ViewMode = 'category' | 'plugin';
type MainTab = 'steps' | 'shapes';

export default function StepPalette({ onDragStart, onShapeDragStart }: StepPaletteProps) {
  const { isLoading, error, fetchStepTypes, getStepTypesByCategory, getStepTypesByPlugin } = usePluginStore();

  const [mainTab, setMainTab] = useState<MainTab>('steps');
  const [viewMode, setViewMode] = useState<ViewMode>('category');
  const [searchQuery, setSearchQuery] = useState('');
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [hasInitializedCollapse, setHasInitializedCollapse] = useState(false);

  // Fetch step types on mount
  useEffect(() => {
    fetchStepTypes();
  }, [fetchStepTypes]);

  // Get grouped steps based on view mode
  const stepsByCategory = getStepTypesByCategory();
  const stepsByPlugin = getStepTypesByPlugin();

  // Initialize collapse state once data is loaded
  useEffect(() => {
    if (hasInitializedCollapse) return;

    const categoryKeys = Object.keys(stepsByCategory);
    const pluginKeys = Object.keys(stepsByPlugin);

    if (categoryKeys.length > 0 || pluginKeys.length > 0) {
      // Collapse all except "Control" for categories and "Built-in" for plugins
      const initialCollapsed: Record<string, boolean> = {};

      categoryKeys.forEach(key => {
        initialCollapsed[key] = key.toLowerCase() !== 'control';
      });

      pluginKeys.forEach(key => {
        initialCollapsed[key] = key.toLowerCase() !== 'built-in';
      });

      setCollapsed(initialCollapsed);
      setHasInitializedCollapse(true);
    }
  }, [stepsByCategory, stepsByPlugin, hasInitializedCollapse]);

  // Get current group keys based on view mode
  const currentGroupKeys = useMemo(() => {
    return Object.keys(viewMode === 'category' ? stepsByCategory : stepsByPlugin);
  }, [viewMode, stepsByCategory, stepsByPlugin]);

  // Check if all groups are collapsed
  const allCollapsed = useMemo(() => {
    return currentGroupKeys.length > 0 && currentGroupKeys.every(key => collapsed[key]);
  }, [currentGroupKeys, collapsed]);

  // Expand all groups
  const expandAll = useCallback(() => {
    const newCollapsed: Record<string, boolean> = { ...collapsed };
    currentGroupKeys.forEach(key => {
      newCollapsed[key] = false;
    });
    setCollapsed(newCollapsed);
  }, [currentGroupKeys, collapsed]);

  // Collapse all groups
  const collapseAll = useCallback(() => {
    const newCollapsed: Record<string, boolean> = { ...collapsed };
    currentGroupKeys.forEach(key => {
      newCollapsed[key] = true;
    });
    setCollapsed(newCollapsed);
  }, [currentGroupKeys, collapsed]);

  // Filter steps based on search query
  const filteredSteps = useMemo(() => {
    if (!searchQuery.trim()) {
      return viewMode === 'category' ? stepsByCategory : stepsByPlugin;
    }

    const query = searchQuery.toLowerCase();
    const groups = viewMode === 'category' ? stepsByCategory : stepsByPlugin;
    const filtered: Record<string, StepTypeInfo[]> = {};

    Object.entries(groups).forEach(([groupName, steps]) => {
      const matchingSteps = steps.filter(
        (step) =>
          step.label.toLowerCase().includes(query) ||
          step.description.toLowerCase().includes(query) ||
          step.type.toLowerCase().includes(query)
      );

      if (matchingSteps.length > 0) {
        filtered[groupName] = matchingSteps;
      }
    });

    return filtered;
  }, [searchQuery, viewMode, stepsByCategory, stepsByPlugin]);

  // Toggle collapse state for a group
  const toggleCollapse = (groupName: string) => {
    setCollapsed((prev) => ({
      ...prev,
      [groupName]: !prev[groupName],
    }));
  };

  // Render individual step
  const renderStepType = (stepType: StepTypeInfo) => {
    const IconComponent = stepType.icon ? (Icons as any)[stepType.icon] : null;

    return (
      <div
        key={stepType.type}
        draggable
        onDragStart={(e) => onDragStart(e, stepType.type)}
        className="
          p-3 rounded-lg border border-gray-300 bg-white
          cursor-grab active:cursor-grabbing
          hover:border-gray-400 hover:shadow-md
          transition-all
        "
        style={{
          borderLeftColor: stepType.color,
          borderLeftWidth: '4px',
        }}
      >
        <div className="flex items-center gap-2 mb-1">
          {IconComponent && (
            <IconComponent
              className="w-4 h-4 flex-shrink-0"
              style={{ color: stepType.color }}
            />
          )}
          <div className="font-medium text-sm text-gray-900">{stepType.label}</div>
        </div>
        <div className="text-xs text-gray-500 line-clamp-2">
          {stepType.description}
        </div>
      </div>
    );
  };

  // Render a collapsible group
  const renderGroup = (groupName: string, steps: StepTypeInfo[]) => {
    const isCollapsed = collapsed[groupName] || false;
    const stepCount = steps.length;

    return (
      <div key={groupName} className="mb-4">
        <button
          onClick={() => toggleCollapse(groupName)}
          className="w-full flex items-center justify-between p-2 hover:bg-gray-100 rounded-md transition-colors group"
        >
          <div className="flex items-center gap-2">
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
            <h3 className="text-sm font-semibold text-gray-700 uppercase">
              {groupName}
            </h3>
            <span className="text-xs text-gray-500">({stepCount})</span>
          </div>
        </button>

        {!isCollapsed && (
          <div className="mt-2 ml-6 space-y-2">
            {steps.map(renderStepType)}
          </div>
        )}
      </div>
    );
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="h-full flex flex-col bg-gray-50 border-r border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">Step Palette</h2>
        </div>
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-sm text-gray-500">Loading step types...</div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="h-full flex flex-col bg-gray-50 border-r border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">Step Palette</h2>
        </div>
        <div className="flex-1 p-4">
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-xs text-red-900">
              <strong>Error:</strong> {error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 border-r border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 space-y-3 shrink-0">
        <h2 className="text-lg font-bold text-gray-900">Palette</h2>

        {/* Main Tabs: Steps, Shapes */}
        <div className="flex gap-1 bg-gray-200 rounded-lg p-1">
          <button
            onClick={() => setMainTab('steps')}
            className={`
              flex-1 flex items-center justify-center gap-1.5 px-2 py-2 rounded-md text-sm font-medium transition-colors
              ${
                mainTab === 'steps'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }
            `}
          >
            <Package size={16} />
            Steps
          </button>
          <button
            onClick={() => setMainTab('shapes')}
            className={`
              flex-1 flex items-center justify-center gap-1.5 px-2 py-2 rounded-md text-sm font-medium transition-colors
              ${
                mainTab === 'shapes'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }
            `}
          >
            <Shapes size={16} />
            Shapes
          </button>
        </div>

        {/* Search - only for steps */}
        {mainTab === 'steps' && (
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search steps..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        )}

        {/* View Mode Tabs - only for steps */}
        {mainTab === 'steps' && (
          <div className="flex items-center gap-2">
            <div className="flex gap-1 bg-gray-200 rounded-lg p-1 flex-1">
              <button
                onClick={() => setViewMode('category')}
                className={`
                  flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors
                  ${
                    viewMode === 'category'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }
                `}
              >
                <Layers className="w-3.5 h-3.5" />
                Category
              </button>
              <button
                onClick={() => setViewMode('plugin')}
                className={`
                  flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors
                  ${
                    viewMode === 'plugin'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }
                `}
              >
                <Package className="w-3.5 h-3.5" />
                Plugin
              </button>
            </div>
            {/* Collapse/Expand All Toggle */}
            <button
              onClick={allCollapsed ? expandAll : collapseAll}
              className="p-1.5 rounded-md bg-gray-200 hover:bg-gray-300 transition-colors"
              title={allCollapsed ? 'Expand all' : 'Collapse all'}
            >
              {allCollapsed ? (
                <ChevronsUpDown className="w-4 h-4 text-gray-600" />
              ) : (
                <ChevronsDownUp className="w-4 h-4 text-gray-600" />
              )}
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {mainTab === 'steps' ? (
          // Steps List
          <div className="p-4">
            {Object.keys(filteredSteps).length === 0 ? (
              <div className="text-center py-8">
                <p className="text-sm text-gray-500">
                  {searchQuery ? 'No steps found matching your search.' : 'No steps available.'}
                </p>
              </div>
            ) : (
              Object.entries(filteredSteps).map(([groupName, steps]) =>
                steps.length > 0 ? renderGroup(groupName, steps) : null
              )
            )}
          </div>
        ) : (
          // Shapes List
          <div className="p-4 space-y-2">
            {/* Rectangle */}
            <div
              draggable
              onDragStart={(e) => onShapeDragStart(e, 'rectangle')}
              className="
                p-3 rounded-lg border border-gray-300 bg-white
                cursor-grab active:cursor-grabbing
                hover:border-gray-400 hover:shadow-md
                transition-all
              "
              style={{
                borderLeftColor: '#3b82f6',
                borderLeftWidth: '4px',
              }}
            >
              <div className="flex items-center gap-2 mb-1">
                <Square className="w-4 h-4 flex-shrink-0 text-blue-600" />
                <div className="font-medium text-sm text-gray-900">Rectangle</div>
              </div>
              <div className="text-xs text-gray-500">
                Rounded rectangle shape for annotations
              </div>
            </div>

            {/* Ellipse */}
            <div
              draggable
              onDragStart={(e) => onShapeDragStart(e, 'ellipse')}
              className="
                p-3 rounded-lg border border-gray-300 bg-white
                cursor-grab active:cursor-grabbing
                hover:border-gray-400 hover:shadow-md
                transition-all
              "
              style={{
                borderLeftColor: '#8b5cf6',
                borderLeftWidth: '4px',
              }}
            >
              <div className="flex items-center gap-2 mb-1">
                <Circle className="w-4 h-4 flex-shrink-0 text-purple-600" />
                <div className="font-medium text-sm text-gray-900">Ellipse</div>
              </div>
              <div className="text-xs text-gray-500">
                Ellipse/circle shape for annotations
              </div>
            </div>

            {/* Text Box */}
            <div
              draggable
              onDragStart={(e) => onShapeDragStart(e, 'textbox')}
              className="
                p-3 rounded-lg border border-gray-300 bg-white
                cursor-grab active:cursor-grabbing
                hover:border-gray-400 hover:shadow-md
                transition-all
              "
              style={{
                borderLeftColor: '#22c55e',
                borderLeftWidth: '4px',
              }}
            >
              <div className="flex items-center gap-2 mb-1">
                <FileText className="w-4 h-4 flex-shrink-0 text-green-600" />
                <div className="font-medium text-sm text-gray-900">Text Box</div>
              </div>
              <div className="text-xs text-gray-500">
                Text container with markdown support
              </div>
            </div>

            {/* Sticky Note */}
            <div
              draggable
              onDragStart={(e) => onShapeDragStart(e, 'stickynote')}
              className="
                p-3 rounded-lg border border-gray-300 bg-white
                cursor-grab active:cursor-grabbing
                hover:border-gray-400 hover:shadow-md
                transition-all
              "
              style={{
                borderLeftColor: '#f59e0b',
                borderLeftWidth: '4px',
              }}
            >
              <div className="flex items-center gap-2 mb-1">
                <StickyNote className="w-4 h-4 flex-shrink-0 text-amber-600" />
                <div className="font-medium text-sm text-gray-900">Sticky Note</div>
              </div>
              <div className="text-xs text-gray-500">
                Quick note with markdown support
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tip */}
      <div className="p-4 border-t border-gray-200 shrink-0">
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs text-blue-900">
            <strong>Tip:</strong> {mainTab === 'steps'
              ? 'Drag and drop steps onto the canvas to build your graph.'
              : 'Drag and drop shapes onto the canvas for visual annotations.'}
          </p>
        </div>
      </div>
    </div>
  );
}
