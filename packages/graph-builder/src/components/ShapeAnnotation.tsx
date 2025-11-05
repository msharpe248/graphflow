import { useEffect, useState } from 'react';
import { Shape } from '@/types/graph';
import { useGraphStore } from '@/stores/graphStore';

interface ShapeAnnotationProps {
  shape: Shape;
}

export default function ShapeAnnotation({ shape }: ShapeAnnotationProps) {
  const updateShape = useGraphStore((state) => state.updateShape);
  const deleteShape = useGraphStore((state) => state.deleteShape);
  const setSelectedShape = useGraphStore((state) => state.setSelectedShape);
  const selectedShapeId = useGraphStore((state) => state.selectedShapeId);

  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, width: 0, height: 0 });

  const isSelected = selectedShapeId === shape.id;

  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).classList.contains('resize-handle')) {
      return;
    }
    e.preventDefault();
    e.stopPropagation();
    setSelectedShape(shape.id);
    setIsDragging(true);
    setDragStart({
      x: e.clientX - shape.position.x,
      y: e.clientY - shape.position.y,
    });
  };

  const handleResizeMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    setResizeStart({
      x: e.clientX,
      y: e.clientY,
      width: shape.size.width,
      height: shape.size.height,
    });
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        updateShape(shape.id, {
          position: {
            x: e.clientX - dragStart.x,
            y: e.clientY - dragStart.y,
          },
        });
      } else if (isResizing) {
        const dx = e.clientX - resizeStart.x;
        const dy = e.clientY - resizeStart.y;
        updateShape(shape.id, {
          size: {
            width: Math.max(100, resizeStart.width + dx),
            height: Math.max(60, resizeStart.height + dy),
          },
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setIsResizing(false);
    };

    if (isDragging || isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, isResizing, dragStart, resizeStart, shape.id, updateShape]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (isSelected && (e.key === 'Delete' || e.key === 'Backspace')) {
      e.preventDefault();
      deleteShape(shape.id);
    }
  };

  const rgbaColor = `${shape.color}${Math.round(shape.opacity * 255).toString(16).padStart(2, '0')}`;

  console.log('[ShapeAnnotation] Rendering shape:', shape.id, 'at', shape.position, 'color:', rgbaColor);

  return (
    <div
      className="absolute cursor-move shape-annotation"
      style={{
        left: shape.position.x,
        top: shape.position.y,
        width: shape.size.width,
        height: shape.size.height,
        zIndex: shape.zIndex || -1,
        pointerEvents: 'auto',
      }}
      onMouseDown={handleMouseDown}
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      <svg
        width={shape.size.width}
        height={shape.size.height}
        style={{ overflow: 'visible' }}
        className="shape-annotation"
      >
        {shape.type === 'rectangle' ? (
          <rect
            x={0}
            y={0}
            width={shape.size.width}
            height={shape.size.height}
            rx={12}
            fill={rgbaColor}
            stroke="#000000"
            strokeWidth={5}
            strokeDasharray={isSelected ? '5,5' : 'none'}
            className="shape-annotation"
          />
        ) : (
          <ellipse
            cx={shape.size.width / 2}
            cy={shape.size.height / 2}
            rx={shape.size.width / 2}
            ry={shape.size.height / 2}
            fill={rgbaColor}
            stroke="#000000"
            strokeWidth={5}
            strokeDasharray={isSelected ? '5,5' : 'none'}
            className="shape-annotation"
          />
        )}
      </svg>

      {/* Title and text */}
      <div
        className="absolute inset-0 flex flex-col items-center justify-center p-4 pointer-events-none"
        style={{ color: shape.color }}
      >
        {shape.title && (
          <div className="font-semibold text-sm mb-1 text-center">{shape.title}</div>
        )}
        {shape.text && (
          <div className="text-xs text-center opacity-80">{shape.text}</div>
        )}
      </div>

      {/* Resize handle */}
      {isSelected && (
        <div
          className="resize-handle absolute bottom-0 right-0 w-4 h-4 bg-blue-500 cursor-se-resize"
          style={{ zIndex: 10 }}
          onMouseDown={handleResizeMouseDown}
        />
      )}
    </div>
  );
}
