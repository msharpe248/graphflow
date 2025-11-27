import { useState } from 'react';
import Toolbar from './Toolbar';
import StepPalette from './StepPalette';
import GraphCanvas from './GraphCanvas';
import PropertiesPanel from './PropertiesPanel';
import MemoryPanel from './MemoryPanel';
import SettingsModal from './SettingsModal';

export default function BuilderView() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [propertiesCollapsed, setPropertiesCollapsed] = useState(false);
  const [memoryCollapsed, setMemoryCollapsed] = useState(false);

  const onDragStart = (event: React.DragEvent, stepType: string) => {
    event.dataTransfer.setData('application/reactflow', stepType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const onShapeDragStart = (event: React.DragEvent, shapeType: 'rectangle' | 'ellipse') => {
    event.dataTransfer.setData('application/shape', shapeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  // Determine height classes based on collapse states
  const getPropertiesHeight = () => {
    if (propertiesCollapsed) return 'h-auto';
    if (memoryCollapsed) return 'flex-1';
    return 'h-1/2';
  };

  const getMemoryHeight = () => {
    if (memoryCollapsed) return 'h-auto';
    if (propertiesCollapsed) return 'flex-1';
    return 'h-1/2';
  };

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <Toolbar onOpenSettings={() => setSettingsOpen(true)} />

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar - Step palette */}
        <div className="w-72 shrink-0">
          <StepPalette onDragStart={onDragStart} onShapeDragStart={onShapeDragStart} />
        </div>

        {/* Center - Canvas */}
        <div className="flex-1">
          <GraphCanvas />
        </div>

        {/* Right sidebar - Properties and Memory */}
        <div className="w-96 shrink-0 flex flex-col overflow-hidden">
          {/* Top: Properties Panel */}
          <div className={`${getPropertiesHeight()} ${!propertiesCollapsed ? 'min-h-0' : ''}`}>
            <PropertiesPanel
              isCollapsed={propertiesCollapsed}
              setIsCollapsed={setPropertiesCollapsed}
            />
          </div>

          {/* Bottom: Memory Panel */}
          <div className={`${getMemoryHeight()} ${!memoryCollapsed ? 'min-h-0' : ''} border-t border-gray-200`}>
            <MemoryPanel
              isCollapsed={memoryCollapsed}
              setIsCollapsed={setMemoryCollapsed}
            />
          </div>
        </div>
      </div>

      {/* Settings modal */}
      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
