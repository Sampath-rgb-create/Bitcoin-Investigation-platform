import React, { useState } from 'react';
import { Upload, FileCheck, ArrowUpRight, CheckCircle } from 'lucide-react';

export interface DropzoneConfig {
  id: 'transactions' | 'inputs' | 'outputs' | 'network';
  title: string;
  expectedFilename: string;
  description: string;
  requiredFields: string[];
}

interface CanonicalIngestionSuiteProps {
  onFilesCommitted: (files: Record<string, File>) => void;
  isProcessing?: boolean;
}

const CANONICAL_SCHEMAS: DropzoneConfig[] = [
  {
    id: 'transactions',
    title: 'Transactions Data',
    expectedFilename: 'transactions.csv',
    description: 'Tx-level telemetry: tx_hash, block_id, timestamp, fee, locktime.',
    requiredFields: ['tx_hash', 'block_height', 'timestamp', 'fee_sats'],
  },
  {
    id: 'inputs',
    title: 'Transaction Inputs',
    expectedFilename: 'inputs.csv',
    description: 'UTXO debits: prev_tx_hash, prev_output_index, script_sig, value.',
    requiredFields: ['tx_hash', 'prev_tx_hash', 'prev_output_index', 'address'],
  },
  {
    id: 'outputs',
    title: 'Transaction Outputs',
    expectedFilename: 'outputs.csv',
    description: 'UTXO credits: script_pubkey, address, satoshis, spent_status.',
    requiredFields: ['tx_hash', 'output_index', 'address', 'amount_sats'],
  },
  {
    id: 'network',
    title: 'Graph Adjacency Matrix',
    expectedFilename: 'network.csv',
    description: 'Peer-to-peer flow edges: source_addr, target_addr, weight, hop_count.',
    requiredFields: ['source', 'target', 'weight_btc', 'tx_count'],
  },
];

export const CanonicalIngestionSuite: React.FC<CanonicalIngestionSuiteProps> = ({
  onFilesCommitted,
  isProcessing = false,
}) => {
  const [stagedFiles, setStagedFiles] = useState<Record<string, File>>({});
  const [dragOverZone, setDragOverZone] = useState<string | null>(null);

  const handleFileDrop = (zoneId: string, fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    const file = fileList[0];
    setStagedFiles((prev) => ({
      ...prev,
      [zoneId]: file,
    }));
  };

  const handleCommit = () => {
    onFilesCommitted(stagedFiles);
  };

  const stagedCount = Object.keys(stagedFiles).length;
  const isReady = stagedCount > 0;

  return (
    <div className="space-y-4">
      {/* Banner / Instructions */}
      <div className="p-3.5 rounded bg-[#0b1322] border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>Canonical Forensic Ingestion Matrix</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
              CSV REQUIRED
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Drop or stage canonical Bitcoin ledger tables. The multi-stream heuristic engine correlates UTXOs across transactions, inputs, outputs, and edge networks.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <div className="text-right text-xs font-mono">
            <span className="text-slate-400">Staged: </span>
            <span className={`font-semibold ${stagedCount === 4 ? 'text-emerald-400' : 'text-cyan-300'}`}>
              {stagedCount} / 4 datasets
            </span>
          </div>
          <button
            onClick={handleCommit}
            disabled={!isReady || isProcessing}
            className="flex items-center space-x-1.5 px-4 py-2 rounded text-xs font-mono font-medium bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_15px_rgba(6,182,212,0.3)] transition disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            <span>{isProcessing ? 'Ingesting Pipeline...' : 'Start Extraction & Analysis'}</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 4 Canonical Dropzone Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {CANONICAL_SCHEMAS.map((zone) => {
          const file = stagedFiles[zone.id];
          const isOver = dragOverZone === zone.id;

          return (
            <div
              key={zone.id}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOverZone(zone.id);
              }}
              onDragLeave={() => setDragOverZone(null)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOverZone(null);
                handleFileDrop(zone.id, e.dataTransfer.files);
              }}
              className={`relative border rounded-lg p-4 transition-all duration-150 flex flex-col justify-between ${
                file
                  ? 'bg-[#0c182a] border-cyan-500/50 shadow-[0_0_10px_rgba(56,189,248,0.08)]'
                  : isOver
                  ? 'bg-slate-800/80 border-cyan-400 border-dashed scale-[1.01]'
                  : 'bg-[#0f172a] border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-semibold">
                      Target: {zone.expectedFilename}
                    </span>
                    <h4 className="text-sm font-medium text-slate-100 mt-0.5">{zone.title}</h4>
                  </div>
                  {file ? (
                    <div className="flex items-center space-x-1 text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800 text-[10px] font-mono">
                      <CheckCircle className="w-3 h-3" />
                      <span>STAGED</span>
                    </div>
                  ) : (
                    <span className="text-[10px] font-mono text-slate-500 bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700/60">
                      EMPTY
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-400 mt-2">{zone.description}</p>

                {/* Schema badge tags */}
                <div className="mt-3 flex flex-wrap gap-1">
                  {zone.requiredFields.map((field) => (
                    <span
                      key={field}
                      className="text-[10px] font-mono bg-slate-800/80 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700/50"
                    >
                      {field}
                    </span>
                  ))}
                </div>
              </div>

              {/* Upload Input Drop Target */}
              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                {file ? (
                  <div className="flex items-center space-x-2 text-xs font-mono text-slate-300 truncate max-w-[200px]">
                    <FileCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span className="truncate">{file.name}</span>
                    <span className="text-[10px] text-slate-500">
                      ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                    </span>
                  </div>
                ) : (
                  <div className="text-[11px] font-mono text-slate-500 flex items-center gap-1.5">
                    <Upload className="w-3.5 h-3.5 text-slate-400" />
                    <span>Drop {zone.expectedFilename} or</span>
                  </div>
                )}

                <label className="cursor-pointer text-xs font-mono text-cyan-400 hover:text-cyan-300 underline underline-offset-2">
                  <span>{file ? 'Change file' : 'Browse local'}</span>
                  <input
                    type="file"
                    accept=".csv"
                    className="hidden"
                    onChange={(e) => handleFileDrop(zone.id, e.target.files)}
                  />
                </label>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
