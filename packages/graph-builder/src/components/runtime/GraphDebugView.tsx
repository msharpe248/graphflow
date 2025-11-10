import { useEffect, useState, useRef } from 'react';
import { Play, Pause, ChevronRight, Square, Loader2, X, Link } from 'lucide-react';
import * as Icons from 'lucide-react';
import { useAgent, useRun, useDebugState, usePauseRun, useResumeRun, useStepRun, useSetBreakpoint, useClearBreakpoint, useMemory, useUpdateMemory } from '@/hooks/useRuntime';
import ReactFlow, { Background, Controls, Node, Edge, BackgroundVariant, Handle, Position } from 'reactflow';
import 'reactflow/dist/style.css';
import { GraphDefinition, Step } from '@/types/graph';
import { usePluginStore } from '@/stores/pluginStore';
import ShapeNode from '@/components/ShapeNode';
import { getEditorForSchema } from '@/components/editors';

interface GraphDebugViewProps {
  agentId: string;
  runId: string;
}

// Custom Debug Node component
function DebugNode({ data }: any) {
  const { step, stepTypeInfo, hasBreakpointBefore, hasBreakpointAfter, pausedAtBefore, pausedAtAfter, executionCount, isRunning, onBreakpointToggle } = data;

  const IconComponent = stepTypeInfo?.icon
    ? (Icons as any)[stepTypeInfo.icon]
    : null;

  const handleBeforeClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onBreakpointToggle(step.id, 'before');
  };

  const handleAfterClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onBreakpointToggle(step.id, 'after');
  };

  const isPausedAtAny = pausedAtBefore || pausedAtAfter;

  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 bg-white shadow-md
        min-w-[160px] max-w-[200px]
        cursor-pointer transition-all relative
        ${isRunning ? 'border-blue-500 ring-2 ring-blue-500/20 animate-pulse' : isPausedAtAny ? 'border-yellow-500 ring-2 ring-yellow-500/20' : (hasBreakpointBefore || hasBreakpointAfter) ? 'border-red-500 ring-2 ring-red-500/20' : 'border-gray-300 hover:border-gray-400'}
      `}
      style={{
        borderLeftColor: stepTypeInfo?.color || '#6b7280',
        borderLeftWidth: '4px',
        background: isPausedAtAny ? '#fef3c7' : (hasBreakpointBefore || hasBreakpointAfter) ? '#fee2e2' : '#fff',
        boxShadow: isRunning ? '0 0 0 3px rgba(59, 130, 246, 0.3)' : isPausedAtAny ? '0 0 0 3px rgba(234, 179, 8, 0.2)' : (hasBreakpointBefore || hasBreakpointAfter) ? '0 0 0 3px rgba(239, 68, 68, 0.2)' : undefined,
      }}
    >
      {/* Execution count badge */}
      {executionCount > 0 && (
        <div className="absolute -top-2 -right-2 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold z-10">
          {executionCount}
        </div>
      )}

      {/* Top Handle with Breakpoint (Before) */}
      {step.type !== 'start' && (
        <div
          className="absolute -top-3 left-1/2 -translate-x-1/2 cursor-pointer z-10"
          onClick={handleBeforeClick}
          title="Click to toggle breakpoint before step execution"
        >
          <Handle
            type="target"
            position={Position.Top}
            id="top"
            className={`!w-4 !h-4 !cursor-pointer transition-all ${
              pausedAtBefore
                ? '!bg-yellow-500 ring-4 ring-yellow-300 animate-pulse'
                : hasBreakpointBefore
                  ? '!bg-red-600 ring-2 ring-red-300'
                  : '!bg-gray-400 hover:!bg-gray-500'
            }`}
          />
        </div>
      )}

      {/* Bottom Handle with Breakpoint (After) */}
      {step.type !== 'output' && (
        <div
          className="absolute -bottom-3 left-1/2 -translate-x-1/2 cursor-pointer z-10"
          onClick={handleAfterClick}
          title="Click to toggle breakpoint after step execution"
        >
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom"
            className={`!w-4 !h-4 !cursor-pointer transition-all ${
              pausedAtAfter
                ? '!bg-yellow-500 ring-4 ring-yellow-300 animate-pulse'
                : hasBreakpointAfter
                  ? '!bg-red-600 ring-2 ring-red-300'
                  : '!bg-gray-400 hover:!bg-gray-500'
            }`}
          />
        </div>
      )}

      {/* Node content */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          {IconComponent && (
            <IconComponent
              className="w-4 h-4 flex-shrink-0"
              style={{ color: stepTypeInfo?.color || '#6b7280' }}
            />
          )}
          <div className="text-xs font-semibold text-gray-500 uppercase">
            {stepTypeInfo?.label || step.type}
          </div>
        </div>
        <div className="text-sm font-medium text-gray-900 truncate">
          {step.id}
        </div>
        {step.config && Object.keys(step.config).length > 0 && (
          <div className="text-xs text-gray-500 truncate">
            {Object.keys(step.config).length} config{Object.keys(step.config).length > 1 ? 's' : ''}
          </div>
        )}
      </div>
    </div>
  );
}

const nodeTypes = {
  debugNode: DebugNode,
  shapeNode: ShapeNode,
};

export default function GraphDebugView({ agentId, runId }: GraphDebugViewProps) {
  const { data: agent } = useAgent(agentId);
  const { data: run } = useRun(agentId, runId);

  // Only poll debug state when run is not completed
  const isActive = run?.status !== 'completed' && run?.status !== 'failed';
  const { data: debugState } = useDebugState(agentId, runId, isActive);
  const { data: memory } = useMemory(agentId, runId);
  const pauseRun = usePauseRun();
  const resumeRun = useResumeRun();
  const stepRun = useStepRun();
  const setBreakpoint = useSetBreakpoint();
  const clearBreakpoint = useClearBreakpoint();
  const updateMemory = useUpdateMemory();
  const getStepType = usePluginStore((state) => state.getStepType);

  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);

  // Track previous debug state to detect count changes
  const prevDebugStateRef = useRef<any>(null);

  // Build graph visualization from agent definition
  useEffect(() => {
    if (!agent) return;

    const graphDef = agent.graph_definition as GraphDefinition;
    if (!graphDef?.steps) return;

    const executionCounts = debugState?.step_execution_counts || run?.step_execution_counts || {};
    const breakpoints = debugState?.breakpoints || run?.breakpoints || [];
    const currentStepId = debugState?.current_step_id || run?.current_step_id;

    // Helper to toggle breakpoints
    const handleBreakpointToggle = (stepId: string, position: 'before' | 'after') => {
      const breakpointId = position === 'before' ? stepId : `${stepId}:after`;
      const hasBreakpoint = breakpoints.includes(breakpointId);

      if (hasBreakpoint) {
        clearBreakpoint.mutate({ agentId, runId, stepId: breakpointId });
      } else {
        setBreakpoint.mutate({ agentId, runId, stepId: breakpointId });
      }
    };

    // Determine if we're paused and where
    const isPaused = debugState?.status === 'paused';

    // Convert steps to ReactFlow nodes
    const stepNodes: Node[] = graphDef.steps.map((step, index) => {
      const hasBreakpointBefore = breakpoints.includes(step.id);
      const hasBreakpointAfter = breakpoints.includes(`${step.id}:after`);
      const isCurrent = currentStepId === step.id;
      const executionCount = executionCounts[step.id] || 0;
      const stepTypeInfo = getStepType(step.type);

      // Detect where we're paused
      // If we're paused at this step, we need to know if it's before or after
      let pausedAtBefore = false;
      let pausedAtAfter = false;

      if (isPaused && isCurrent) {
        // Compare current execution count to previous count to determine if we're before or after
        const currentCount = debugState?.step_execution_counts?.[step.id] || 0;
        const previousCount = prevDebugStateRef.current?.step_execution_counts?.[step.id] || 0;

        // If count increased since last poll, we just completed the step = paused after
        if (currentCount > previousCount) {
          pausedAtAfter = true;
        } else {
          // Count stayed the same = we haven't completed it yet = paused before
          pausedAtBefore = true;
        }
      }

      // Show green triangle only when actively running (Resume mode, not stepping)
      // In stepping mode, execution is too fast to see the triangle anyway
      const isRunning = isCurrent && debugState?.status === 'running';

      return {
        id: step.id,
        type: 'debugNode',
        position: step.position || { x: 100 + (index % 3) * 200, y: 100 + Math.floor(index / 3) * 150 },
        data: {
          step,
          stepTypeInfo,
          hasBreakpointBefore,
          hasBreakpointAfter,
          pausedAtBefore,
          pausedAtAfter,
          executionCount,
          isRunning,
          onBreakpointToggle: handleBreakpointToggle,
        },
        zIndex: 100, // Steps above shapes
        draggable: false,
        selectable: true,
      };
    });

    // Convert shapes to ReactFlow nodes
    const shapeNodes: Node[] = (graphDef.shapes || []).map((shape) => ({
      id: shape.id,
      type: 'shapeNode',
      position: shape.position,
      data: { shape },
      zIndex: shape.zIndex || 1, // Use shape's zIndex, default to 1 (behind steps at 100)
      draggable: false,
      selectable: false,
    }));

    // Combine and sort by zIndex (lower zIndex = behind, higher = in front)
    const allNodes = [...stepNodes, ...shapeNodes];
    const flowNodes = allNodes.sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0));

    // Convert edges
    const flowEdges: Edge[] = (graphDef.edges || []).map((edge) => ({
      id: edge.id,
      source: edge.from,
      target: edge.to,
      label: edge.condition,
      animated: currentStepId === edge.from,
      style: {
        stroke: currentStepId === edge.from ? '#3b82f6' : '#9ca3af',
        strokeWidth: 2,
      },
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);

    // Update previous debug state ref for next comparison
    prevDebugStateRef.current = debugState;
  }, [agent, debugState, run, getStepType]);

  const handlePause = () => {
    pauseRun.mutate({ agentId, runId });
  };

  const handleResume = () => {
    resumeRun.mutate({ agentId, runId });
  };

  const handleStep = () => {
    stepRun.mutate({ agentId, runId });
  };

  const handleNodeClick = (event: React.MouseEvent, node: Node) => {
    // Only handle step nodes, not shape nodes
    if (node.type !== 'debugNode') return;

    // Click selects the step
    setSelectedStepId(node.id);
  };

  const isPaused = debugState?.status === 'paused';
  const isRunning = run?.status === 'running' && debugState?.status !== 'paused';
  const isCompleted = run?.status === 'completed';

  return (
    <div className="h-full flex flex-col">
      {/* Control Bar */}
      <div className="bg-gray-50 border-b border-gray-200 p-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Status */}
          <div className="flex items-center gap-2">
            {isRunning && (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span className="text-sm font-medium text-blue-600">Running</span>
              </>
            )}
            {isPaused && (
              <>
                <Pause className="w-4 h-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-600">
                  Paused {debugState?.current_step_id ? `at: ${debugState.current_step_id}` : 'before start'}
                </span>
              </>
            )}
            {isCompleted && (
              <>
                <Square className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-green-600">Completed</span>
              </>
            )}
          </div>

          {/* Debug State */}
          {debugState && (
            <div className="text-xs text-gray-600 bg-white px-2 py-1 rounded border border-gray-200">
              Steps: {Object.keys(debugState.step_execution_counts || {}).length} |
              Breakpoints: {debugState.breakpoints?.length || 0}
            </div>
          )}
        </div>

        {/* Control Buttons */}
        <div className="flex items-center gap-2">
          {isPaused && (
            <>
              <button
                onClick={handleStep}
                disabled={stepRun.isPending}
                className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-sm font-medium transition-colors"
                title="Execute one step (F10)"
              >
                <ChevronRight className="w-4 h-4" />
                Step
              </button>
              <button
                onClick={handleResume}
                disabled={resumeRun.isPending}
                className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-sm font-medium transition-colors"
                title="Resume to next breakpoint (F8)"
              >
                <Play className="w-4 h-4" />
                Resume
              </button>
            </>
          )}
          {isRunning && (
            <button
              onClick={handlePause}
              disabled={pauseRun.isPending}
              className="flex items-center gap-1 px-3 py-1.5 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50 text-sm font-medium transition-colors"
              title="Pause execution"
            >
              <Pause className="w-4 h-4" />
              Pause
            </button>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border-b border-blue-200 px-3 py-2">
        <p className="text-xs text-blue-800">
          <strong>Click nodes</strong> to view properties • <strong>Click connection points</strong> (top = before, bottom = after) to toggle breakpoints •
          Use <strong>Step</strong> to execute one step at a time • <strong>Resume</strong> runs until next breakpoint
        </p>
      </div>

      {/* Main Content - Graph and Properties */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph Canvas */}
        <div className="flex-1 bg-gray-50">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodeClick={handleNodeClick}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            attributionPosition="bottom-left"
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={true}
          >
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
            <Controls />
          </ReactFlow>
        </div>

        {/* Properties Panel */}
        {selectedStepId && (() => {
          const graphDef = agent?.graph_definition as GraphDefinition;
          const selectedStep = graphDef?.steps.find(s => s.id === selectedStepId);
          const stepTypeInfo = selectedStep ? getStepType(selectedStep.type) : null;

          if (!selectedStep || !stepTypeInfo) return null;

          // Check if paused to allow editing
          const canEdit = isPaused;

          // Handler to update memory value
          const handleMemoryUpdate = (binding: string, value: any) => {
            if (!canEdit || !memory) return;

            const memPath = binding.replace('{memory.', '').replace('}', '');

            // Determine namespace and key using same logic as reading
            let namespace: string;
            let key: string;

            const knownNamespaces = ['inputs', 'outputs', 'intermediate', 'config', 'environment', 'secrets'];
            const firstPart = memPath.split('.')[0];

            if (knownNamespaces.includes(firstPart)) {
              // Has explicit namespace
              const parts = memPath.split('.');
              namespace = parts[0];
              key = parts.slice(1).join('.');
            } else {
              // No namespace prefix - determine by looking in memory
              if (memory.inputs && memPath in memory.inputs) {
                namespace = 'inputs';
                key = memPath;
              } else if (memory.intermediate && memPath in memory.intermediate) {
                namespace = 'intermediate';
                key = memPath;
              } else if (memory.outputs && memPath in memory.outputs) {
                namespace = 'outputs';
                key = memPath;
              } else {
                // Default to inputs namespace
                namespace = 'inputs';
                key = memPath;
              }
            }

            updateMemory.mutate({
              agentId,
              runId,
              namespace,
              key,
              value
            });
          };

          return (
            <div className="w-96 shrink-0 bg-gray-50 border-l border-gray-200 flex flex-col">
              {/* Header */}
              <div className="bg-white border-b border-gray-200 p-3 flex items-center justify-between">
                <h2 className="text-sm font-bold text-gray-900">Step Properties</h2>
                <button
                  onClick={() => setSelectedStepId(null)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {/* Step Info */}
                <div>
                  <div
                    className="inline-block px-3 py-1 rounded-full text-sm font-medium text-white"
                    style={{ backgroundColor: stepTypeInfo.color }}
                  >
                    {stepTypeInfo.label}
                  </div>
                  <p className="text-xs text-gray-600 mt-2">{stepTypeInfo.description}</p>
                  <p className="text-sm font-mono text-gray-900 mt-2">{selectedStep.id}</p>
                </div>

                {/* Configuration Inputs */}
                {selectedStep.config && Object.keys(selectedStep.config).length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Inputs</h3>
                    <div className="space-y-3">
                      {Object.entries(selectedStep.config).map(([key, value]) => {
                        const schema = stepTypeInfo.configSchema?.properties?.[key];
                        const isMemoryBinding = typeof value === 'string' && value.startsWith('{memory.') && value.endsWith('}');

                        // Extract actual memory value for bindings
                        let actualValue = value;
                        let memoryNotFound = false;
                        if (isMemoryBinding) {
                          if (!memory) {
                            actualValue = undefined;
                            memoryNotFound = true;
                          } else {
                            const memPath = value.replace('{memory.', '').replace('}', '');

                            // Determine namespace and key
                            let namespace: string;
                            let memKey: string;

                            // Check if memPath starts with a known namespace
                            const knownNamespaces = ['inputs', 'outputs', 'intermediate', 'config', 'environment', 'secrets'];
                            const firstPart = memPath.split('.')[0];

                            if (knownNamespaces.includes(firstPart)) {
                              // Has explicit namespace: {memory.inputs.url}
                              const parts = memPath.split('.');
                              namespace = parts[0];
                              memKey = parts.slice(1).join('.');
                            } else {
                              // No namespace prefix - determine by looking in memory
                              // First check inputs, then intermediate
                              if (memory.inputs && memPath in memory.inputs) {
                                namespace = 'inputs';
                                memKey = memPath;
                              } else if (memory.intermediate && memPath in memory.intermediate) {
                                namespace = 'intermediate';
                                memKey = memPath;
                              } else if (memory.outputs && memPath in memory.outputs) {
                                namespace = 'outputs';
                                memKey = memPath;
                              } else {
                                // Default to inputs namespace
                                namespace = 'inputs';
                                memKey = memPath;
                              }
                            }

                            actualValue = memory[namespace]?.[memKey];

                            // Debug: log what we're looking for vs what we found
                            console.log('Memory lookup:', {
                              binding: value,
                              memPath,
                              namespace,
                              memKey,
                              found: actualValue,
                              memoryExists: !!memory,
                              namespaceExists: !!memory[namespace],
                              allMemory: memory
                            });
                          }
                        }

                        // Generate label from key or use title from schema
                        const label = schema?.title || key.split('_').map((word: string) =>
                          word.charAt(0).toUpperCase() + word.slice(1)
                        ).join(' ');

                        return (
                          <div key={key}>
                            <div className="flex items-center justify-between mb-1">
                              <label className="block text-xs font-medium text-gray-600">
                                {label}
                              </label>
                              {isMemoryBinding && (
                                <div className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                                  <Link className="w-3 h-3" />
                                  {value} {canEdit ? '(editable)' : '(view only)'}
                                </div>
                              )}
                            </div>
                            {isMemoryBinding ? (
                              <div className="mb-2">
                                <label className="block text-xs font-medium text-gray-600 mb-1">
                                  Current Value {canEdit && <span className="text-green-600">(editable while paused)</span>}
                                </label>
                                {memoryNotFound ? (
                                  <div className="bg-yellow-50 border border-yellow-200 rounded p-2 text-xs text-yellow-800">
                                    Memory not loaded yet...
                                  </div>
                                ) : actualValue === undefined ? (
                                  <div className="bg-gray-50 border border-gray-200 rounded p-2 text-xs text-gray-600">
                                    Value not set (undefined)
                                  </div>
                                ) : (() => {
                                  // Get the appropriate editor for this schema
                                  const editorConfig = getEditorForSchema(schema || {});
                                  const EditorComponent = editorConfig.component;

                                  return (
                                    <div className={canEdit ? '' : 'pointer-events-none opacity-75'}>
                                      <EditorComponent
                                        value={actualValue}
                                        onChange={(newValue) => canEdit ? handleMemoryUpdate(value, newValue) : undefined}
                                        schema={schema || {}}
                                      />
                                    </div>
                                  );
                                })()}
                              </div>
                            ) : (() => {
                              // Get the appropriate editor for this schema (read-only, not bound)
                              const editorConfig = getEditorForSchema(schema || {});
                              const EditorComponent = editorConfig.component;

                              return (
                                <div className="pointer-events-none opacity-75">
                                  <EditorComponent
                                    value={value ?? schema?.default}
                                    onChange={() => {}} // Read-only (not bound to memory)
                                    schema={schema || {}}
                                  />
                                </div>
                              );
                            })()}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Outputs */}
                {stepTypeInfo.outputsSchema?.properties && Object.keys(stepTypeInfo.outputsSchema.properties).length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Outputs</h3>
                    <div className="space-y-3">
                      {Object.entries(stepTypeInfo.outputsSchema.properties).map(([outputKey, outputSchema]: [string, any]) => {
                        // Get the memory location from step.outputs
                        const outputMapping = selectedStep.outputs?.[outputKey] || `{memory.${outputKey}}`;
                        const isOutputBound = typeof outputMapping === 'string' && outputMapping.startsWith('{memory.') && outputMapping.endsWith('}');

                        // Extract actual output value from memory
                        let outputValue;
                        if (isOutputBound && memory) {
                          const memPath = outputMapping.replace('{memory.', '').replace('}', '');

                          // Determine namespace and key
                          let namespace: string;
                          let memKey: string;

                          // Check if memPath starts with a known namespace
                          const knownNamespaces = ['inputs', 'outputs', 'intermediate', 'config', 'environment', 'secrets'];
                          const firstPart = memPath.split('.')[0];

                          if (knownNamespaces.includes(firstPart)) {
                            // Has explicit namespace: {memory.outputs.response}
                            const parts = memPath.split('.');
                            namespace = parts[0];
                            memKey = parts.slice(1).join('.');
                          } else {
                            // No namespace prefix - determine by looking in memory
                            if (memory.outputs && memPath in memory.outputs) {
                              namespace = 'outputs';
                              memKey = memPath;
                            } else if (memory.intermediate && memPath in memory.intermediate) {
                              namespace = 'intermediate';
                              memKey = memPath;
                            } else {
                              // Default to outputs namespace for output mappings
                              namespace = 'outputs';
                              memKey = memPath;
                            }
                          }

                          outputValue = memory[namespace]?.[memKey];
                        }

                        const typeLabel = outputSchema.type || 'any';

                        return (
                          <div key={outputKey} className="bg-green-50 border border-green-200 rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-semibold text-green-900">
                                  {outputKey}
                                </span>
                                <span className="text-xs text-green-600 bg-green-100 px-2 py-0.5 rounded">
                                  {typeLabel}
                                </span>
                              </div>
                              {isOutputBound && (
                                <div className="flex items-center gap-1 text-xs text-green-600 bg-green-100 px-1.5 py-0.5 rounded">
                                  <Link className="w-3 h-3" />
                                  {outputMapping} {canEdit ? '(editable)' : '(view only)'}
                                </div>
                              )}
                            </div>
                            {outputSchema.description && (
                              <p className="text-xs text-green-700 mb-2">
                                {outputSchema.description}
                              </p>
                            )}
                            {isOutputBound && (
                              <div>
                                <label className="block text-xs font-medium text-green-700 mb-1">
                                  Current Value {canEdit && <span className="text-green-600">(editable while paused)</span>}
                                </label>
                                {(() => {
                                  // Get the appropriate editor for this output schema
                                  const editorConfig = getEditorForSchema(outputSchema);
                                  const EditorComponent = editorConfig.component;

                                  return (
                                    <div className={canEdit ? '' : 'pointer-events-none opacity-75'}>
                                      <EditorComponent
                                        value={outputValue !== undefined ? outputValue : (outputSchema.default ?? '')}
                                        onChange={(newValue) => canEdit ? handleMemoryUpdate(outputMapping, newValue) : undefined}
                                        schema={outputSchema}
                                      />
                                    </div>
                                  );
                                })()}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })()}
      </div>

      {/* Legend */}
      <div className="bg-white border-t border-gray-200 px-3 py-2 flex items-center gap-6 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-500 bg-blue-50 rounded"></div>
          <span className="text-gray-600">Current Step</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-red-500 bg-red-50 rounded"></div>
          <span className="text-gray-600">Breakpoint</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border border-gray-300 bg-white rounded"></div>
          <span className="text-gray-600">Pending</span>
        </div>
      </div>
    </div>
  );
}
