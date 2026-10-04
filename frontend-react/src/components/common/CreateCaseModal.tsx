import React, { useState } from 'react';
import { X, FolderPlus, Key } from 'lucide-react';
import type { CaseSummary } from '../../types/forensics';

interface CreateCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateCase: (newCase: CaseSummary) => void;
}

export const CreateCaseModal: React.FC<CreateCaseModalProps> = ({
  isOpen,
  onClose,
  onCreateCase,
}) => {
  const [caseName, setCaseName] = useState('');
  const [targetAddress, setTargetAddress] = useState('');
  const [description, setDescription] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!caseName.trim()) return;

    const newCase: CaseSummary = {
      id: `case-${Date.now()}`,
      name: caseName.trim(),
      targetAddress: targetAddress.trim() || '1UnknownTargetAddressUTXO',
      createdDate: new Date().toISOString().split('T')[0],
      status: 'ACTIVE',
      datasetCount: 0,
      alertCount: 0,
      criticalAlertCount: 0,
    };

    onCreateCase(newCase);
    setCaseName('');
    setTargetAddress('');
    setDescription('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg bg-[#0b1322] border border-slate-800 rounded-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 bg-[#090e17] border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded bg-cyan-950/60 border border-cyan-800 text-cyan-400">
              <FolderPlus className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100 font-mono">
                INITIALIZE FORENSIC CASE DOSSIER
              </h3>
              <p className="text-[10px] text-slate-400 font-mono">
                Create an isolated AML investigation workspace
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

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4 text-xs font-mono">
          <div>
            <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
              Case Operation Title *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Operation Silk Road Drain #2026"
              value={caseName}
              onChange={(e) => setCaseName(e.target.value)}
              className="w-full bg-[#090e17] border border-slate-700 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-sans text-xs"
            />
          </div>

          <div>
            <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1 flex items-center justify-between">
              <span>Primary Suspect Bitcoin Address</span>
              <span className="text-slate-500 text-[9px] font-mono">P2PKH / P2SH / Bech32</span>
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="e.g. bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
                value={targetAddress}
                onChange={(e) => setTargetAddress(e.target.value)}
                className="w-full bg-[#090e17] border border-slate-700 rounded pl-8 pr-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono text-xs"
              />
              <Key className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
            </div>
          </div>

          <div>
            <label className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
              Investigation Scope / Notes
            </label>
            <textarea
              rows={3}
              placeholder="Case briefing, seizure warrants, or ransomware incident notes..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-[#090e17] border border-slate-700 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-sans text-xs resize-none"
            />
          </div>

          <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded text-slate-400 hover:text-slate-200 border border-slate-800 hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!caseName.trim()}
              className="px-4 py-1.5 rounded font-medium bg-cyan-600 hover:bg-cyan-500 text-white shadow transition disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              Initialize Dossier
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
