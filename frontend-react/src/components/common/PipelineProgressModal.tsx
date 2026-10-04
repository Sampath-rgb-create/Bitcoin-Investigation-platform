import React from 'react';
import type { PipelineStage } from '../../types/forensics';
import { CheckCircle2, Loader2, AlertCircle, X, Cpu } from 'lucide-react';

interface PipelineProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  stages: PipelineStage[];
  currentOverallProgress: number; // 0 - 100
  activeStageIndex: number;
}

export const PipelineProgressModal: React.FC<PipelineProgressModalProps> = ({
  isOpen,
  onClose,
  stages,
  currentOverallProgress,
  activeStageIndex,
}) => {
  if (!isOpen) return null;

  const isCompleted = currentOverallProgress >= 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg bg-[#0b1322] border border-slate-800 rounded-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 bg-[#090e17] border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded bg-cyan-950/60 border border-cyan-800 text-cyan-400">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100 font-mono">
                PIPELINE EXECUTION TELEMETRY
              </h3>
              <p className="text-[10px] text-slate-400 font-mono">
                Asynchronous UTXO ingestion & 5-stream heuristic processing
              </p>
            </div>
          </div>
          {isCompleted && (
            <button
              onClick={onClose}
              className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-5">
          {/* Main Progress Bar */}
          <div>
            <div className="flex items-center justify-between text-xs font-mono mb-1.5">
              <span className="text-slate-300">
                {isCompleted ? 'Analysis Pipeline Finished' : 'Processing Ledger Stream...'}
              </span>
              <span className="text-cyan-400 font-bold">{currentOverallProgress.toFixed(0)}%</span>
            </div>
            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-linear-to-r from-cyan-500 to-indigo-500 transition-all duration-300"
                style={{ width: `${currentOverallProgress}%` }}
              ></div>
            </div>
          </div>

          {/* Stage Step Cards */}
          <div className="space-y-2 font-mono">
            {stages.map((stage, idx) => {
              const isCurrent = idx === activeStageIndex;
              const isDone = stage.status === 'COMPLETED' || idx < activeStageIndex;
              const isFailed = stage.status === 'FAILED';

              return (
                <div
                  key={stage.id}
                  className={`p-3 rounded-lg border text-xs flex items-center justify-between transition-colors ${
                    isDone
                      ? 'bg-[#0f1b2b] border-emerald-900/40 text-slate-200'
                      : isCurrent
                      ? 'bg-[#132238] border-cyan-500/50 text-cyan-200 shadow-sm'
                      : 'bg-[#090e17] border-slate-800/80 text-slate-500'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : isCurrent ? (
                      <Loader2 className="w-4 h-4 text-cyan-400 animate-spin shrink-0" />
                    ) : isFailed ? (
                      <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-slate-700 flex items-center justify-center text-[9px] text-slate-500">
                        {idx + 1}
                      </div>
                    )}

                    <div>
                      <div className="font-semibold text-slate-200">{stage.name}</div>
                      {stage.detail && (
                        <div className="text-[10px] text-slate-400 mt-0.5">{stage.detail}</div>
                      )}
                    </div>
                  </div>

                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                    {isDone ? 'DONE' : isCurrent ? 'RUNNING' : 'QUEUED'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-[#090e17] border-t border-slate-800 flex items-center justify-between">
          <span className="text-[10px] font-mono text-slate-500">
            {isCompleted ? 'All matrices loaded into memory' : 'Hardware thread pool active'}
          </span>
          {isCompleted && (
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded text-xs font-mono font-medium bg-emerald-600 hover:bg-emerald-500 text-white shadow cursor-pointer transition"
            >
              Inspect Alerts & Graphs
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
