import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface RuntimeConnection {
  host: string;
  port: number;
  protocol: 'http' | 'https';
  insecureMode: boolean; // Skip SSL verification for self-signed certs
  connected: boolean;
  lastChecked: number | null;
}

interface SettingsStore {
  // Runtime connection
  runtime: RuntimeConnection;

  // Actions
  setRuntimeEndpoint: (host: string, port: number, protocol?: 'http' | 'https', insecureMode?: boolean) => void;
  setInsecureMode: (insecure: boolean) => void;
  getApiBaseUrl: () => string;
  checkConnection: () => Promise<boolean>;
  setConnected: (connected: boolean) => void;
}

const DEFAULT_HOST = 'localhost';
const DEFAULT_PORT = 8000;
const DEFAULT_PROTOCOL = 'https';
const DEFAULT_INSECURE_MODE = true; // Enable for local dev with self-signed certs

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      // Initial state
      runtime: {
        host: DEFAULT_HOST,
        port: DEFAULT_PORT,
        protocol: DEFAULT_PROTOCOL,
        insecureMode: DEFAULT_INSECURE_MODE,
        connected: false,
        lastChecked: null,
      },

      // Set runtime endpoint
      setRuntimeEndpoint: (host, port, protocol = 'https', insecureMode = true) => {
        set({
          runtime: {
            host,
            port,
            protocol,
            insecureMode,
            connected: false,
            lastChecked: null,
          },
        });
      },

      // Toggle insecure mode (for self-signed certificates)
      setInsecureMode: (insecure) => {
        set({
          runtime: {
            ...get().runtime,
            insecureMode: insecure,
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
      name: 'graphflow-settings', // localStorage key
      partialize: (state) => ({
        runtime: {
          host: state.runtime.host,
          port: state.runtime.port,
          protocol: state.runtime.protocol,
          insecureMode: state.runtime.insecureMode,
          // Don't persist connection status
          connected: false,
          lastChecked: null,
        },
      }),
    }
  )
);
