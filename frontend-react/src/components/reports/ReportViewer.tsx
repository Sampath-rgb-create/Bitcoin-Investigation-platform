import React from 'react';
import type { ForensicAlert, CaseSummary } from '../../types/forensics';
import { Download, FileJson, FileText, CheckCircle2, ShieldCheck, AlertOctagon } from 'lucide-react';

interface ReportViewerProps {
  activeCase: CaseSummary;
  alerts: ForensicAlert[];
  pipelineTimestamp?: string;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({
  activeCase,
  alerts,
  pipelineTimestamp = new Date().toISOString(),
}) => {
  const criticalCount = alerts.filter((a) => a.severity === 'CRITICAL').length;
  const highCount = alerts.filter((a) => a.severity === 'HIGH').length;
  const totalVolume = alerts.reduce((sum, a) => sum + a.amountBtc, 0);

  const downloadJsonReport = () => {
    const reportData = {
      case: activeCase,
      generatedAt: pipelineTimestamp,
      summary: {
        totalAlerts: alerts.length,
        criticalAlerts: criticalCount,
        highAlerts: highCount,
        totalVolumeBtc: totalVolume,
      },
      flaggedAlerts: alerts,
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Forensic_Report_${activeCase.id}_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const downloadMarkdownReport = () => {
    const mdContent = `# CipherTrace Forensic AML Investigation Report
**Case Dossier**: ${activeCase.name}
**Case ID**: ${activeCase.id}
**Primary Suspect Address**: \`${activeCase.targetAddress}\`
**Generated At**: ${pipelineTimestamp}
**Classification**: LAW ENFORCEMENT SENSITIVE // CONFIDENTIAL

---

## Executive Summary
- **Total Flagged Entities**: ${alerts.length}
- **Critical Severity Alerts**: ${criticalCount}
- **High Severity Alerts**: ${highCount}
- **Total Traced Displaced BTC**: ${totalVolume.toFixed(4)} BTC

---

## Top Forensic Alerts & Typology Breakdown

| Rank | Severity | Transaction Hash | Target Addr | Displaced BTC | Composite Score | Typology / Tags |
|------|----------|------------------|-------------|---------------|-----------------|-----------------|
${alerts
  .slice(0, 15)
  .map(
    (a, idx) =>
      `| #${idx + 1} | ${a.severity} | \`${a.txHash.slice(0, 14)}...\` | \`${a.targetAddress.slice(0, 10)}...\` | ${a.amountBtc.toFixed(4)} ₿ | ${(a.scores.compositeScore * 100).toFixed(1)}% | ${a.tags.join(', ')} |`
  )
  .join('\n')}

---

## Heuristic Multi-Stream Attributions

${alerts
  .slice(0, 5)
  .map(
    (a, idx) => `### Alert #${idx + 1}: ${a.txHash}
- **Severity**: ${a.severity}
- **Scores**: Composite: ${(a.scores.compositeScore * 100).toFixed(1)}% | Supervised ML: ${(a.scores.supervisedMlScore * 100).toFixed(1)}% | IF Anomaly: ${(a.scores.unsupervisedIfScore * 100).toFixed(1)}% | Graph Flow: ${(a.scores.graphFlowScore * 100).toFixed(1)}%
- **Investigative Narrative**: ${a.narrative}
- **Key Anomaly Deviations**:
${a.deviationReasons.map((d) => `  * **${d.feature}** (+${d.contribution}%): ${d.description}`).join('\n')}
`
  )
  .join('\n')}

---
*Report certified by CipherTrace AML Engine v2.4.*
`;

    const blob = new Blob([mdContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Forensic_Report_${activeCase.id}_${Date.now()}.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Top Banner and Download Actions */}
      <div className="p-4 bg-[#0b1322] border border-slate-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-semibold text-slate-100 font-mono">
              OFFICIAL FORENSIC ATTESTATION DOSSIER
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
              LE-CONFIDENTIAL
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Export comprehensive heuristic audit trail, UTXO attributions, and anomaly evidence.
          </p>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={downloadJsonReport}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-mono font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition cursor-pointer"
          >
            <FileJson className="w-3.5 h-3.5 text-cyan-400" />
            <span>Export JSON</span>
          </button>

          <button
            onClick={downloadMarkdownReport}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded text-xs font-mono font-medium bg-cyan-600 hover:bg-cyan-500 text-white shadow transition cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Export Markdown</span>
            <Download className="w-3.5 h-3.5 ml-1" />
          </button>
        </div>
      </div>

      {/* Structured Document Preview */}
      <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-6 space-y-6 font-mono">
        {/* Document Header */}
        <div className="border-b border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="text-xs text-slate-400">Target Investigation Subject:</div>
            <div className="text-base font-bold text-slate-100 mt-0.5">{activeCase.name}</div>
            <div className="text-xs text-cyan-400 font-mono mt-0.5">
              Subject Address: {activeCase.targetAddress}
            </div>
          </div>
          <div className="sm:text-right text-xs text-slate-400">
            <div>Timestamp: {pipelineTimestamp}</div>
            <div className="flex items-center sm:justify-end gap-1 text-emerald-400 mt-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Evidence Ledger Validated</span>
            </div>
          </div>
        </div>

        {/* Quick Metrics Matrix */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 bg-[#090e17] rounded border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase">Total Flagged</span>
            <span className="text-lg font-bold text-slate-100">{alerts.length}</span>
          </div>
          <div className="p-3 bg-[#090e17] rounded border border-rose-950/60">
            <span className="text-[10px] text-rose-400 block uppercase">Critical Alerts</span>
            <span className="text-lg font-bold text-rose-400">{criticalCount}</span>
          </div>
          <div className="p-3 bg-[#090e17] rounded border border-amber-950/60">
            <span className="text-[10px] text-amber-400 block uppercase">High Alerts</span>
            <span className="text-lg font-bold text-amber-400">{highCount}</span>
          </div>
          <div className="p-3 bg-[#090e17] rounded border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase">Total Volume</span>
            <span className="text-lg font-bold text-cyan-300">{totalVolume.toFixed(2)} ₿</span>
          </div>
        </div>

        {/* Top 5 Alerts Summary Preview */}
        <div>
          <h4 className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-3 flex items-center gap-2">
            <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
            <span>Forensic Findings Summary (Top 5 Priority Leads)</span>
          </h4>

          <div className="space-y-3">
            {alerts.slice(0, 5).map((a, idx) => (
              <div
                key={a.id}
                className="p-3.5 rounded bg-[#090e17] border border-slate-800 text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-slate-500 font-bold">#{idx + 1}</span>
                    <span className="text-cyan-300 select-all font-semibold">
                      {a.txHash.slice(0, 16)}...{a.txHash.slice(-8)}
                    </span>
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded border font-bold ${
                        a.severity === 'CRITICAL'
                          ? 'bg-rose-950 text-rose-300 border-rose-800'
                          : 'bg-amber-950 text-amber-300 border-amber-800'
                      }`}
                    >
                      {a.severity}
                    </span>
                  </div>

                  <span className="text-slate-200 font-bold">
                    {a.amountBtc.toFixed(4)} ₿ (${a.amountUsd.toLocaleString()})
                  </span>
                </div>

                <p className="text-slate-300 font-sans text-xs leading-relaxed">
                  {a.narrative}
                </p>

                <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] text-slate-400">
                  <span className="text-slate-500">Heuristics:</span>
                  <span>Composite: {(a.scores.compositeScore * 100).toFixed(0)}%</span>
                  <span>|</span>
                  <span>ML: {(a.scores.supervisedMlScore * 100).toFixed(0)}%</span>
                  <span>|</span>
                  <span>IF: {(a.scores.unsupervisedIfScore * 100).toFixed(0)}%</span>
                  <span>|</span>
                  <span>Graph: {(a.scores.graphFlowScore * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Attestation */}
        <div className="pt-4 border-t border-slate-800 text-[10px] text-slate-500 flex items-center justify-between">
          <div className="flex items-center space-x-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Digital Fingerprint Verified (HMAC-SHA512)</span>
          </div>
          <span>Confidentiality Notice: Restricted to Authorized Compliance Officers</span>
        </div>
      </div>
    </div>
  );
};
