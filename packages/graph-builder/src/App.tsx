import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Wrench, Activity, Circle } from 'lucide-react';
import BuilderView from './components/BuilderView';
import RuntimeView from './components/runtime/RuntimeView';
import RuntimeConnectionModal from './components/RuntimeConnectionModal';
import { useSettingsStore } from './stores/settingsStore';
import { useAppStore } from './stores/appStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export default function App() {
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const { runtime, checkConnection, getApiBaseUrl } = useSettingsStore();
  const { activeView, setActiveView } = useAppStore();

  // Check connection on mount and periodically
  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, [checkConnection]);

  return (
    <QueryClientProvider client={queryClient}>
      <div className="h-screen w-screen flex flex-col overflow-hidden">
        {/* Main navigation */}
        <div className="h-12 bg-primary text-primary-foreground flex items-center px-4 gap-2 shrink-0">
          <div className="flex items-center gap-2 flex-1">
            <div className="text-xl font-bold">GraphFlow</div>
            <div className="text-xs opacity-75">Visual Agent Builder</div>
          </div>

          {/* Connection Status */}
          <button
            onClick={() => setShowConnectionModal(true)}
            className="flex items-center gap-2 px-3 py-1 bg-primary-foreground/10 rounded-md hover:bg-primary-foreground/20 transition-colors"
            title="Click to configure runtime connection"
          >
            <Circle
              className={`w-2 h-2 fill-current ${
                runtime.connected ? 'text-green-400' : 'text-red-400'
              }`}
            />
            <span className="text-xs font-medium">
              {runtime.connected ? 'Connected' : 'Disconnected'}
            </span>
            <span className="text-xs opacity-60 hidden sm:inline">
              {getApiBaseUrl().replace(/^https?:\/\//, '')}
            </span>
          </button>

          {/* View switcher */}
          <div className="flex gap-1 bg-primary-foreground/10 rounded-lg p-1">
            <button
              onClick={() => setActiveView('builder', undefined)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors
                ${
                  activeView === 'builder'
                    ? 'bg-primary-foreground text-primary'
                    : 'text-primary-foreground/80 hover:text-primary-foreground'
                }
              `}
            >
              <Wrench className="w-4 h-4" />
              Builder
            </button>
            <button
              onClick={() => setActiveView('runtime', undefined)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors
                ${
                  activeView === 'runtime'
                    ? 'bg-primary-foreground text-primary'
                    : 'text-primary-foreground/80 hover:text-primary-foreground'
                }
              `}
            >
              <Activity className="w-4 h-4" />
              Runtime
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeView === 'builder' ? <BuilderView /> : <RuntimeView />}
        </div>

        {/* Runtime Connection Modal */}
        <RuntimeConnectionModal
          isOpen={showConnectionModal}
          onClose={() => setShowConnectionModal(false)}
        />
      </div>
    </QueryClientProvider>
  );
}
