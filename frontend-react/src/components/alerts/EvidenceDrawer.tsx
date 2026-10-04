import React from 'react';
import type { ForensicAlert } from '../../types/forensics';
import {
  X,
  Target,
  Brain,
  Search,
  GitFork,
  Scale,
  TrendingUp,
  FileCode,
  ShieldAlert,
  Flame,
  Clock,
  ArrowRight,
} from 'lucide-react';

interface EvidenceDrawerProps {
  alert: ForensicAlert | null;
  onClose: () => void;
  onSendToGraphCanvas?: (alert: ForensicAlert) => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  alert,
  onClose,
  onSendToGraphCanvas,
}) => {
  if (!alert) return null;

  const scoreCards = [
    {
      title: 'Composite Ensemble',
      score: alert.scores.compositeScore,
      icon: Target,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-950/20 border-cyan-500/40',
      desc: 'Combined Bayesian ensemble weight',
    },
    {
      title: 'Supervised ML',
      score: alert.scores.supervisedMlScore,
      icon: Brain,
      color: 'text-indigo-400',
      bgColor: 'bg-indigo-950/20 border-indigo-500/40',
      desc: 'XGBoost darknet pattern classification',
    },
    {
      title: 'Unsupervised (IF)',
      score: alert.scores.unsupervisedIfScore,
      icon: Search,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-950/20 border-emerald-500/40',
      desc: 'Isolation Forest distance anomaly',
    },
    {
      title: 'Graph Flow',
      score: alert.scores.graphFlowScore,
      icon: GitFork,
      color: 'text-amber-400',
      bgColor: 'bg-amber-950/20 border-amber-500/40',
      desc: 'Peeling chain / mixer taint transfer',
    },
    {
      title: 'Custom Rules',
      score: alert.scores.customRulesScore,
      icon: Scale,
      color: 'text-rose-400',
      bgColor: 'bg-rose-950/20 border-rose-500/40',
      desc: 'Investigator policy thresholds',
    },
  ];

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-xl bg-[#090e17] border-l border-slate-800 shadow-2xl z-50 flex flex-col overflow-hidden animate-in slide-in-from-right duration-200">
      {/* Top Bar */}
      <div className="p-4 bg-[#0b1322] border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1 rounded bg-rose-950/80 border border-rose-800 text-rose-400">
            <Flame className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-semibold text-slate-100 font-mono">
                FORENSIC EVIDENCE DOSSIER
              </h3>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-rose-950/60 text-rose-300 border border-rose-800 font-bold">
                {alert.severity}
              </span>
            </div>
            <p className="text-[10px] font-mono text-slate-500">ID: {alert.id}</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Main Drawer Scrollable Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Tx Metadata Ribbon */}
        <div className="p-3 rounded-lg bg-[#0f172a] border border-slate-800 space-y-2 text-xs font-mono">
          <div className="flex items-center justify-between text-slate-400">
            <span>Tx Hash:</span>
            <span className="text-cyan-300 font-semibold select-all">
              {alert.txHash.slice(0, 16)}...{alert.txHash.slice(-12)}
            </span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span>Target Addr:</span>
            <span className="text-slate-200 select-all font-semibold">
              {alert.targetAddress}
            </span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span>Timestamp:</span>
            <span className="text-slate-300 flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-500" />
              {alert.timestamp}
            </span>
          </div>
          <div className="flex items-center justify-between text-slate-400 pt-1 border-t border-slate-800/80">
            <span>Displaced Volume:</span>
            <span className="text-slate-100 font-bold">
              {alert.amountBtc.toFixed(4)} ₿ (${alert.amountUsd.toLocaleString()})
            </span>
          </div>
        </div>

        {/* 5 Separated Heuristic Score Cards */}
        <div>
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
            <span>5-Stream Multi-Heuristic Scoring</span>
            <span className="text-[10px] text-slate-500">Normal Range: 0.0 - 1.0</span>
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {scoreCards.map((sc) => {
              const Icon = sc.icon;
              return (
                <div
                  key={sc.title}
                  className={`p-2.5 rounded-lg border ${sc.bgColor} flex flex-col justify-between`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1.5">
                      <Icon className={`w-3.5 h-3.5 ${sc.color}`} />
                      <span className="text-[11px] font-mono text-slate-300 font-medium">
                        {sc.title}
                      </span>
                    </div>
                    <span className={`text-sm font-mono font-bold ${sc.color}`}>
                      {(sc.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1 font-mono">{sc.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Forensic Explanation Narrative */}
        <div className="p-3.5 rounded-lg bg-[#0f172a] border border-slate-800">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" />
            <span>Investigative Narrative & Heuristic Reasoning</span>
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            {alert.narrative}
          </p>

          <div className="mt-3 flex flex-wrap gap-1.5">
            {alert.tags.map((tag) => (
              <span
                key={tag}
                className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/50 text-cyan-300 border border-cyan-800/60"
              >
                #{tag}
              </span>
            ))}
          </div>
        </div>

        {/* Top Deviation Reasons Breakdown */}
        <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-3.5">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2.5 flex items-center space-x-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
            <span>Top Anomaly Feature Deviations (SHAP/Attribution)</span>
          </h4>

          <div className="space-y-2">
            {alert.deviationReasons.map((reason, idx) => (
              <div
                key={idx}
                className="p-2 rounded bg-[#090e17] border border-slate-800/80 text-xs font-mono"
              >
                <div className="flex items-center justify-between text-slate-300 mb-1">
                  <span className="font-semibold text-cyan-300">{reason.feature}</span>
                  <span className="text-rose-400 font-bold">
                    +{reason.contribution}% anomaly weight
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 mb-1">
                  <div>
                    <span className="text-slate-500">Baseline/Expected: </span>
                    <span>{reason.expectedValue}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Observed: </span>
                    <span className="text-slate-200 font-semibold">{reason.observedValue}</span>
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 font-sans">{reason.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Raw Source Record Details */}
        <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-3.5">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1.5">
            <FileCode className="w-3.5 h-3.5 text-emerald-400" />
            <span>Raw Canonical Ledger Attributes</span>
          </h4>

          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="p-2 rounded bg-[#090e17] border border-slate-800/70">
              <span className="text-slate-500 block text-[10px]">Inputs Count:</span>
              <span className="text-slate-200 font-bold">{alert.rawSource.inputsCount}</span>
            </div>
            <div className="p-2 rounded bg-[#090e17] border border-slate-800/70">
              <span className="text-slate-500 block text-[10px]">Outputs Count:</span>
              <span className="text-slate-200 font-bold">{alert.rawSource.outputsCount}</span>
            </div>
            <div className="p-2 rounded bg-[#090e17] border border-slate-800/70">
              <span className="text-slate-500 block text-[10px]">Miner Fee:</span>
              <span className="text-slate-200 font-bold">
                {alert.rawSource.feeSats.toLocaleString()} sats
              </span>
            </div>
            <div className="p-2 rounded bg-[#090e17] border border-slate-800/70">
              <span className="text-slate-500 block text-[10px]">First Seen Block:</span>
              <span className="text-slate-200 font-bold">
                #{alert.rawSource.firstSeenBlock.toLocaleString()}
              </span>
            </div>
            {alert.rawSource.peelingChainLength !== undefined && (
              <div className="p-2 rounded bg-[#090e17] border border-slate-800/70 col-span-2">
                <span className="text-slate-500 block text-[10px]">Peeling Chain Length:</span>
                <span className="text-amber-400 font-bold">
                  {alert.rawSource.peelingChainLength} successive hops detected
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Drawer Action Footer */}
      <div className="p-4 bg-[#0b1322] border-t border-slate-800 flex items-center justify-between">
        <span className="text-[10px] font-mono text-slate-500">
          CASE ATTESTATION SAFE (SHA256)
        </span>
        {onSendToGraphCanvas && (
          <button
            onClick={() => onSendToGraphCanvas(alert)}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-mono font-medium bg-cyan-600 hover:bg-cyan-500 text-white shadow transition cursor-pointer"
          >
            <span>Trace in Graph Canvas</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};
