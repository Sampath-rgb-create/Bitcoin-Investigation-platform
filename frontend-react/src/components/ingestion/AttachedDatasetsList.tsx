import React from 'react';
import { Database, FileText, CheckCircle2, AlertTriangle, Trash2, HardDrive } from 'lucide-react';
import type { AttachedDataset } from '../../types/forensics';

interface AttachedDatasetsListProps {
  datasets: AttachedDataset[];
  onRemoveDataset?: (name: string) => void;
  onRefreshStats?: () => void;
}

export const AttachedDatasetsList: React.FC<AttachedDatasetsListProps> = ({
  datasets,
  onRemoveDataset,
}) => {
  const totalRows = datasets.reduce((sum, d) => sum + d.rowsCount, 0);
  const totalBytes = datasets.reduce((sum, d) => sum + d.fileSizeBytes, 0);
  const totalMb = (totalBytes / (1024 * 1024)).toFixed(2);

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-3.5 bg-[#0b1322] border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Database className="w-4 h-4 text-cyan-400" />
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Active Forensic Datasets In-Memory
          </h4>
        </div>

        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="flex items-center space-x-1.5 text-slate-400">
            <HardDrive className="w-3.5 h-3.5 text-slate-500" />
            <span>Total Footprint:</span>
            <span className="text-slate-200 font-semibold">{totalMb} MB</span>
          </div>
          <div className="text-slate-400">
            <span>Cumulative Records:</span>{' '}
            <span className="text-cyan-400 font-semibold">{totalRows.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Dataset Table */}
      {datasets.length === 0 ? (
        <div className="p-8 text-center text-xs font-mono text-slate-500">
          No datasets currently bound to this forensic session. Drop canonical CSVs above.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#090e17] text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-4 font-medium">Dataset Type</th>
                <th className="py-2.5 px-4 font-medium">Physical File</th>
                <th className="py-2.5 px-4 font-medium text-right">Row Count</th>
                <th className="py-2.5 px-4 font-medium text-right">Size (MB)</th>
                <th className="py-2.5 px-4 font-medium">Status</th>
                <th className="py-2.5 px-4 font-medium">Indexed At</th>
                <th className="py-2.5 px-4 font-medium text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 font-mono text-slate-300">
              {datasets.map((dataset) => (
                <tr key={dataset.name} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 px-4 font-medium flex items-center space-x-2">
                    <FileText className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="capitalize">{dataset.type}</span>
                  </td>
                  <td className="py-2.5 px-4 text-slate-400 truncate max-w-[180px]">
                    {dataset.filename}
                  </td>
                  <td className="py-2.5 px-4 text-right text-slate-200 font-semibold">
                    {dataset.rowsCount.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-4 text-right text-slate-400">
                    {(dataset.fileSizeBytes / (1024 * 1024)).toFixed(2)}
                  </td>
                  <td className="py-2.5 px-4">
                    {dataset.status === 'READY' ? (
                      <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-300 border border-emerald-800/60">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        INDEXED
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded bg-amber-950/40 text-amber-300 border border-amber-800/60">
                        <AlertTriangle className="w-3 h-3 text-amber-400" />
                        {dataset.status}
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 px-4 text-slate-500 text-[11px]">
                    {dataset.uploadedAt}
                  </td>
                  <td className="py-2.5 px-4 text-center">
                    {onRemoveDataset && (
                      <button
                        onClick={() => onRemoveDataset(dataset.name)}
                        className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                        title="Detach Dataset"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
