import { memo } from 'react';
import { NodeProps, NodeResizer } from 'reactflow';
import { Shape } from '@/types/graph';
import { useGraphStore } from '@/stores/graphStore';

interface ShapeNodeData {
  shape: Shape;
}

function ShapeNode({ id, data, selected }: NodeProps<ShapeNodeData>) {
  const { shape } = data;
  const updateShape = useGraphStore((state) => state.updateShape);
  const deleteShape = useGraphStore((state) => state.deleteShape);
  const setSelectedShape = useGraphStore((state) => state.setSelectedShape);

  const handleClick = () => {
    setSelectedShape(id);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (selected && (e.key === 'Delete' || e.key === 'Backspace')) {
      e.preventDefault();
      deleteShape(id);
    }
  };

  const rgbaColor = `${shape.color}${Math.round(shape.opacity * 255).toString(16).padStart(2, '0')}`;

  return (
    <div
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      style={{
        width: shape.size.width,
        height: shape.size.height,
        cursor: 'move',
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
        style={{ overflow: 'visible' }}
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
        ) : (
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
        )}
      </svg>

      {/* Title and text */}
      <div
        className={`absolute inset-0 flex flex-col p-4 pointer-events-none ${
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
        }}
      >
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
      </div>
    </div>
  );
}

export default memo(ShapeNode);
