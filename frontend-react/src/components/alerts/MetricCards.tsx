import React from 'react';
import { AlertOctagon, Flame, ShieldAlert, AlertCircle, TrendingUp } from 'lucide-react';
import type { ForensicAlert } from '../../types/forensics';

interface MetricCardsProps {
  alerts: ForensicAlert[];
}

export const MetricCards: React.FC<MetricCardsProps> = ({ alerts }) => {
  const total = alerts.length;
  const critical = alerts.filter((a) => a.severity === 'CRITICAL').length;
  const high = alerts.filter((a) => a.severity === 'HIGH').length;
  const medium = alerts.filter((a) => a.severity === 'MEDIUM').length;

  const totalVolumeBtc = alerts.reduce((acc, a) => acc + a.amountBtc, 0);

  const metrics = [
    {
      label: 'Total Flagged Entities',
      value: total,
      subtext: `${totalVolumeBtc.toFixed(2)} BTC exposed`,
      icon: AlertOctagon,
      textColor: 'text-slate-100',
      borderColor: 'border-slate-800',
      badgeBg: 'bg-slate-800 text-slate-300',
      trend: '+12% vs prior block window',
    },
    {
      label: 'Critical Heuristic Anomalies',
      value: critical,
      subtext: 'Score >= 0.85 or sanction hit',
      icon: Flame,
      textColor: 'text-rose-400',
      borderColor: 'border-rose-900/40',
      badgeBg: 'bg-rose-950/60 text-rose-300 border border-rose-800/60',
      trend: 'Immediate freezing advised',
    },
    {
      label: 'High Probability ML Hits',
      value: high,
      subtext: '0.65 <= Composite < 0.85',
      icon: ShieldAlert,
      textColor: 'text-amber-400',
      borderColor: 'border-amber-900/40',
      badgeBg: 'bg-amber-950/60 text-amber-300 border border-amber-800/60',
      trend: 'Peeling chain / mixer signatures',
    },
    {
      label: 'Medium Risk Deviations',
      value: medium,
      subtext: '0.40 <= Composite < 0.65',
      icon: AlertCircle,
      textColor: 'text-cyan-400',
      borderColor: 'border-cyan-900/40',
      badgeBg: 'bg-cyan-950/60 text-cyan-300 border border-cyan-800/60',
      trend: 'Statistical outlier velocity',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {metrics.map((m) => {
        const Icon = m.icon;
        return (
          <div
            key={m.label}
            className={`bg-[#0f172a] rounded-lg p-3.5 border ${m.borderColor} shadow-sm relative overflow-hidden flex flex-col justify-between`}
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
                  {m.label}
                </span>
                <Icon className={`w-4 h-4 ${m.textColor}`} />
              </div>
              <div className="mt-2 flex items-baseline space-x-2">
                <span className={`text-2xl font-bold font-mono ${m.textColor}`}>
                  {m.value.toLocaleString()}
                </span>
                <span className="text-[11px] font-mono text-slate-500">{m.subtext}</span>
              </div>
            </div>

            <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono text-slate-500">
              <span className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3 text-slate-500" />
                <span>{m.trend}</span>
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
