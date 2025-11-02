import { useEffect } from 'react';
import * as Icons from 'lucide-react';
import { StepTypeInfo } from '@/types/graph';
import { usePluginStore } from '@/stores/pluginStore';

interface StepPaletteProps {
  onDragStart: (event: React.DragEvent, stepType: string) => void;
}

export default function StepPalette({ onDragStart }: StepPaletteProps) {
  const { stepTypes, isLoading, error, fetchStepTypes, getStepTypesByCategory } = usePluginStore();

  // Fetch step types on mount
  useEffect(() => {
    fetchStepTypes();
  }, [fetchStepTypes]);

  const stepsByCategory = getStepTypesByCategory();

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

  // Show loading state
  if (isLoading) {
    return (
      <div className="h-full overflow-y-auto bg-gray-50 border-r border-gray-200 p-4">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Step Palette</h2>
        <div className="flex items-center justify-center p-8">
          <div className="text-sm text-gray-500">Loading step types...</div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="h-full overflow-y-auto bg-gray-50 border-r border-gray-200 p-4">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Step Palette</h2>
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-xs text-red-900">
            <strong>Error:</strong> {error}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50 border-r border-gray-200 p-4">
      <h2 className="text-lg font-bold text-gray-900 mb-4">Step Palette</h2>

      {Object.entries(stepsByCategory).map(([category, steps]) => {
        if (steps.length === 0) return null;

        return (
          <div key={category} className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 uppercase mb-2">
              {category}
            </h3>
            <div className="space-y-2">
              {steps.map(renderStepType)}
            </div>
          </div>
        );
      })}

      <div className="mt-6 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-900">
          <strong>Tip:</strong> Drag and drop steps onto the canvas to build your graph.
        </p>
      </div>
    </div>
  );
}
