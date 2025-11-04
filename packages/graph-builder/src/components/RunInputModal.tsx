import { useState, useMemo } from 'react';
import { X, AlertCircle, AlertTriangle, Code2, FileText } from 'lucide-react';
import { ValidationResult, ValidationIssue, formatValidationIssue } from '@/utils/graphValidator';
import { MemorySchema } from '@/types/graph';

interface RunInputModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRun: (inputs: Record<string, any>) => void;
  graphName: string;
  memory: MemorySchema;
  validation: ValidationResult;
}

export default function RunInputModal({
  isOpen,
  onClose,
  onRun,
  graphName,
  memory,
  validation,
}: RunInputModalProps) {
  const [inputs, setInputs] = useState<Record<string, any>>({});
  const [mode, setMode] = useState<'form' | 'json'>('form');
  const [jsonText, setJsonText] = useState<string>('{}');
  const [jsonError, setJsonError] = useState<string>('');

  // Initialize inputs with defaults
  useMemo(() => {
    const initialInputs: Record<string, any> = {};
    Object.entries(memory.inputs).forEach(([key, field]) => {
      if (field.default !== undefined) {
        initialInputs[key] = field.default;
      } else {
        // Provide sensible defaults based on type
        switch (field.type) {
          case 'string':
            initialInputs[key] = '';
            break;
          case 'number':
          case 'integer':
            initialInputs[key] = 0;
            break;
          case 'boolean':
            initialInputs[key] = false;
            break;
          case 'array':
            initialInputs[key] = [];
            break;
          case 'object':
            initialInputs[key] = {};
            break;
          default:
            initialInputs[key] = '';
        }
      }
    });
    setInputs(initialInputs);
    setJsonText(JSON.stringify(initialInputs, null, 2));
  }, [memory.inputs]);

  const handleInputChange = (key: string, value: any) => {
    const newInputs = { ...inputs, [key]: value };
    setInputs(newInputs);
    setJsonText(JSON.stringify(newInputs, null, 2));
  };

  const handleJsonChange = (text: string) => {
    setJsonText(text);
    try {
      const parsed = JSON.parse(text);
      setInputs(parsed);
      setJsonError('');
    } catch (e) {
      setJsonError((e as Error).message);
    }
  };

  const handleRun = () => {
    if (mode === 'json' && jsonError) {
      return; // Don't run if JSON is invalid
    }

    // Block if there are validation errors
    if (!validation.isValid) {
      return;
    }

    onRun(inputs);
  };

  const renderIssue = (issue: ValidationIssue) => {
    const Icon = issue.type === 'error' ? AlertCircle : AlertTriangle;
    const colorClasses = issue.type === 'error'
      ? 'bg-red-50 border-red-200 text-red-800'
      : 'bg-yellow-50 border-yellow-200 text-yellow-800';

    return (
      <div key={`${issue.type}-${issue.field}-${issue.stepId}`} className={`flex gap-2 p-2 rounded border ${colorClasses}`}>
        <Icon className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <div className="flex-1 text-xs">
          <pre className="whitespace-pre-wrap font-mono">{formatValidationIssue(issue)}</pre>
        </div>
      </div>
    );
  };

  const renderFormInput = (key: string, field: any) => {
    const value = inputs[key];

    if (field.type === 'boolean') {
      return (
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={value || false}
            onChange={(e) => handleInputChange(key, e.target.checked)}
            className="rounded border-gray-300"
          />
          <span className="text-sm text-gray-600">
            {field.description || key}
          </span>
        </div>
      );
    }

    if (field.type === 'number' || field.type === 'integer') {
      return (
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            {field.description || key}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <input
            type="number"
            step={field.type === 'integer' ? 1 : 'any'}
            value={value || 0}
            onChange={(e) => handleInputChange(key, field.type === 'integer' ? parseInt(e.target.value, 10) : parseFloat(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            required={field.required}
          />
        </div>
      );
    }

    if (field.type === 'array' || field.type === 'object') {
      return (
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            {field.description || key}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <textarea
            value={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleInputChange(key, parsed);
              } catch {
                // Keep as string while editing
                handleInputChange(key, e.target.value);
              }
            }}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
            placeholder={field.type === 'array' ? '[]' : '{}'}
            required={field.required}
          />
          {field.description && (
            <p className="text-xs text-gray-500 mt-1">{field.description}</p>
          )}
        </div>
      );
    }

    // Default: string input
    return (
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          {field.description || key}
          {field.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <input
          type="text"
          value={value || ''}
          onChange={(e) => handleInputChange(key, e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          required={field.required}
        />
      </div>
    );
  };

  if (!isOpen) return null;

  const hasInputs = Object.keys(memory.inputs).length > 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Run Graph</h2>
            <p className="text-sm text-gray-600">{graphName}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Validation Issues */}
          {validation.hasIssues && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-gray-900">Validation Results</h3>

              {validation.errors.length > 0 && (
                <div className="space-y-2">
                  {validation.errors.map(renderIssue)}
                </div>
              )}

              {validation.warnings.length > 0 && (
                <div className="space-y-2">
                  {validation.warnings.map(renderIssue)}
                </div>
              )}

              {!validation.isValid && (
                <p className="text-sm text-red-600 font-medium">
                  Please fix all errors before running.
                </p>
              )}
            </div>
          )}

          {/* Input Collection */}
          {validation.isValid && (
            <>
              {hasInputs && (
                <>
                  {/* Mode Toggle */}
                  <div className="flex items-center gap-2 border-b border-gray-200 pb-2">
                    <button
                      onClick={() => setMode('form')}
                      className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                        mode === 'form'
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <FileText className="w-4 h-4" />
                      Form
                    </button>
                    <button
                      onClick={() => setMode('json')}
                      className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                        mode === 'json'
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <Code2 className="w-4 h-4" />
                      JSON
                    </button>
                  </div>

                  {/* Form Mode */}
                  {mode === 'form' && (
                    <div className="space-y-3">
                      <h3 className="text-sm font-semibold text-gray-900">Input Values</h3>
                      {Object.entries(memory.inputs).map(([key, field]) => (
                        <div key={key}>
                          {renderFormInput(key, field)}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* JSON Mode */}
                  {mode === 'json' && (
                    <div className="space-y-2">
                      <h3 className="text-sm font-semibold text-gray-900">Input JSON</h3>
                      <textarea
                        value={jsonText}
                        onChange={(e) => handleJsonChange(e.target.value)}
                        rows={10}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
                        spellCheck={false}
                      />
                      {jsonError && (
                        <p className="text-xs text-red-600">
                          Invalid JSON: {jsonError}
                        </p>
                      )}
                    </div>
                  )}
                </>
              )}

              {!hasInputs && (
                <div className="text-center py-8">
                  <p className="text-sm text-gray-500">
                    This graph has no inputs defined.
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    The graph will run with an empty input object.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleRun}
            disabled={!validation.isValid || (mode === 'json' && !!jsonError)}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Run
          </button>
        </div>
      </div>
    </div>
  );
}
