import React from 'react';
import {
  Search,
  Maximize2,
  ArrowRightLeft,
  Eye,
  EyeOff,
  RefreshCw,
} from 'lucide-react';
import type { LayoutDirection } from './graphLayout';

interface GraphToolbarProps {
  layoutMode: LayoutDirection;
  onLayoutChange: (mode: LayoutDirection) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onFitView: () => void;
  showIps: boolean;
  onToggleIps: () => void;
  onResetGraph?: () => void;
  totalNodes: number;
  totalEdges: number;
}

export const GraphToolbar: React.FC<GraphToolbarProps> = ({
  layoutMode,
  onLayoutChange,
  searchQuery,
  onSearchChange,
  onFitView,
  showIps,
  onToggleIps,
  onResetGraph,
  totalNodes,
  totalEdges,
}) => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-2.5 bg-slate-950/90 backdrop-blur-md border border-slate-800/80 rounded-xl shadow-xl font-sans text-xs">
      {/* Left: Search Bar */}
      <div className="relative flex-1 min-w-[240px] max-w-md">
        <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Locate Address, TXID, or IP node..."
          className="w-full bg-slate-900/90 text-slate-200 placeholder-slate-500 pl-8 pr-3 py-1.5 rounded-lg border border-slate-800 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 focus:outline-none font-mono text-xs transition-all"
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 text-[11px]"
          >
            ✕
          </button>
        )}
      </div>

      {/* Middle: Layout Direction Mode Switcher */}
      <div className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-lg border border-slate-800">
        <span className="text-[10px] uppercase font-semibold text-slate-400 px-2 flex items-center gap-1">
          <ArrowRightLeft className="w-3 h-3 text-sky-400" /> Layout:
        </span>
        <button
          onClick={() => onLayoutChange('LR')}
          className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
            layoutMode === 'LR'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/50 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
          title="Left-to-Right money flow"
        >
          LR Flow
        </button>
        <button
          onClick={() => onLayoutChange('TB')}
          className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
            layoutMode === 'TB'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/50 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
          title="Top-to-Bottom hierarchy"
        >
          TB Vertical
        </button>
        <button
          onClick={() => onLayoutChange('RADIAL')}
          className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
            layoutMode === 'RADIAL'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/50 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
          title="Radial cluster layout"
        >
          Radial
        </button>
      </div>

      {/* Right Controls: IP Toggle, Fit View, Topology Stats */}
      <div className="flex items-center gap-2">
        {/* Toggle Telemetry IPs */}
        <button
          onClick={onToggleIps}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[11px] font-medium transition-all ${
            showIps
              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-700/60'
              : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:text-slate-200'
          }`}
          title={showIps ? 'Hide Network IPs' : 'Show Network IPs'}
        >
          {showIps ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
          <span>IP Telemetry</span>
        </button>

        {/* Fit View Button */}
        <button
          onClick={onFitView}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900/90 hover:bg-slate-800 text-slate-200 hover:text-white rounded-lg border border-slate-800 text-[11px] font-medium transition-colors"
          title="Fit graph to canvas"
        >
          <Maximize2 className="w-3.5 h-3.5 text-sky-400" />
          <span>Fit View</span>
        </button>

        {/* Reset / Recalculate */}
        {onResetGraph && (
          <button
            onClick={onResetGraph}
            className="p-1.5 text-slate-400 hover:text-slate-200 bg-slate-900/90 hover:bg-slate-800 rounded-lg border border-slate-800 transition-colors"
            title="Reset Graph Positions"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        )}

        {/* Node/Edge Counter Indicator */}
        <div className="hidden lg:flex items-center gap-2 pl-2 border-l border-slate-800 text-slate-400 text-[10px] font-mono">
          <span>{totalNodes} NODES</span>
          <span>•</span>
          <span>{totalEdges} EDGES</span>
        </div>
      </div>
    </div>
  );
};
