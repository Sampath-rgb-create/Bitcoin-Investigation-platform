import React, { memo } from 'react';
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  EdgeProps,
} from '@xyflow/react';
import { Coins, ArrowRight } from 'lucide-react';

export interface ForensicEdgeData {
  amount?: number;
  type?: string;
  basis?: string;
  sourceRecordIds?: string[];
  isHighlighted?: boolean;
}

export const ForensicFlowEdge: React.FC<EdgeProps> = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
  selected,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const edgeData = (data as ForensicEdgeData) || {};
  const isHighlighted = selected || edgeData.isHighlighted;
  const edgeType = edgeData.type || '';
  const amount = edgeData.amount;

  // Determine edge color theme based on edge relationship
  let strokeColor = '#334155'; // default slate-700
  let strokeWidth = 2;
  let strokeDasharray: string | undefined = undefined;

  if (edgeType === 'RELAYED_BY' || edgeType === 'OBSERVED') {
    strokeColor = isHighlighted ? '#34d399' : '#059669'; // emerald-400 : emerald-600
    strokeDasharray = '5 4';
    strokeWidth = isHighlighted ? 2.5 : 1.5;
  } else if (edgeType === 'SPENT_FROM' || edgeType === 'INPUT_TO') {
    strokeColor = isHighlighted ? '#38bdf8' : '#0284c7'; // sky-400 : sky-600
    strokeWidth = isHighlighted ? 3 : 2;
  } else if (edgeType === 'SENT_TO' || edgeType === 'OUTPUT_TO') {
    strokeColor = isHighlighted ? '#818cf8' : '#4f46e5'; // indigo-400 : indigo-600
    strokeWidth = isHighlighted ? 3 : 2;
  } else if (isHighlighted) {
    strokeColor = '#38bdf8';
    strokeWidth = 3;
  }

  // If amount is large, adjust thickness slightly
  if (amount && amount > 10) {
    strokeWidth = Math.min(strokeWidth + 1.5, 6);
  }

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          stroke: strokeColor,
          strokeWidth,
          strokeDasharray,
          transition: 'stroke 0.2s ease, stroke-width 0.2s ease',
          filter: isHighlighted ? `drop-shadow(0 0 6px ${strokeColor})` : undefined,
        }}
      />
      {amount !== undefined && amount !== null && amount > 0 && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="nodrag nopan"
          >
            <div
              className={`flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-mono font-semibold backdrop-blur-md transition-all border ${
                isHighlighted
                  ? 'bg-slate-900 text-sky-300 border-sky-400 shadow-md shadow-sky-900/50 scale-105'
                  : 'bg-slate-950/90 text-slate-300 border-slate-800 hover:border-slate-700 hover:text-slate-100'
              }`}
            >
              <Coins className="w-2.5 h-2.5 text-amber-400" />
              <span>{amount.toFixed(4)} BTC</span>
            </div>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});
ForensicFlowEdge.displayName = 'ForensicFlowEdge';

export const customEdgeTypes = {
  forensic: ForensicFlowEdge,
};
