import { X } from 'lucide-react';
import { useState } from 'react';
import { useSettingsStore } from '@/stores/settingsStore';

interface SettingsModalProps {
  onClose: () => void;
}

export default function SettingsModal({ onClose }: SettingsModalProps) {
  const { runtime, setRuntimeEndpoint, checkConnection } = useSettingsStore();
  const [host, setHost] = useState(runtime.host);
  const [port, setPort] = useState(runtime.port.toString());
  const [protocol, setProtocol] = useState<'http' | 'https'>(runtime.protocol);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  const handleSave = async () => {
    const portNum = parseInt(port, 10);
    if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
      setTestResult('error');
      return;
    }

    setRuntimeEndpoint(host, portNum, protocol);
    setTesting(true);
    setTestResult(null);

    const connected = await checkConnection();
    setTestResult(connected ? 'success' : 'error');
    setTesting(false);

    if (connected) {
      setTimeout(onClose, 500);
    }
  };

  const handleTest = async () => {
    const portNum = parseInt(port, 10);
    if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
      setTestResult('error');
      return;
    }

    // Temporarily update to test
    setRuntimeEndpoint(host, portNum, protocol);
    setTesting(true);
    setTestResult(null);

    const connected = await checkConnection();
    setTestResult(connected ? 'success' : 'error');
    setTesting(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background border border-border rounded-lg shadow-lg w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-muted transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          <div>
            <h3 className="text-sm font-medium mb-3">Runtime Connection</h3>

            <div className="space-y-3">
              {/* Protocol */}
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Protocol</label>
                <select
                  value={protocol}
                  onChange={(e) => setProtocol(e.target.value as 'http' | 'https')}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background"
                >
                  <option value="http">HTTP</option>
                  <option value="https">HTTPS</option>
                </select>
              </div>

              {/* Host */}
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Host</label>
                <input
                  type="text"
                  value={host}
                  onChange={(e) => setHost(e.target.value)}
                  placeholder="localhost"
                  className="w-full px-3 py-2 border border-border rounded-md bg-background"
                />
              </div>

              {/* Port */}
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Port</label>
                <input
                  type="text"
                  value={port}
                  onChange={(e) => setPort(e.target.value)}
                  placeholder="8000"
                  className="w-full px-3 py-2 border border-border rounded-md bg-background"
                />
              </div>

              {/* Test result */}
              {testResult && (
                <div className={`text-sm ${testResult === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                  {testResult === 'success' ? 'Connection successful!' : 'Connection failed. Please check settings.'}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-border">
          <button
            onClick={handleTest}
            disabled={testing}
            className="px-4 py-2 border border-border rounded-md hover:bg-muted transition-colors disabled:opacity-50"
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          <button
            onClick={handleSave}
            disabled={testing}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
