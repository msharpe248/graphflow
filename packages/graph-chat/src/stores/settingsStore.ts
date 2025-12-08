import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface RuntimeConnection {
  host: string;
  port: number;
  protocol: 'http' | 'https';
  connected: boolean;
  lastChecked: number | null;
}

interface SettingsStore {
  // Runtime connection
  runtime: RuntimeConnection;

  // Actions
  setRuntimeEndpoint: (host: string, port: number, protocol?: 'http' | 'https') => void;
  getApiBaseUrl: () => string;
  checkConnection: () => Promise<boolean>;
  setConnected: (connected: boolean) => void;
}

const DEFAULT_HOST = 'localhost';
const DEFAULT_PORT = 8000;
const DEFAULT_PROTOCOL = 'http';

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      // Initial state
      runtime: {
        host: DEFAULT_HOST,
        port: DEFAULT_PORT,
        protocol: DEFAULT_PROTOCOL,
        connected: false,
        lastChecked: null,
      },

      // Set runtime endpoint
      setRuntimeEndpoint: (host, port, protocol = 'http') => {
        set({
          runtime: {
            host,
            port,
            protocol,
            connected: false,
            lastChecked: null,
          },
        });
      },

      // Get full API base URL
      getApiBaseUrl: () => {
        const { runtime } = get();
        return `${runtime.protocol}://${runtime.host}:${runtime.port}`;
      },

      // Check if runtime is reachable
      checkConnection: async () => {
        const baseUrl = get().getApiBaseUrl();

        try {
          const response = await fetch(`${baseUrl}/api/v1/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(5000), // 5 second timeout
          });

          const isConnected = response.ok;

          set({
            runtime: {
              ...get().runtime,
              connected: isConnected,
              lastChecked: Date.now(),
            },
          });

          return isConnected;
        } catch (error) {
          set({
            runtime: {
              ...get().runtime,
              connected: false,
              lastChecked: Date.now(),
            },
          });
          return false;
        }
      },

      // Manually set connection status
      setConnected: (connected) => {
        set({
          runtime: {
            ...get().runtime,
            connected,
            lastChecked: Date.now(),
          },
        });
      },
    }),
    {
      name: 'graphflow-chat-settings', // localStorage key (different from builder)
      partialize: (state) => ({
        runtime: {
          host: state.runtime.host,
          port: state.runtime.port,
          protocol: state.runtime.protocol,
          // Don't persist connection status
          connected: false,
          lastChecked: null,
        },
      }),
    }
  )
);
