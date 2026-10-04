import React from 'react';
import { ShieldAlert, Database, WifiOff, Terminal, Activity } from 'lucide-react';

interface HeaderProps {
  activeCaseName?: string;
  targetAddress?: string;
  isOfflineMode?: boolean;
  onOpenRulesManager?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeCaseName = 'Operation DarkHydra #4082',
  targetAddress = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
  isOfflineMode = true,
  onOpenRulesManager,
}) => {
  return (
    <header className="h-14 border-b border-slate-800 bg-[#0b1322] px-4 flex items-center justify-between select-none z-30 sticky top-0">
      <div className="flex items-center space-x-3">
        {/* Forensic Brand Icon */}
        <div className="flex items-center justify-center w-8 h-8 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_12px_rgba(56,189,248,0.15)]">
          <ShieldAlert className="w-5 h-5 text-cyan-400" />
        </div>

        <div className="flex flex-col">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-semibold tracking-wider text-slate-100 uppercase">
              CipherTrace <span className="text-cyan-400 font-mono font-bold">AML</span>
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/60 uppercase tracking-wider">
              v2.4-Forensics
            </span>
          </div>
          <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block"></span>
            HEURISTIC ENGINE READY
          </span>
        </div>
      </div>

      {/* Center: Active Target Case & Address Pill */}
      <div className="hidden md:flex items-center space-x-3 px-3 py-1 rounded bg-[#090e17] border border-slate-800/80">
        <div className="flex items-center space-x-1.5 text-xs text-slate-400">
          <Activity className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-slate-500 uppercase tracking-wider text-[10px] font-mono">Case:</span>
          <span className="text-slate-200 font-medium">{activeCaseName}</span>
        </div>
        <div className="h-3 w-px bg-slate-700"></div>
        <div className="flex items-center space-x-1.5 text-xs">
          <span className="text-slate-500 uppercase tracking-wider text-[10px] font-mono">Target:</span>
          <span className="font-mono text-cyan-300 text-xs px-1.5 py-0.5 rounded bg-cyan-950/40 border border-cyan-800/40">
            {targetAddress.slice(0, 10)}...{targetAddress.slice(-6)}
          </span>
        </div>
      </div>

      {/* Right: Security & Network Telemetry */}
      <div className="flex items-center space-x-3">
        {onOpenRulesManager && (
          <button
            onClick={onOpenRulesManager}
            className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 text-xs font-mono text-slate-300 hover:text-cyan-300 bg-slate-800/80 hover:bg-slate-800 border border-slate-700 rounded transition-colors"
          >
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
            <span>Rules Heuristics</span>
          </button>
        )}

        {/* Offline air-gap status */}
        <div
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border text-xs font-mono ${
            isOfflineMode
              ? 'bg-emerald-950/30 text-emerald-300 border-emerald-800/50'
              : 'bg-amber-950/30 text-amber-300 border-amber-800/50'
          }`}
          title={isOfflineMode ? 'Air-gapped safe environment active' : 'Connected to live external nodes'}
        >
          {isOfflineMode ? (
            <>
              <WifiOff className="w-3.5 h-3.5 text-emerald-400" />
              <span>AIR-GAPPED</span>
            </>
          ) : (
            <>
              <Database className="w-3.5 h-3.5 text-amber-400" />
              <span>REMOTE SYNC</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
