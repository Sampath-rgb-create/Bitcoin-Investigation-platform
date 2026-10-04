import React from 'react';
import { Briefcase, Plus, Play, ChevronDown, CheckCircle2, Clock } from 'lucide-react';
import type { CaseSummary } from '../../types/forensics';

interface CaseSelectorSidebarProps {
  cases: CaseSummary[];
  activeCaseId: string;
  onSelectCase: (caseId: string) => void;
  onOpenCreateCaseModal: () => void;
  onTriggerDemoRun: () => void;
  isDemoRunning?: boolean;
}

export const CaseSelectorSidebar: React.FC<CaseSelectorSidebarProps> = ({
  cases,
  activeCaseId,
  onSelectCase,
  onOpenCreateCaseModal,
  onTriggerDemoRun,
  isDemoRunning = false,
}) => {
  const activeCase = cases.find((c) => c.id === activeCaseId) || cases[0];

  return (
    <aside className="w-64 border-r border-slate-800 bg-[#090e17] flex flex-col h-[calc(100vh-3.5rem)] shrink-0 select-none">
      {/* Target Case Selector Block */}
      <div className="p-3 border-b border-slate-800">
        <label className="text-[10px] uppercase font-mono tracking-wider text-slate-500 block mb-1">
          Active Case Vault
        </label>
        <div className="relative">
          <select
            value={activeCaseId}
            onChange={(e) => onSelectCase(e.target.value)}
            className="w-full bg-[#131e32] border border-slate-700/80 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono appearance-none pr-7 cursor-pointer"
          >
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2 top-2.5 pointer-events-none" />
        </div>

        {/* Selected Case Metadata Card */}
        {activeCase && (
          <div className="mt-2.5 p-2 rounded bg-[#0e1626] border border-slate-800/80 space-y-1.5 text-[11px] font-mono">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-slate-500">Status:</span>
              <span className="flex items-center gap-1 text-emerald-400 font-medium">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                {activeCase.status}
              </span>
            </div>
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-slate-500">Datasets:</span>
              <span className="text-slate-300">{activeCase.datasetCount} loaded</span>
            </div>
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-slate-500">High Risk:</span>
              <span className="text-rose-400 font-bold">{activeCase.criticalAlertCount} critical</span>
            </div>
            <div className="flex items-center justify-between text-slate-400 pt-1 border-t border-slate-800/60">
              <span className="text-slate-500 text-[10px]">Created:</span>
              <span className="text-slate-400 text-[10px] flex items-center gap-1">
                <Clock className="w-2.5 h-2.5" />
                {activeCase.createdDate}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Case Management Actions */}
      <div className="p-3 space-y-2 border-b border-slate-800">
        <button
          onClick={onOpenCreateCaseModal}
          className="w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
        >
          <Plus className="w-3.5 h-3.5 text-cyan-400" />
          <span>New Case Dossier</span>
        </button>

        <button
          onClick={onTriggerDemoRun}
          disabled={isDemoRunning}
          className="w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded text-xs font-mono font-medium bg-cyan-950/60 hover:bg-cyan-900/60 text-cyan-300 border border-cyan-700/50 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Play className={`w-3 h-3 text-cyan-400 ${isDemoRunning ? 'animate-spin' : ''}`} />
          <span>{isDemoRunning ? 'Simulating...' : 'Quick Demo Run'}</span>
        </button>
      </div>

      {/* Recent Cases History List */}
      <div className="flex-1 overflow-y-auto p-3">
        <span className="text-[10px] uppercase font-mono tracking-wider text-slate-500 block mb-2">
          Investigation Dossiers
        </span>
        <div className="space-y-1">
          {cases.map((c) => {
            const isSelected = c.id === activeCaseId;
            return (
              <button
                key={c.id}
                onClick={() => onSelectCase(c.id)}
                className={`w-full text-left p-2 rounded text-xs transition border flex flex-col space-y-0.5 ${
                  isSelected
                    ? 'bg-[#131e32] border-cyan-500/40 text-cyan-200 shadow-sm'
                    : 'bg-transparent border-transparent text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="font-medium truncate max-w-[140px]">{c.name}</span>
                  <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-slate-800 text-slate-400">
                    {c.alertCount} alrts
                  </span>
                </div>
                <span className="text-[10px] font-mono text-slate-500 truncate">
                  {c.targetAddress.slice(0, 8)}...{c.targetAddress.slice(-4)}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Sidebar Footer telemetry */}
      <div className="p-3 border-t border-slate-800 text-[10px] font-mono text-slate-500 flex items-center justify-between bg-[#070b12]">
        <span className="flex items-center gap-1.5">
          <Briefcase className="w-3 h-3 text-slate-400" />
          <span>VAULT LOCAL</span>
        </span>
        <span className="text-slate-400 font-semibold">{cases.length} cases</span>
      </div>
    </aside>
  );
};
