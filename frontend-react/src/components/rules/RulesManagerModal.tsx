import React, { useState } from 'react';
import type { CustomRule, AlertSeverity } from '../../types/forensics';
import { X, Plus, Trash2, Check, Scale } from 'lucide-react';

interface RulesManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  rules: CustomRule[];
  onSaveRules: (rules: CustomRule[]) => void;
}

export const RulesManagerModal: React.FC<RulesManagerModalProps> = ({
  isOpen,
  onClose,
  rules,
  onSaveRules,
}) => {
  const [activeRules, setActiveRules] = useState<CustomRule[]>(rules);
  const [newRule, setNewRule] = useState<Partial<CustomRule>>({
    name: '',
    target: 'TRANSACTION',
    field: 'amount_btc',
    operator: '>',
    threshold: 10,
    severity: 'HIGH',
    weight: 0.25,
    isActive: true,
  });

  if (!isOpen) return null;

  const handleAddRule = () => {
    if (!newRule.name) return;
    const rule: CustomRule = {
      id: `rule-${Date.now()}`,
      name: newRule.name || 'Untitled Policy Rule',
      target: newRule.target || 'TRANSACTION',
      field: newRule.field || 'amount_btc',
      operator: newRule.operator || '>',
      threshold: newRule.threshold || 0,
      severity: (newRule.severity as AlertSeverity) || 'MEDIUM',
      weight: Number(newRule.weight) || 0.2,
      isActive: true,
    };
    const updated = [...activeRules, rule];
    setActiveRules(updated);
    setNewRule({
      name: '',
      target: 'TRANSACTION',
      field: 'amount_btc',
      operator: '>',
      threshold: 10,
      severity: 'HIGH',
      weight: 0.25,
      isActive: true,
    });
  };

  const handleToggleRule = (id: string) => {
    setActiveRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, isActive: !r.isActive } : r))
    );
  };

  const handleDeleteRule = (id: string) => {
    setActiveRules((prev) => prev.filter((r) => r.id !== id));
  };

  const handleCommit = () => {
    onSaveRules(activeRules);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
      <div className="w-full max-w-3xl bg-[#0b1322] border border-slate-800 rounded-xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 bg-[#090e17] border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded bg-indigo-950/60 border border-indigo-800 text-indigo-400">
              <Scale className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100 font-mono">
                INVESTIGATOR CUSTOM RULES ENGINE
              </h3>
              <p className="text-[10px] text-slate-400 font-mono">
                Define deterministic behavioral thresholds and sanction-filter policies
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {/* Create New Rule Form */}
          <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-3.5 space-y-3">
            <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-semibold block">
              + Add Dynamic Rule Heuristic
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs font-mono">
              <div className="sm:col-span-2">
                <label className="text-[10px] text-slate-400 block mb-1">Rule Name</label>
                <input
                  type="text"
                  placeholder="e.g. Rapid Peeling Chain Velocity (> 15 hops)"
                  value={newRule.name || ''}
                  onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                  className="w-full bg-[#090e17] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Target Entity</label>
                <select
                  value={newRule.target}
                  onChange={(e) =>
                    setNewRule({ ...newRule, target: e.target.value as any })
                  }
                  className="w-full bg-[#090e17] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="TRANSACTION">Transaction</option>
                  <option value="ADDRESS">Address</option>
                  <option value="EDGE">Flow Edge</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Telemetry Field</label>
                <input
                  type="text"
                  placeholder="e.g. amount_btc, hop_count, fee_rate"
                  value={newRule.field || ''}
                  onChange={(e) => setNewRule({ ...newRule, field: e.target.value })}
                  className="w-full bg-[#090e17] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Operator</label>
                <select
                  value={newRule.operator}
                  onChange={(e) =>
                    setNewRule({ ...newRule, operator: e.target.value as any })
                  }
                  className="w-full bg-[#090e17] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value=">">&gt; Greater Than</option>
                  <option value="<">&lt; Less Than</option>
                  <option value="==">== Equals</option>
                  <option value="!=">!= Not Equal</option>
                  <option value="CONTAINS">Contains</option>
                  <option value="MATCHES_REGEX">Regex Match</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Threshold</label>
                <input
                  type="text"
                  placeholder="e.g. 50"
                  value={newRule.threshold}
                  onChange={(e) => setNewRule({ ...newRule, threshold: e.target.value })}
                  className="w-full bg-[#090e17] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Severity Flag</label>
                <select
                  value={newRule.severity}
                  onChange={(e) =>
                    setNewRule({ ...newRule, severity: e.target.value as AlertSeverity })
                  }
                  className="w-full bg-[#090e17] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Composite Weight (0.0-1.0)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={newRule.weight}
                  onChange={(e) => setNewRule({ ...newRule, weight: parseFloat(e.target.value) })}
                  className="w-full bg-[#090e17] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-end">
                <button
                  onClick={handleAddRule}
                  disabled={!newRule.name}
                  className="w-full py-1.5 px-3 rounded text-xs font-mono font-medium bg-cyan-600 hover:bg-cyan-500 text-white transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center space-x-1 cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Append Rule</span>
                </button>
              </div>
            </div>
          </div>

          {/* Active Rules List Table */}
          <div className="bg-[#0f172a] border border-slate-800 rounded-lg overflow-hidden">
            <div className="p-3 bg-[#090e17] border-b border-slate-800 flex items-center justify-between text-xs font-mono">
              <span className="text-slate-300 font-semibold uppercase tracking-wider">
                Configured Rule Policies ({activeRules.length})
              </span>
              <span className="text-slate-500">Live Evaluation</span>
            </div>

            <table className="w-full text-left text-xs font-mono">
              <thead className="text-[10px] text-slate-400 uppercase bg-[#090e17]/50 border-b border-slate-800">
                <tr>
                  <th className="py-2 px-3">State</th>
                  <th className="py-2 px-3">Rule Name</th>
                  <th className="py-2 px-3">Predicate</th>
                  <th className="py-2 px-3">Severity</th>
                  <th className="py-2 px-3 text-right">Weight</th>
                  <th className="py-2 px-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {activeRules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3">
                      <button
                        onClick={() => handleToggleRule(rule.id)}
                        className={`w-4 h-4 rounded flex items-center justify-center border transition ${
                          rule.isActive
                            ? 'bg-cyan-600 border-cyan-500 text-white'
                            : 'bg-slate-800 border-slate-700 text-transparent'
                        }`}
                      >
                        <Check className="w-3 h-3" />
                      </button>
                    </td>
                    <td className="py-2 px-3 font-medium text-slate-200">{rule.name}</td>
                    <td className="py-2 px-3 text-slate-400">
                      <code className="bg-slate-800 px-1 py-0.5 rounded text-[11px] text-cyan-300">
                        {rule.target}.{rule.field} {rule.operator} {rule.threshold}
                      </code>
                    </td>
                    <td className="py-2 px-3">
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded border font-semibold ${
                          rule.severity === 'CRITICAL'
                            ? 'bg-rose-950/60 text-rose-300 border-rose-800'
                            : rule.severity === 'HIGH'
                            ? 'bg-amber-950/60 text-amber-300 border-amber-800'
                            : 'bg-slate-800 text-slate-300 border-slate-700'
                        }`}
                      >
                        {rule.severity}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right text-slate-400 font-semibold">
                      {(rule.weight * 100).toFixed(0)}%
                    </td>
                    <td className="py-2 px-3 text-center">
                      <button
                        onClick={() => handleDeleteRule(rule.id)}
                        className="text-slate-500 hover:text-rose-400 transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-[#090e17] border-t border-slate-800 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded text-xs font-mono text-slate-400 hover:text-slate-200 border border-slate-800 hover:bg-slate-800 transition"
          >
            Cancel
          </button>
          <button
            onClick={handleCommit}
            className="px-4 py-1.5 rounded text-xs font-mono font-medium bg-cyan-600 hover:bg-cyan-500 text-white shadow transition cursor-pointer"
          >
            Apply & Recalculate Composite
          </button>
        </div>
      </div>
    </div>
  );
};
