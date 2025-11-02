import { useState } from 'react';
import Toolbar from './Toolbar';
import StepPalette from './StepPalette';
import GraphCanvas from './GraphCanvas';
import PropertiesPanel from './PropertiesPanel';
import SettingsModal from './SettingsModal';

export default function BuilderView() {
  const [settingsOpen, setSettingsOpen] = useState(false);

  const onDragStart = (event: React.DragEvent, stepType: string) => {
    event.dataTransfer.setData('application/reactflow', stepType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <Toolbar onOpenSettings={() => setSettingsOpen(true)} />

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar - Step palette */}
        <div className="w-64 shrink-0">
          <StepPalette onDragStart={onDragStart} />
        </div>

        {/* Center - Canvas */}
        <div className="flex-1">
          <GraphCanvas />
        </div>

        {/* Right sidebar - Properties */}
        <div className="w-80 shrink-0">
          <PropertiesPanel />
        </div>
      </div>

      {/* Settings modal */}
      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
