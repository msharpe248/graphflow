import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Wrench, Activity } from 'lucide-react';
import BuilderView from './components/BuilderView';
import RuntimeView from './components/runtime/RuntimeView';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

type View = 'builder' | 'runtime';

export default function App() {
  const [activeView, setActiveView] = useState<View>('builder');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="h-screen w-screen flex flex-col overflow-hidden">
        {/* Main navigation */}
        <div className="h-12 bg-primary text-primary-foreground flex items-center px-4 gap-2 shrink-0">
          <div className="flex items-center gap-2 flex-1">
            <div className="text-xl font-bold">GraphFlow</div>
            <div className="text-xs opacity-75">Visual Agent Builder</div>
          </div>

          {/* View switcher */}
          <div className="flex gap-1 bg-primary-foreground/10 rounded-lg p-1">
            <button
              onClick={() => setActiveView('builder')}
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
              onClick={() => setActiveView('runtime')}
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
      </div>
    </QueryClientProvider>
  );
}
