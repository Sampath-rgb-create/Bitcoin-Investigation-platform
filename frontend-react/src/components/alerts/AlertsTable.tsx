import React from 'react';
import type { ForensicAlert, ScoreStream } from '../../types/forensics';
import { ExternalLink, ShieldCheck, Flame, AlertTriangle, AlertCircle } from 'lucide-react';

interface AlertsTableProps {
  alerts: ForensicAlert[];
  activeStream: ScoreStream;
  selectedAlertId: string | null;
  onSelectAlert: (alert: ForensicAlert) => void;
  onSendToGraphCanvas?: (alert: ForensicAlert) => void;
}

export const AlertsTable: React.FC<AlertsTableProps> = ({
  alerts,
  activeStream,
  selectedAlertId,
  onSelectAlert,
  onSendToGraphCanvas,
}) => {
  // Sort alerts dynamically by the active score stream
  const sortedAlerts = [...alerts].sort((a, b) => {
    let scoreA = 0;
    let scoreB = 0;
    switch (activeStream) {
      case 'supervised':
        scoreA = a.scores.supervisedMlScore;
        scoreB = b.scores.supervisedMlScore;
        break;
      case 'unsupervised':
        scoreA = a.scores.unsupervisedIfScore;
        scoreB = b.scores.unsupervisedIfScore;
        break;
      case 'graph_flow':
        scoreA = a.scores.graphFlowScore;
        scoreB = b.scores.graphFlowScore;
        break;
      case 'custom_rules':
        scoreA = a.scores.customRulesScore;
        scoreB = b.scores.customRulesScore;
        break;
      case 'composite':
      default:
        scoreA = a.scores.compositeScore;
        scoreB = b.scores.compositeScore;
        break;
    }
    return scoreB - scoreA;
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950/60 text-rose-300 border border-rose-800">
            <Flame className="w-2.5 h-2.5 text-rose-400" />
            CRIT
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-950/60 text-amber-300 border border-amber-800">
            <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
            HIGH
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-cyan-950/60 text-cyan-300 border border-cyan-800">
            <AlertCircle className="w-2.5 h-2.5 text-cyan-400" />
            MED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
            <ShieldCheck className="w-2.5 h-2.5" />
            LOW
          </span>
        );
    }
  };

  const getScoreValue = (alert: ForensicAlert) => {
    switch (activeStream) {
      case 'supervised':
        return alert.scores.supervisedMlScore;
      case 'unsupervised':
        return alert.scores.unsupervisedIfScore;
      case 'graph_flow':
        return alert.scores.graphFlowScore;
      case 'custom_rules':
        return alert.scores.customRulesScore;
      case 'composite':
      default:
        return alert.scores.compositeScore;
    }
  };

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-lg overflow-hidden flex flex-col">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#0b1322] text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800 select-none">
            <tr>
              <th className="py-2.5 px-3 font-medium">Rank</th>
              <th className="py-2.5 px-3 font-medium">Severity</th>
              <th className="py-2.5 px-3 font-medium">Transaction Hash / Target</th>
              <th className="py-2.5 px-3 font-medium text-right">Volume (BTC)</th>
              <th className="py-2.5 px-3 font-medium text-right">Volume (USD)</th>
              <th className="py-2.5 px-3 font-medium text-right">Active Stream Score</th>
              <th className="py-2.5 px-3 font-medium">Tags & Typology</th>
              <th className="py-2.5 px-3 font-medium text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80 font-mono text-slate-300">
            {sortedAlerts.map((alert, idx) => {
              const isSelected = selectedAlertId === alert.id;
              const activeScore = getScoreValue(alert);

              return (
                <tr
                  key={alert.id}
                  onClick={() => onSelectAlert(alert)}
                  className={`cursor-pointer transition-colors duration-100 ${
                    isSelected
                      ? 'bg-[#15233c] text-slate-100 font-medium'
                      : 'hover:bg-slate-800/40'
                  }`}
                >
                  {/* Rank */}
                  <td className="py-2 px-3 text-slate-500 font-mono text-[11px]">
                    #{String(idx + 1).padStart(2, '0')}
                  </td>

                  {/* Severity */}
                  <td className="py-2 px-3">{getSeverityBadge(alert.severity)}</td>

                  {/* Hash & Target Address */}
                  <td className="py-2 px-3">
                    <div className="flex flex-col">
                      <span className="text-cyan-300 hover:underline truncate max-w-[200px]">
                        {alert.txHash.slice(0, 10)}...{alert.txHash.slice(-8)}
                      </span>
                      <span className="text-[10px] text-slate-500 truncate max-w-[200px]">
                        addr: {alert.targetAddress.slice(0, 8)}...{alert.targetAddress.slice(-6)}
                      </span>
                    </div>
                  </td>

                  {/* BTC Amount */}
                  <td className="py-2 px-3 text-right text-slate-200 font-bold">
                    {alert.amountBtc.toFixed(4)} ₿
                  </td>

                  {/* USD Amount */}
                  <td className="py-2 px-3 text-right text-slate-400">
                    ${alert.amountUsd.toLocaleString()}
                  </td>

                  {/* Score with mini visual bar */}
                  <td className="py-2 px-3 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <div className="w-12 h-1.5 bg-slate-800 rounded-full overflow-hidden hidden sm:block">
                        <div
                          className={`h-full rounded-full ${
                            activeScore >= 0.8
                              ? 'bg-rose-500'
                              : activeScore >= 0.6
                              ? 'bg-amber-500'
                              : 'bg-cyan-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(5, activeScore * 100))}%` }}
                        ></div>
                      </div>
                      <span
                        className={`font-bold ${
                          activeScore >= 0.8
                            ? 'text-rose-400'
                            : activeScore >= 0.6
                            ? 'text-amber-400'
                            : 'text-cyan-400'
                        }`}
                      >
                        {(activeScore * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>

                  {/* Tags */}
                  <td className="py-2 px-3">
                    <div className="flex flex-wrap gap-1 max-w-[180px]">
                      {alert.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60"
                        >
                          {tag}
                        </span>
                      ))}
                      {alert.tags.length > 2 && (
                        <span className="text-[9px] text-slate-500">+{alert.tags.length - 2}</span>
                      )}
                    </div>
                  </td>

                  {/* Open Canvas CTA */}
                  <td className="py-2 px-3 text-center">
                    {onSendToGraphCanvas && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSendToGraphCanvas(alert);
                        }}
                        className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-cyan-300 transition"
                        title="Send UTXO flow to Graph Canvas"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
