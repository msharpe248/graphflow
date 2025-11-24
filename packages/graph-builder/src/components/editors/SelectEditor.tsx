import { useState, useRef, useEffect } from 'react';
import { EditorProps } from './types';

export default function SelectEditor({ value, onChange, schema }: EditorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showAll, setShowAll] = useState(false); // Show all options when clicking dropdown button
  const [inputValue, setInputValue] = useState(value || '');
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const options: string[] = schema.enum || [];
  const hasCustomValue = value && !options.includes(value);

  // Filter options based on input (for typeahead), unless showAll is true
  const filteredOptions = showAll
    ? options
    : inputValue
      ? options.filter(opt => opt.toLowerCase().includes(inputValue.toLowerCase()))
      : options;

  // Sync input value with external value changes
  useEffect(() => {
    setInputValue(value || '');
  }, [value]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setShowAll(false); // When typing, filter options
    setIsOpen(true);
  };

  const handleInputBlur = () => {
    // Commit the typed value on blur
    if (inputValue !== value) {
      onChange(inputValue);
    }
  };

  const handleSelectOption = (option: string) => {
    setInputValue(option);
    onChange(option);
    setIsOpen(false);
    setShowAll(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
    } else if (e.key === 'Enter') {
      if (filteredOptions.length === 1) {
        handleSelectOption(filteredOptions[0]);
      } else {
        onChange(inputValue);
        setIsOpen(false);
      }
    } else if (e.key === 'ArrowDown' && !isOpen) {
      setIsOpen(true);
    }
  };

  return (
    <div className="relative" ref={containerRef}>
      <div className="flex">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
          placeholder={schema.description || 'Select or type...'}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="button"
          onClick={() => {
            setShowAll(true); // Show all options when clicking dropdown button
            setIsOpen(!isOpen);
          }}
          className="px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isOpen ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"} />
          </svg>
        </button>
      </div>

      {hasCustomValue && (
        <span className="absolute right-10 top-1/2 -translate-y-1/2 text-xs text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">
          custom
        </span>
      )}

      {isOpen && filteredOptions.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {filteredOptions.map((option) => (
            <div
              key={option}
              onMouseDown={(e) => {
                e.preventDefault(); // Prevent blur before click registers
                handleSelectOption(option);
              }}
              className={`px-3 py-2 cursor-pointer hover:bg-blue-50 ${
                option === value ? 'bg-blue-100 font-medium' : ''
              }`}
            >
              {option}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
