import { MessageSquare, Settings, Wifi, WifiOff } from 'lucide-react';
import { useSettingsStore } from '@/stores/settingsStore';
import { useState } from 'react';
import SettingsModal from '@/components/modals/SettingsModal';

export default function Header() {
  const { runtime } = useSettingsStore();
  const [showSettings, setShowSettings] = useState(false);

  return (
    <>
      <header className="h-14 border-b border-border bg-background px-4 flex items-center justify-between">
        {/* Logo and title */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">GraphFlow Chat</h1>
          </div>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-4">
          {/* Connection status */}
          <div className="flex items-center gap-2 text-sm">
            {runtime.connected ? (
              <>
                <Wifi className="w-4 h-4 text-green-500" />
                <span className="text-muted-foreground">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-red-500" />
                <span className="text-muted-foreground">Disconnected</span>
              </>
            )}
          </div>

          {/* Settings button */}
          <button
            onClick={() => setShowSettings(true)}
            className="p-2 rounded-md hover:bg-muted transition-colors"
            title="Settings"
          >
            <Settings className="w-5 h-5 text-muted-foreground" />
          </button>

          {/* Link to Builder */}
          <a
            href="http://localhost:3000"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Open Builder
          </a>
        </div>
      </header>

      {/* Settings Modal */}
      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} />
      )}
    </>
  );
}
