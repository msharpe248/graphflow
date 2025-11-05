import { memo, useState, useRef, useEffect } from 'react';
import { NodeProps, NodeResizer } from 'reactflow';
import { Shape } from '@/types/graph';
import { useGraphStore } from '@/stores/graphStore';
import MarkdownText from './MarkdownText';

interface ShapeNodeData {
  shape: Shape;
}

function ShapeNode({ id, data, selected }: NodeProps<ShapeNodeData>) {
  const { shape } = data;
  const updateShape = useGraphStore((state) => state.updateShape);
  const deleteShape = useGraphStore((state) => state.deleteShape);
  const setSelectedShape = useGraphStore((state) => state.setSelectedShape);

  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(shape.text || '');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleClick = () => {
    setSelectedShape(id);
  };

  const handleDoubleClick = (e: React.MouseEvent) => {
    // Only enable editing for textbox and stickynote
    if (shape.type === 'textbox' || shape.type === 'stickynote') {
      e.stopPropagation();
      setIsEditing(true);
      setEditText(shape.text || '');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (isEditing) {
      // Exit edit mode on Escape
      if (e.key === 'Escape') {
        e.stopPropagation();
        setIsEditing(false);
        setEditText(shape.text || '');
      }
      // Don't let other keyboard events propagate while editing
      // This prevents the shape from being deleted, moved, etc.
      if (e.key !== 'Tab') {
        e.stopPropagation();
      }
    } else if (selected && (e.key === 'Delete' || e.key === 'Backspace')) {
      e.preventDefault();
      deleteShape(id);
    }
  };

  const handleBlur = () => {
    // Save changes when clicking outside
    updateShape(id, { text: editText });
    setIsEditing(false);
  };

  // Focus textarea when entering edit mode
  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      // Move cursor to end
      textareaRef.current.selectionStart = editText.length;
      textareaRef.current.selectionEnd = editText.length;
    }
  }, [isEditing, editText.length]);

  const rgbaColor = `${shape.color}${Math.round(shape.opacity * 255).toString(16).padStart(2, '0')}`;

  return (
    <div
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      style={{
        width: shape.size.width,
        height: shape.size.height,
        cursor: isEditing ? 'text' : 'move',
      }}
    >
      <NodeResizer
        isVisible={selected}
        minWidth={100}
        minHeight={60}
        onResize={(event, params) => {
          updateShape(id, {
            size: { width: params.width, height: params.height },
          });
        }}
      />

      <svg
        width={shape.size.width}
        height={shape.size.height}
        style={{ overflow: 'visible', filter: shape.shadow ? 'drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.2))' : 'none' }}
      >
        {shape.type === 'rectangle' ? (
          <rect
            x={0}
            y={0}
            width={shape.size.width}
            height={shape.size.height}
            rx={12}
            fill={rgbaColor}
            stroke={shape.borderColor || '#64748b'}
            strokeWidth={3}
            strokeDasharray={selected ? '5,5' : 'none'}
          />
        ) : shape.type === 'ellipse' ? (
          <ellipse
            cx={shape.size.width / 2}
            cy={shape.size.height / 2}
            rx={shape.size.width / 2}
            ry={shape.size.height / 2}
            fill={rgbaColor}
            stroke={shape.borderColor || '#64748b'}
            strokeWidth={3}
            strokeDasharray={selected ? '5,5' : 'none'}
          />
        ) : shape.type === 'textbox' ? (
          <rect
            x={0}
            y={0}
            width={shape.size.width}
            height={shape.size.height}
            rx={6}
            fill={rgbaColor}
            stroke={shape.borderColor || '#d1d5db'}
            strokeWidth={2}
            strokeDasharray={selected ? '5,5' : 'none'}
          />
        ) : shape.type === 'stickynote' ? (
          <rect
            x={0}
            y={0}
            width={shape.size.width}
            height={shape.size.height}
            rx={8}
            fill={rgbaColor}
            stroke={shape.borderColor || '#fde047'}
            strokeWidth={2}
            strokeDasharray={selected ? '5,5' : 'none'}
          />
        ) : null}
      </svg>

      {/* Title and text */}
      <div
        className={`absolute inset-0 flex flex-col ${
          isEditing ? 'pointer-events-auto' : 'pointer-events-none'
        } ${
          shape.textAlign === 'left' ? 'items-start' :
          shape.textAlign === 'right' ? 'items-end' :
          'items-center'
        } ${
          shape.textVerticalAlign === 'top' ? 'justify-start' :
          shape.textVerticalAlign === 'bottom' ? 'justify-end' :
          'justify-center'
        }`}
        style={{
          color: shape.textColor || '#1f2937',
          padding: `${shape.padding || 16}px`,
        }}
      >
        {(shape.type === 'textbox' || shape.type === 'stickynote') ? (
          // Markdown rendering for textbox and stickynote
          isEditing ? (
            <textarea
              ref={textareaRef}
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              onBlur={handleBlur}
              className="w-full h-full resize-none bg-transparent border-none outline-none"
              style={{
                color: shape.textColor || '#1f2937',
                fontSize: `${shape.textFontSize || 12}px`,
                fontFamily: 'inherit',
                textAlign: shape.textAlign || 'left',
              }}
              placeholder="Type your text here... Supports markdown!"
            />
          ) : shape.text ? (
            <div className="w-full h-full overflow-auto">
              <MarkdownText
                content={shape.text}
                fontSize={shape.textFontSize || 12}
                fontWeight={shape.fontWeight}
                textAlign={shape.textAlign}
                textColor={shape.textColor}
              />
            </div>
          ) : (
            <div className="text-gray-400 text-sm italic">
              Double-click to edit
            </div>
          )
        ) : (
          // Original plain text rendering for rectangle and ellipse
          <>
            {shape.title && (
              <div
                className={`mb-1 ${
                  shape.textAlign === 'left' ? 'text-left' :
                  shape.textAlign === 'right' ? 'text-right' :
                  'text-center'
                } ${
                  shape.fontWeight === 'bold' ? 'font-bold' :
                  shape.fontWeight === 'semibold' ? 'font-semibold' :
                  shape.fontWeight === 'medium' ? 'font-medium' :
                  'font-normal'
                }`}
                style={{ fontSize: shape.titleFontSize ? `${shape.titleFontSize}px` : '14px' }}
              >
                {shape.title}
              </div>
            )}
            {shape.text && (
              <div
                className={`${
                  shape.textAlign === 'left' ? 'text-left' :
                  shape.textAlign === 'right' ? 'text-right' :
                  'text-center'
                } ${
                  shape.fontWeight === 'bold' ? 'font-bold' :
                  shape.fontWeight === 'semibold' ? 'font-semibold' :
                  shape.fontWeight === 'medium' ? 'font-medium' :
                  'font-normal'
                }`}
                style={{ fontSize: shape.textFontSize ? `${shape.textFontSize}px` : '12px' }}
              >
                {shape.text}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default memo(ShapeNode);
