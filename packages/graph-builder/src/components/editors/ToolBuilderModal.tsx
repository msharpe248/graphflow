import { useState, useEffect, useMemo } from 'react';
import { X, ChevronRight, ChevronLeft, Check, AlertCircle, Wrench, Info } from 'lucide-react';
import {
  ToolDefinition,
  ToolPropertyMapping,
  createEmptyToolDefinition,
} from '@/types/tool';
import { usePluginStore } from '@/stores/pluginStore';
import { useGraphStore } from '@/stores/graphStore';
import { StepTypeInfo } from '@/types/graph';
import PropertyMappingCard from './PropertyMappingCard';

interface ToolBuilderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (tool: ToolDefinition) => void;
  initialTool?: ToolDefinition;
  title?: string;
  stepId?: string;  // Parent step ID for generating memory bindings
}

type Step = 'basic' | 'step-select' | 'mappings';

export default function ToolBuilderModal({
  isOpen,
  onClose,
  onSave,
  initialTool,
  title = 'Create Tool',
  stepId,
}: ToolBuilderModalProps) {
  const { stepTypes } = usePluginStore();
  const { memory, setMemoryValue } = useGraphStore();

  // Current wizard step
  const [currentStep, setCurrentStep] = useState<Step>('basic');

  // Tool being edited
  const [tool, setTool] = useState<ToolDefinition>(
    initialTool || createEmptyToolDefinition()
  );

  // Validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Filter for step selection
  const [stepFilter, setStepFilter] = useState('');

  // Reset when modal opens/closes or initial tool changes
  useEffect(() => {
    if (isOpen) {
      setTool(initialTool || createEmptyToolDefinition());
      setCurrentStep('basic');
      setErrors({});
      setStepFilter('');
    }
  }, [isOpen, initialTool]);

  // Get tool-eligible steps
  const toolEligibleSteps = useMemo(() => {
    return Object.values(stepTypes).filter(
      (step: StepTypeInfo) => step.can_be_tool === true
    );
  }, [stepTypes]);

  // Filter steps based on search
  const filteredSteps = useMemo(() => {
    if (!stepFilter.trim()) return toolEligibleSteps;
    const query = stepFilter.toLowerCase();
    return toolEligibleSteps.filter(
      (step) =>
        step.label.toLowerCase().includes(query) ||
        step.description.toLowerCase().includes(query) ||
        step.type.toLowerCase().includes(query)
    );
  }, [toolEligibleSteps, stepFilter]);

  // Get selected step type info
  const selectedStepInfo = useMemo(() => {
    if (!tool.source_step_type) return null;
    return stepTypes[tool.source_step_type];
  }, [tool.source_step_type, stepTypes]);

  // Initialize property mappings when step type changes
  useEffect(() => {
    if (selectedStepInfo?.configSchema?.properties && tool.property_mappings.length === 0) {
      const mappings: ToolPropertyMapping[] = Object.entries(
        selectedStepInfo.configSchema.properties
      ).map(([key, schema]: [string, any]) => {
        // Auto-create memory binding if tool name and stepId are set
        let runtimeValue = '';
        if (tool.name && stepId) {
          const memoryKey = `${stepId}.${tool.name}.${key}`;
          runtimeValue = `{memory.${memoryKey}}`;

          // Create the memory location if it doesn't exist
          if (!memory.intermediate[memoryKey]) {
            setMemoryValue('intermediate', memoryKey, {
              type: schema.type || 'string',
              description: `Runtime value for ${stepId}.${tool.name}.${key}`,
              default: schema.default,
            });
          }
        }

        return {
          source_property: key,
          visibility: 'runtime' as const,
          runtime_value: runtimeValue,
          llm_parameter_name: key,
          llm_description: schema.description || '',
          llm_schema: { type: schema.type || 'string' },
          required: schema.required || false,
        };
      });
      setTool((prev) => ({ ...prev, property_mappings: mappings }));
    }
  }, [selectedStepInfo, tool.property_mappings.length, tool.name, stepId, memory.intermediate, setMemoryValue]);

  // Validate current step
  const validateStep = (step: Step): boolean => {
    const newErrors: Record<string, string> = {};

    if (step === 'basic') {
      if (!tool.name.trim()) {
        newErrors.name = 'Tool name is required';
      } else if (!/^[a-z][a-z0-9_]*$/.test(tool.name)) {
        newErrors.name = 'Tool name must start with lowercase letter and contain only lowercase letters, numbers, and underscores';
      }
      if (!tool.description.trim()) {
        newErrors.description = 'Tool description is required';
      }
    }

    if (step === 'step-select') {
      if (!tool.source_step_type) {
        newErrors.source_step_type = 'Please select a source step';
      }
    }

    if (step === 'mappings') {
      // Check that at least one property is LLM-controlled
      const llmParams = tool.property_mappings.filter((m) => m.visibility === 'llm');
      if (llmParams.length === 0) {
        newErrors.mappings = 'At least one property must be LLM-controlled';
      }
      // Runtime properties without values will get auto-created bindings on save
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Navigation
  const goNext = () => {
    if (!validateStep(currentStep)) return;

    if (currentStep === 'basic') {
      setCurrentStep('step-select');
    } else if (currentStep === 'step-select') {
      setCurrentStep('mappings');
    }
  };

  const goBack = () => {
    if (currentStep === 'step-select') {
      setCurrentStep('basic');
    } else if (currentStep === 'mappings') {
      setCurrentStep('step-select');
    }
  };

  // Check if a value is a memory binding
  const isMemoryBinding = (value: string | undefined): boolean => {
    if (!value) return false;
    return (
      value.startsWith('{memory.') ||
      value.startsWith('{config.') ||
      value.startsWith('{env.') ||
      value.startsWith('{secrets.')
    );
  };

  const handleSave = () => {
    if (!validateStep('mappings')) return;

    // Auto-create memory bindings for runtime properties without bindings
    const updatedMappings = tool.property_mappings.map((mapping) => {
      // Skip LLM-controlled properties
      if (mapping.visibility === 'llm') return mapping;

      // Skip if already has a memory binding
      if (isMemoryBinding(mapping.runtime_value)) return mapping;

      // Skip if has a constant value set
      if (mapping.runtime_value && mapping.runtime_value.trim()) return mapping;

      // Create a new intermediate memory location
      const memoryKey = stepId ? `${stepId}.${tool.name}.${mapping.source_property}` : `${tool.name}.${mapping.source_property}`;

      // Get the schema for this property to determine type and default
      const schema = selectedStepInfo?.configSchema?.properties?.[mapping.source_property] || {};

      // Create the memory location if it doesn't exist
      if (!memory.intermediate[memoryKey]) {
        setMemoryValue('intermediate', memoryKey, {
          type: schema.type || 'string',
          description: `Runtime value for ${memoryKey}`,
          default: schema.default,
        });
      }

      // Update the mapping with the binding
      return {
        ...mapping,
        runtime_value: `{memory.${memoryKey}}`,
      };
    });

    // Save the tool with updated mappings
    onSave({ ...tool, property_mappings: updatedMappings });
    onClose();
  };

  // Update property mapping
  const updateMapping = (index: number, updates: Partial<ToolPropertyMapping>) => {
    setTool((prev) => ({
      ...prev,
      property_mappings: prev.property_mappings.map((m, i) =>
        i === index ? { ...m, ...updates } : m
      ),
    }));
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Wrench className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-md transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
          <div className="flex items-center justify-center gap-2">
            {(['basic', 'step-select', 'mappings'] as Step[]).map((step, index) => (
              <div key={step} className="flex items-center">
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                    ${currentStep === step
                      ? 'bg-blue-600 text-white'
                      : index < ['basic', 'step-select', 'mappings'].indexOf(currentStep)
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-200 text-gray-600'}
                  `}
                >
                  {index < ['basic', 'step-select', 'mappings'].indexOf(currentStep) ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    index + 1
                  )}
                </div>
                {index < 2 && (
                  <div
                    className={`w-12 h-0.5 mx-2 ${
                      index < ['basic', 'step-select', 'mappings'].indexOf(currentStep)
                        ? 'bg-green-500'
                        : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-center mt-2 text-xs text-gray-500">
            {currentStep === 'basic' && 'Step 1: Basic Info'}
            {currentStep === 'step-select' && 'Step 2: Select Source Step'}
            {currentStep === 'mappings' && 'Step 3: Configure Properties'}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Step 1: Basic Info */}
          {currentStep === 'basic' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tool Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={tool.name}
                  onChange={(e) => setTool((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="search_recipes"
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.name ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.name ? (
                  <p className="mt-1 text-xs text-red-600">{errors.name}</p>
                ) : (
                  <p className="mt-1 text-xs text-gray-500">
                    Use lowercase letters, numbers, and underscores (e.g., search_web, get_user_profile)
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={tool.description}
                  onChange={(e) => setTool((prev) => ({ ...prev, description: e.target.value }))}
                  placeholder="Search for recipes matching the given ingredients and cuisine type..."
                  rows={4}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.description ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.description ? (
                  <p className="mt-1 text-xs text-red-600">{errors.description}</p>
                ) : (
                  <p className="mt-1 text-xs text-gray-500">
                    Describe when and how the LLM should use this tool. Use domain-specific terminology.
                  </p>
                )}
              </div>

              {selectedStepInfo && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-md flex items-start gap-2">
                  <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-900">
                    <strong>Default:</strong> {selectedStepInfo.description}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Step Selection */}
          {currentStep === 'step-select' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Source Step <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={stepFilter}
                  onChange={(e) => setStepFilter(e.target.value)}
                  placeholder="Search steps..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-3"
                />
              </div>

              {errors.source_step_type && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  <span className="text-sm text-red-900">{errors.source_step_type}</span>
                </div>
              )}

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {filteredSteps.map((step) => (
                  <button
                    key={step.type}
                    onClick={() => {
                      setTool((prev) => ({
                        ...prev,
                        source_step_type: step.type,
                        property_mappings: [], // Reset mappings when step changes
                      }));
                    }}
                    className={`w-full p-3 text-left rounded-lg border transition-all ${
                      tool.source_step_type === step.type
                        ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900">{step.label}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{step.description}</div>
                      </div>
                      {tool.source_step_type === step.type && (
                        <Check className="w-5 h-5 text-blue-600" />
                      )}
                    </div>
                  </button>
                ))}
              </div>

              {filteredSteps.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No matching steps found
                </div>
              )}
            </div>
          )}

          {/* Step 3: Property Mappings */}
          {currentStep === 'mappings' && selectedStepInfo && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">Configure Properties</h4>
                  <p className="text-sm text-gray-500">
                    Choose which properties the LLM controls vs runtime provides
                  </p>
                </div>
              </div>

              {errors.mappings && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  <span className="text-sm text-red-900">{errors.mappings}</span>
                </div>
              )}

              <div className="space-y-3">
                {tool.property_mappings.map((mapping, index) => {
                  const schema = selectedStepInfo.configSchema?.properties?.[mapping.source_property] || {};
                  return (
                    <PropertyMappingCard
                      key={mapping.source_property}
                      mapping={mapping}
                      schema={schema}
                      onChange={(updates) => updateMapping(index, updates)}
                      error={errors[`mapping_${mapping.source_property}`]}
                      toolName={tool.name}
                      stepId={stepId}
                    />
                  );
                })}
              </div>

              {tool.property_mappings.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No configurable properties for this step
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 flex justify-between">
          <button
            onClick={currentStep === 'basic' ? onClose : goBack}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors flex items-center gap-1"
          >
            {currentStep === 'basic' ? (
              'Cancel'
            ) : (
              <>
                <ChevronLeft className="w-4 h-4" />
                Back
              </>
            )}
          </button>

          {currentStep === 'mappings' ? (
            <button
              onClick={handleSave}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors flex items-center gap-1"
            >
              <Check className="w-4 h-4" />
              Save Tool
            </button>
          ) : (
            <button
              onClick={goNext}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors flex items-center gap-1"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
