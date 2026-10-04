import React from 'react';
import type { ScoreStream } from '../../types/forensics';
import { Target, Brain, Search, GitFork, Scale } from 'lucide-react';

interface ScoreStreamSwitcherProps {
  activeStream: ScoreStream;
  onStreamChange: (stream: ScoreStream) => void;
  streamWeights?: Record<ScoreStream, number>;
}

export const ScoreStreamSwitcher: React.FC<ScoreStreamSwitcherProps> = ({
  activeStream,
  onStreamChange,
  streamWeights = {
    composite: 1.0,
    supervised: 0.35,
    unsupervised: 0.25,
    graph_flow: 0.25,
    custom_rules: 0.15,
  },
}) => {
  const streams: { id: ScoreStream; label: string; icon: React.ElementType; color: string; desc: string }[] = [
    {
      id: 'composite',
      label: 'Composite Ensemble',
      icon: Target,
      color: 'text-cyan-400 border-cyan-500/50 bg-cyan-950/40',
      desc: 'Ensemble score weighted across all 4 algorithmic engines',
    },
    {
      id: 'supervised',
      label: 'Supervised ML',
      icon: Brain,
      color: 'text-indigo-400 border-indigo-500/50 bg-indigo-950/40',
      desc: 'XGBoost trained on known illicit darknet & ransomware labels',
    },
    {
      id: 'unsupervised',
      label: 'Unsupervised (IF)',
      icon: Search,
      color: 'text-emerald-400 border-emerald-500/50 bg-emerald-950/40',
      desc: 'Isolation Forest anomaly detection on multidimensional UTXO vectors',
    },
    {
      id: 'graph_flow',
      label: 'Graph Flow',
      icon: GitFork,
      color: 'text-amber-400 border-amber-500/50 bg-amber-950/40',
      desc: 'PageRank & peeling-chain flow propagation heuristics',
    },
    {
      id: 'custom_rules',
      label: 'Custom Rules',
      icon: Scale,
      color: 'text-rose-400 border-rose-500/50 bg-rose-950/40',
      desc: 'Investigator deterministic thresholds & OFAC sanctions filters',
    },
  ];

  return (
    <div className="flex flex-col space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
          Rank Sorting Heuristic Stream:
        </span>
        <span className="text-[10px] font-mono text-slate-500">
          Weights dynamically normalized in composite engine
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {streams.map((s) => {
          const Icon = s.icon;
          const isActive = activeStream === s.id;
          const weight = streamWeights[s.id];

          return (
            <button
              key={s.id}
              onClick={() => onStreamChange(s.id)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-mono transition cursor-pointer ${
                isActive
                  ? `${s.color} font-semibold ring-1 ring-cyan-500/30`
                  : 'bg-[#0f172a] border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
              title={s.desc}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{s.label}</span>
              {s.id !== 'composite' && (
                <span className="text-[10px] opacity-70 border-l border-slate-700 pl-1.5 ml-1">
                  {(weight * 100).toFixed(0)}%
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
