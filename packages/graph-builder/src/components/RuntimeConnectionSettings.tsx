import { useState, useEffect } from 'react';
import { Check, X, RefreshCw, AlertCircle } from 'lucide-react';
import { useSettingsStore } from '@/stores/settingsStore';

export default function RuntimeConnectionSettings() {
  const {
    runtime,
    setRuntimeEndpoint,
    checkConnection,
    getApiBaseUrl,
  } = useSettingsStore();

  const [host, setHost] = useState(runtime.host);
  const [port, setPort] = useState(runtime.port.toString());
  const [protocol, setProtocol] = useState<'http' | 'https'>(runtime.protocol);
  const [isChecking, setIsChecking] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Check for changes
  useEffect(() => {
    const portNum = parseInt(port, 10);
    const changed =
      host !== runtime.host ||
      portNum !== runtime.port ||
      protocol !== runtime.protocol;
    setHasChanges(changed);
  }, [host, port, protocol, runtime]);

  // Check connection on mount
  useEffect(() => {
    handleCheckConnection();
  }, []);

  const handleCheckConnection = async () => {
    setIsChecking(true);
    await checkConnection();
    setIsChecking(false);
  };

  const handleApply = () => {
    const portNum = parseInt(port, 10);
    if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
      alert('Please enter a valid port number (1-65535)');
      return;
    }

    setRuntimeEndpoint(host, portNum, protocol);
    setHasChanges(false);
    handleCheckConnection();
  };

  const handleReset = () => {
    setHost('localhost');
    setPort('8000');
    setProtocol('http');
    setRuntimeEndpoint('localhost', 8000, 'http');
    setHasChanges(false);
    handleCheckConnection();
  };

  const getStatusColor = () => {
    if (!runtime.lastChecked) return 'text-gray-400';
    return runtime.connected ? 'text-green-600' : 'text-red-600';
  };

  const getStatusIcon = () => {
    if (isChecking) return <RefreshCw className="w-4 h-4 animate-spin" />;
    if (!runtime.lastChecked) return <AlertCircle className="w-4 h-4" />;
    return runtime.connected ? (
      <Check className="w-4 h-4" />
    ) : (
      <X className="w-4 h-4" />
    );
  };

  const getStatusText = () => {
    if (isChecking) return 'Checking...';
    if (!runtime.lastChecked) return 'Not checked';
    return runtime.connected ? 'Connected' : 'Disconnected';
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-2">
          Runtime Connection
        </h3>
        <p className="text-xs text-gray-500 mb-4">
          Configure the GraphFlow runtime server connection
        </p>
      </div>

      {/* Connection Status */}
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2">
          <span className={`${getStatusColor()}`}>{getStatusIcon()}</span>
          <span className="text-sm font-medium text-gray-700">
            {getStatusText()}
          </span>
        </div>
        <button
          onClick={handleCheckConnection}
          disabled={isChecking}
          className="text-xs px-2 py-1 rounded bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
        >
          Test Connection
        </button>
      </div>

      {/* Current Endpoint Display */}
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="text-xs font-medium text-blue-900 mb-1">
          Current Endpoint:
        </div>
        <div className="text-sm font-mono text-blue-700 break-all">
          {getApiBaseUrl()}
        </div>
      </div>

      {/* Configuration Form */}
      <div className="space-y-3">
        {/* Protocol Selection */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Protocol
          </label>
          <select
            value={protocol}
            onChange={(e) => setProtocol(e.target.value as 'http' | 'https')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="http">http://</option>
            <option value="https">https://</option>
          </select>
        </div>

        {/* Host Input */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Hostname / IP Address
          </label>
          <input
            type="text"
            value={host}
            onChange={(e) => setHost(e.target.value)}
            placeholder="localhost"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* Port Input */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Port
          </label>
          <input
            type="number"
            value={port}
            onChange={(e) => setPort(e.target.value)}
            placeholder="8000"
            min="1"
            max="65535"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-2">
        <button
          onClick={handleApply}
          disabled={!hasChanges}
          className="flex-1 px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Apply Changes
        </button>
        <button
          onClick={handleReset}
          className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Reset to Default
        </button>
      </div>

      {/* Future: Authentication Section */}
      <div className="mt-6 p-3 bg-gray-50 border border-gray-200 rounded-lg">
        <div className="flex items-center gap-2 mb-1">
          <AlertCircle className="w-4 h-4 text-gray-400" />
          <span className="text-xs font-medium text-gray-700">
            Authentication
          </span>
        </div>
        <p className="text-xs text-gray-500">
          API authentication will be available in a future release.
        </p>
      </div>
    </div>
  );
}
