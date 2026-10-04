import React, { useState } from 'react';
import {
  X,
  Copy,
  Check,
  Globe,
  Wallet,
  FileCode,
  ArrowRight,
  ArrowLeft,
  Activity,
  Layers,
  ExternalLink,
  ChevronRight,
} from 'lucide-react';
import type { GraphNode, GraphEdge } from '../../types/graph';
import { RiskBadge, truncateHash } from './CustomNodes';

interface NodeInspectorDrawerProps {
  selectedNode: GraphNode | null;
  allEdges: GraphEdge[];
  allNodes: GraphNode[];
  onClose: () => void;
  onSelectNode: (nodeId: string) => void;
}

export const NodeInspectorDrawer: React.FC<NodeInspectorDrawerProps> = ({
  selectedNode,
  allEdges,
  allNodes,
  onClose,
  onSelectNode,
}) => {
  const [copied, setCopied] = useState(false);

  if (!selectedNode) return null;

  const attrs = selectedNode.attributes || {};
  const isWallet = selectedNode.type === 'wallet';
  const isTx = selectedNode.type === 'transaction';
  const isIp = selectedNode.type === 'ip';

  // Compute incoming and outgoing edges for this node
  const incomingEdges = allEdges.filter((e) => e.target === selectedNode.id);
  const outgoingEdges = allEdges.filter((e) => e.source === selectedNode.id);

  // Compute in/out degree
  const inDegree = incomingEdges.length;
  const outDegree = outgoingEdges.length;

  // Approximate or provided PageRank
  const pageRank = typeof attrs.pagerank === 'number'
    ? attrs.pagerank.toFixed(4)
    : ((inDegree * 1.5 + outDegree) / Math.max(1, allNodes.length * 0.5)).toFixed(3);

  // Resolve connected counterparties
  const nodeLookup = new Map<string, GraphNode>();
  allNodes.forEach((n) => nodeLookup.set(n.id, n));

  const incomingCounterparties = incomingEdges.map((e) => ({
    edge: e,
    node: nodeLookup.get(e.source),
    direction: 'in' as const,
  }));

  const outgoingCounterparties = outgoingEdges.map((e) => ({
    edge: e,
    node: nodeLookup.get(e.target),
    direction: 'out' as const,
  }));

  const rawEntityId =
    attrs.address || attrs.txid || attrs.ip || selectedNode.label || selectedNode.id;

  const handleCopy = () => {
    navigator.clipboard.writeText(String(rawEntityId));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <aside className="fixed top-0 right-0 w-96 h-screen bg-slate-950/95 backdrop-blur-xl border-l border-slate-800 shadow-2xl z-50 flex flex-col font-sans transition-all duration-300">
      {/* Drawer Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800/80 bg-slate-900/60">
        <div className="flex items-center gap-2">
          <div
            className={`p-1.5 rounded-md ${
              isWallet
                ? 'bg-sky-500/20 text-sky-400'
                : isTx
                ? 'bg-indigo-500/20 text-indigo-400'
                : 'bg-emerald-500/20 text-emerald-400'
            }`}
          >
            {isWallet ? (
              <Wallet className="w-4 h-4" />
            ) : isTx ? (
              <FileCode className="w-4 h-4" />
            ) : (
              <Globe className="w-4 h-4" />
            )}
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Entity Inspector
            </h3>
            <span className="text-[11px] font-mono text-slate-500">
              {selectedNode.type.toUpperCase()}
            </span>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition-colors"
          title="Close Inspector"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Drawer Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {/* Entity Identifier Card & Copy */}
        <div className="bg-slate-900/90 rounded-lg p-3.5 border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Entity ID / Hash</span>
            <RiskBadge score={attrs.risk_score} />
          </div>

          <div className="flex items-center justify-between gap-2 bg-slate-950 p-2 rounded border border-slate-800/60">
            <code className="text-xs font-mono text-sky-300 break-all select-all">
              {String(rawEntityId)}
            </code>
            <button
              onClick={handleCopy}
              className="p-1.5 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded transition-all flex-shrink-0"
              title="Copy to clipboard"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Network & Graph Centrality Stats */}
        <div className="space-y-2">
          <h4 className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-sky-400" />
            Graph Topology Centrality
          </h4>
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800/70 text-center">
              <span className="text-[10px] text-slate-500 uppercase block font-sans">In Degree</span>
              <span className="text-sm font-bold font-mono text-slate-200">{inDegree}</span>
            </div>
            <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800/70 text-center">
              <span className="text-[10px] text-slate-500 uppercase block font-sans">Out Degree</span>
              <span className="text-sm font-bold font-mono text-slate-200">{outDegree}</span>
            </div>
            <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800/70 text-center">
              <span className="text-[10px] text-slate-500 uppercase block font-sans">PageRank</span>
              <span className="text-sm font-bold font-mono text-indigo-300">{pageRank}</span>
            </div>
          </div>
        </div>

        {/* Node-Specific Forensic Attributes */}
        <div className="space-y-2">
          <h4 className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            Forensic Metadata
          </h4>

          <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-800/70 space-y-2.5 text-xs font-mono">
            {isWallet && (
              <>
                <div className="flex justify-between border-b border-slate-800/50 pb-1.5">
                  <span className="text-slate-400 font-sans">Balance:</span>
                  <span className="text-slate-200 font-semibold">
                    {attrs.balance !== undefined ? `${Number(attrs.balance).toFixed(4)} BTC` : '—'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800/50 pb-1.5">
                  <span className="text-slate-400 font-sans">Balance Change:</span>
                  <span
                    className={
                      Number(attrs.balance_change) > 0
                        ? 'text-emerald-400 font-semibold'
                        : Number(attrs.balance_change) < 0
                        ? 'text-rose-400 font-semibold'
                        : 'text-slate-300'
                    }
                  >
                    {attrs.balance_change !== undefined
                      ? `${Number(attrs.balance_change) > 0 ? '+' : ''}${Number(attrs.balance_change).toFixed(4)} BTC`
                      : '—'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800/50 pb-1.5">
                  <span className="text-slate-400 font-sans">Mixer Flag:</span>
                  <span className={attrs.is_mixer ? 'text-amber-400 font-bold' : 'text-slate-500'}>
                    {attrs.is_mixer ? 'YES (Detected)' : 'NO'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans">Sanctions Match:</span>
                  <span className={attrs.is_sanctioned ? 'text-rose-400 font-bold' : 'text-slate-500'}>
                    {attrs.is_sanctioned ? 'OFAC MATCH' : 'CLEAN'}
                  </span>
                </div>
              </>
            )}

            {isTx && (
              <>
                <div className="flex justify-between border-b border-slate-800/50 pb-1.5">
                  <span className="text-slate-400 font-sans">Transacted Volume:</span>
                  <span className="text-slate-200 font-semibold">
                    {attrs.amount_btc || attrs.total_output
                      ? `${Number(attrs.amount_btc || attrs.total_output).toFixed(4)} BTC`
                      : '—'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800/50 pb-1.5">
                  <span className="text-slate-400 font-sans">Fee:</span>
                  <span className="text-slate-300">
                    {attrs.fee ? `${(Number(attrs.fee) * 1000).toFixed(3)} mBTC` : '—'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800/50 pb-1.5">
                  <span className="text-slate-400 font-sans">Script Type:</span>
                  <span className="text-slate-300 font-mono">{attrs.script_type || 'P2WPKH'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans">CoinJoin Tumbler:</span>
                  <span className={attrs.is_coinjoin ? 'text-amber-400 font-bold' : 'text-slate-500'}>
                    {attrs.is_coinjoin ? 'DETECTED' : 'STANDARD'}
                  </span>
                </div>
              </>
            )}

            {isIp && (
              <>
                <div className="flex justify-between border-b border-slate-800/50 pb-1.5">
                  <span className="text-slate-400 font-sans">Country:</span>
                  <span className="text-slate-200">
                    {attrs.country_name || attrs.country || 'Global'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800/50 pb-1.5">
                  <span className="text-slate-400 font-sans">Autonomous System:</span>
                  <span className="text-emerald-400">{attrs.asn ? `AS${attrs.asn}` : '—'}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/50 pb-1.5">
                  <span className="text-slate-400 font-sans">Tor Exit Node:</span>
                  <span className={attrs.tor_exit_node ? 'text-rose-400 font-bold' : 'text-slate-500'}>
                    {attrs.tor_exit_node ? 'CONFIRMED' : 'NO'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans">ISP / Org:</span>
                  <span className="text-slate-300 truncate max-w-[170px]" title={String(attrs.asn_org || attrs.isp)}>
                    {attrs.asn_org || attrs.isp || '—'}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Connected Counterparties List */}
        <div className="space-y-3">
          <h4 className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <ExternalLink className="w-3.5 h-3.5 text-emerald-400" />
              Connected Counterparties
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              {incomingCounterparties.length + outgoingCounterparties.length} Links
            </span>
          </h4>

          {/* Incoming Sources */}
          {incomingCounterparties.length > 0 && (
            <div className="space-y-1.5">
              <div className="text-[10px] uppercase font-bold text-sky-400 flex items-center gap-1 font-mono">
                <ArrowLeft className="w-3 h-3" /> Inflow Sources
              </div>
              {incomingCounterparties.map(({ edge, node }) => {
                const partnerLabel = node?.label || edge.source;
                return (
                  <div
                    key={edge.id}
                    onClick={() => node && onSelectNode(node.id)}
                    className="flex items-center justify-between p-2 rounded bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800/80 cursor-pointer transition-colors group"
                  >
                    <div className="min-w-0 flex items-center gap-1.5">
                      <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-sky-400 transition-colors" />
                      <div className="truncate">
                        <div className="text-xs font-mono text-slate-200 group-hover:text-sky-300">
                          {truncateHash(partnerLabel, 8, 6)}
                        </div>
                        <span className="text-[9px] text-slate-500 font-sans">
                          {edge.type.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                    {edge.amount && (
                      <span className="text-[11px] font-mono font-semibold text-emerald-400 flex-shrink-0">
                        +{edge.amount.toFixed(3)} BTC
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Outgoing Destinations */}
          {outgoingCounterparties.length > 0 && (
            <div className="space-y-1.5 pt-2">
              <div className="text-[10px] uppercase font-bold text-indigo-400 flex items-center gap-1 font-mono">
                <ArrowRight className="w-3 h-3" /> Outflow Destinations
              </div>
              {outgoingCounterparties.map(({ edge, node }) => {
                const partnerLabel = node?.label || edge.target;
                return (
                  <div
                    key={edge.id}
                    onClick={() => node && onSelectNode(node.id)}
                    className="flex items-center justify-between p-2 rounded bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800/80 cursor-pointer transition-colors group"
                  >
                    <div className="min-w-0 flex items-center gap-1.5">
                      <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-indigo-400 transition-colors" />
                      <div className="truncate">
                        <div className="text-xs font-mono text-slate-200 group-hover:text-indigo-300">
                          {truncateHash(partnerLabel, 8, 6)}
                        </div>
                        <span className="text-[9px] text-slate-500 font-sans">
                          {edge.type.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                    {edge.amount && (
                      <span className="text-[11px] font-mono font-semibold text-rose-400 flex-shrink-0">
                        -{edge.amount.toFixed(3)} BTC
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {incomingCounterparties.length === 0 && outgoingCounterparties.length === 0 && (
            <div className="text-center py-4 text-xs text-slate-500">
              No direct topological counterparties found.
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
