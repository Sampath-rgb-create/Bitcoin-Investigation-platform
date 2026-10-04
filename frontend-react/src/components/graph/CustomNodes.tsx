import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import {
  Wallet,
  ArrowUpRight,
  ArrowDownLeft,
  ShieldAlert,
  AlertTriangle,
  Globe,
  Radio,
  FileCode,
  Layers,
  Flame,
} from 'lucide-react';
import type { GraphNode } from '../../types/graph';

// Truncate crypto address or hashes gracefully
export const truncateHash = (hash?: string, lead: number = 6, tail: number = 4): string => {
  if (!hash) return 'Unknown';
  if (hash.length <= lead + tail + 3) return hash;
  return `${hash.slice(0, lead)}...${hash.slice(-tail)}`;
};

// Render Risk Score Badge with glowing styling
export const RiskBadge: React.FC<{ score?: number }> = ({ score }) => {
  if (score === undefined || score === null) return null;
  const numScore = Math.max(0, Math.min(100, score <= 1 ? Math.round(score * 100) : Math.round(score)));

  let colorClasses = 'bg-emerald-950/80 text-emerald-400 border-emerald-700/50 shadow-emerald-900/30';

  if (numScore >= 80) {
    colorClasses = 'bg-rose-950/90 text-rose-400 border-rose-600/60 shadow-rose-900/50 animate-pulse';
  } else if (numScore >= 60) {
    colorClasses = 'bg-amber-950/90 text-amber-400 border-amber-600/60 shadow-amber-900/40';
  } else if (numScore >= 35) {
    colorClasses = 'bg-yellow-950/70 text-yellow-300 border-yellow-700/50 shadow-yellow-900/20';
  }

  return (
    <div
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold border shadow-sm ${colorClasses}`}
      title={`Risk Anomaly Score: ${numScore}%`}
    >
      {numScore >= 80 ? (
        <Flame className="w-2.5 h-2.5" />
      ) : numScore >= 35 ? (
        <AlertTriangle className="w-2.5 h-2.5" />
      ) : (
        <ShieldAlert className="w-2.5 h-2.5" />
      )}
      <span>{numScore}%</span>
    </div>
  );
};

// -------------------------------------------------------------
// 1. WALLET NODE
// -------------------------------------------------------------
export const WalletNode: React.FC<NodeProps> = memo(({ data, selected }) => {
  const nodeData = (data?.node as GraphNode) || {
    id: 'wallet:unknown',
    type: 'wallet',
    label: 'Unknown',
    attributes: {},
  };

  const attrs = nodeData.attributes || {};
  const rawAddr = (attrs.address as string) || nodeData.label || nodeData.id.replace(/^wallet:/, '');
  const displayAddr = truncateHash(rawAddr, 6, 6);
  const balance = typeof attrs.balance === 'number' ? attrs.balance : 0;
  const balanceChange = typeof attrs.balance_change === 'number' ? attrs.balance_change : null;
  const riskScore = typeof attrs.risk_score === 'number' ? attrs.risk_score : undefined;
  const isSanctioned = Boolean(attrs.is_sanctioned);
  const isMixer = Boolean(attrs.is_mixer);
  const isExchange = Boolean(attrs.is_exchange);

  return (
    <div
      className={`relative min-w-[210px] max-w-[260px] rounded-lg transition-all duration-200 select-none ${
        selected
          ? 'ring-2 ring-sky-400 shadow-lg shadow-sky-500/30 scale-[1.02] border-sky-400 bg-slate-900'
          : 'border-slate-800 hover:border-slate-700 bg-slate-950/95 hover:bg-slate-900/95'
      } border shadow-md backdrop-blur-md p-3 font-sans`}
    >
      {/* React Flow Source & Target Handles for Left-to-Right Money Flow */}
      <Handle
        type="target"
        position={Position.Left}
        id="in"
        className="!w-2.5 !h-2.5 !bg-sky-400 !border-2 !border-slate-950 !-left-1.5 transition-transform hover:scale-125"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="out"
        className="!w-2.5 !h-2.5 !bg-sky-400 !border-2 !border-slate-950 !-right-1.5 transition-transform hover:scale-125"
      />

      {/* Top Header: Icon, Entity Type, Risk Badge */}
      <div className="flex items-center justify-between gap-1.5 mb-2 pb-1.5 border-b border-slate-800/80">
        <div className="flex items-center gap-1.5 min-w-0">
          <div
            className={`p-1.5 rounded-md flex-shrink-0 ${
              isSanctioned
                ? 'bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/40'
                : isMixer
                ? 'bg-amber-500/20 text-amber-400 ring-1 ring-amber-500/40'
                : 'bg-sky-500/15 text-sky-400 ring-1 ring-sky-500/30'
            }`}
          >
            <Wallet className="w-3.5 h-3.5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[10px] font-bold tracking-wider uppercase text-slate-400 truncate">
              {isSanctioned
                ? 'Sanctioned Entity'
                : isMixer
                ? 'Tumbler / Mixer'
                : isExchange
                ? 'Exchange Clustered'
                : 'Wallet Address'}
            </span>
          </div>
        </div>

        <RiskBadge score={riskScore} />
      </div>

      {/* Address Hash Row */}
      <div className="mb-2">
        <div
          className="text-xs font-mono font-medium text-slate-200 hover:text-sky-300 transition-colors cursor-pointer truncate"
          title={rawAddr}
        >
          {displayAddr}
        </div>
      </div>

      {/* Metrics Row: Balance & Change */}
      <div className="grid grid-cols-2 gap-2 text-[11px] bg-slate-900/80 rounded p-1.5 border border-slate-800/60 font-mono">
        <div>
          <div className="text-[9px] uppercase tracking-wider text-slate-500 font-sans">Balance</div>
          <div className="text-slate-200 font-semibold truncate">
            {balance > 0 ? `${balance.toFixed(4)}` : '0.0000'}{' '}
            <span className="text-[9px] text-sky-400 font-sans">BTC</span>
          </div>
        </div>

        <div>
          <div className="text-[9px] uppercase tracking-wider text-slate-500 font-sans">Net Flow</div>
          {balanceChange !== null ? (
            <div
              className={`flex items-center gap-0.5 font-semibold truncate ${
                balanceChange > 0
                  ? 'text-emerald-400'
                  : balanceChange < 0
                  ? 'text-rose-400'
                  : 'text-slate-400'
              }`}
            >
              {balanceChange > 0 ? (
                <ArrowDownLeft className="w-3 h-3 flex-shrink-0" />
              ) : (
                <ArrowUpRight className="w-3 h-3 flex-shrink-0" />
              )}
              <span>{Math.abs(balanceChange).toFixed(3)}</span>
            </div>
          ) : (
            <span className="text-slate-500">—</span>
          )}
        </div>
      </div>

      {/* Sanctioned / Warning Tag if applicable */}
      {isSanctioned && (
        <div className="mt-2 text-[10px] font-sans font-medium text-rose-300 bg-rose-950/60 border border-rose-800/50 rounded px-1.5 py-0.5 flex items-center gap-1">
          <ShieldAlert className="w-3 h-3 flex-shrink-0 text-rose-400" />
          <span className="truncate">OFAC Sanction List Hit</span>
        </div>
      )}
    </div>
  );
});
WalletNode.displayName = 'WalletNode';

// -------------------------------------------------------------
// 2. TRANSACTION NODE
// -------------------------------------------------------------
export const TransactionNode: React.FC<NodeProps> = memo(({ data, selected }) => {
  const nodeData = (data?.node as GraphNode) || {
    id: 'transaction:unknown',
    type: 'transaction',
    label: 'Unknown TX',
    attributes: {},
  };

  const attrs = nodeData.attributes || {};
  const rawTxid = (attrs.txid as string) || nodeData.label || nodeData.id.replace(/^transaction:/, '');
  const displayTxid = truncateHash(rawTxid, 7, 5);
  const volumeBtc =
    typeof attrs.amount_btc === 'number'
      ? attrs.amount_btc
      : typeof attrs.total_output === 'number'
      ? attrs.total_output
      : typeof attrs.total_input === 'number'
      ? attrs.total_input
      : 0;
  const fee = typeof attrs.fee === 'number' ? attrs.fee : typeof attrs.fee_sats === 'number' ? attrs.fee_sats / 1e8 : 0;
  const riskScore = typeof attrs.risk_score === 'number' ? attrs.risk_score : undefined;
  const isCoinJoin = Boolean(attrs.is_coinjoin || attrs.script_type === 'coinjoin');

  return (
    <div
      className={`relative min-w-[210px] max-w-[250px] rounded-lg transition-all duration-200 select-none ${
        selected
          ? 'ring-2 ring-indigo-400 shadow-lg shadow-indigo-500/30 scale-[1.02] border-indigo-400 bg-slate-900'
          : 'border-indigo-900/50 hover:border-indigo-700/80 bg-slate-950/95 hover:bg-slate-900/95'
      } border shadow-md backdrop-blur-md p-3 font-sans`}
    >
      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        id="in"
        className="!w-2.5 !h-2.5 !bg-indigo-400 !border-2 !border-slate-950 !-left-1.5 transition-transform hover:scale-125"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="out"
        className="!w-2.5 !h-2.5 !bg-indigo-400 !border-2 !border-slate-950 !-right-1.5 transition-transform hover:scale-125"
      />
      {/* Extra Top handle for IP association links */}
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        className="!w-2.5 !h-2.5 !bg-amber-400 !border-2 !border-slate-950 !-top-1.5 transition-transform hover:scale-125"
      />

      {/* Header */}
      <div className="flex items-center justify-between gap-1.5 mb-2 pb-1.5 border-b border-indigo-950/70">
        <div className="flex items-center gap-1.5 min-w-0">
          <div className="p-1.5 rounded-md bg-indigo-500/20 text-indigo-400 ring-1 ring-indigo-500/30 flex-shrink-0">
            <FileCode className="w-3.5 h-3.5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[10px] font-bold tracking-wider uppercase text-indigo-300 truncate">
              {isCoinJoin ? 'CoinJoin Mixer TX' : 'Transaction Hop'}
            </span>
          </div>
        </div>

        <RiskBadge score={riskScore} />
      </div>

      {/* TXID pill */}
      <div className="mb-2">
        <div
          className="text-xs font-mono font-medium text-indigo-200 hover:text-indigo-100 transition-colors cursor-pointer truncate"
          title={rawTxid}
        >
          {displayTxid}
        </div>
      </div>

      {/* Volume & Fee Grid */}
      <div className="grid grid-cols-2 gap-2 text-[11px] bg-slate-900/90 rounded p-1.5 border border-indigo-950/50 font-mono">
        <div>
          <div className="text-[9px] uppercase tracking-wider text-slate-500 font-sans">Volume</div>
          <div className="text-slate-100 font-bold truncate">
            {volumeBtc > 0 ? volumeBtc.toFixed(4) : '0.0000'} <span className="text-[9px] text-indigo-400 font-sans">BTC</span>
          </div>
        </div>

        <div>
          <div className="text-[9px] uppercase tracking-wider text-slate-500 font-sans">Fee</div>
          <div className="text-slate-300 font-medium truncate">
            {fee > 0 ? `${(fee * 1000).toFixed(3)} mB` : '0 mB'}
          </div>
        </div>
      </div>

      {/* CoinJoin / Locktime flag */}
      {isCoinJoin && (
        <div className="mt-2 text-[10px] font-sans font-medium text-amber-300 bg-amber-950/60 border border-amber-800/50 rounded px-1.5 py-0.5 flex items-center gap-1">
          <Layers className="w-3 h-3 flex-shrink-0 text-amber-400" />
          <span className="truncate">Peeling Chain / CoinJoin Pool</span>
        </div>
      )}
    </div>
  );
});
TransactionNode.displayName = 'TransactionNode';

// -------------------------------------------------------------
// 3. NETWORK IP NODE
// -------------------------------------------------------------
export const IpNode: React.FC<NodeProps> = memo(({ data, selected }) => {
  const nodeData = (data?.node as GraphNode) || {
    id: 'ip:unknown',
    type: 'ip',
    label: '0.0.0.0',
    attributes: {},
  };

  const attrs = nodeData.attributes || {};
  const rawIp = (attrs.ip as string) || nodeData.label || nodeData.id.replace(/^ip:/, '');
  const asn = attrs.asn ? `AS${String(attrs.asn).replace(/^AS/i, '')}` : undefined;
  const asnOrg = (attrs.asn_org as string) || (attrs.isp as string) || undefined;
  const country = (attrs.country as string) || (attrs.country_code as string) || (attrs.country_name as string) || 'WW';
  const isTor = Boolean(attrs.tor_exit_node);
  const isVpn = Boolean(attrs.vpn_proxy);
  const riskScore = typeof attrs.risk_score === 'number' ? attrs.risk_score : undefined;

  // Convert 2-letter ISO country code to Emoji flag
  const getFlagEmoji = (countryCode: string) => {
    if (!countryCode || countryCode.length !== 2) return '🌐';
    const code = countryCode.toUpperCase();
    return String.fromCodePoint(...[...code].map((c) => 127397 + c.charCodeAt(0)));
  };

  return (
    <div
      className={`relative min-w-[200px] max-w-[250px] rounded-lg transition-all duration-200 select-none ${
        selected
          ? 'ring-2 ring-emerald-400 shadow-lg shadow-emerald-500/30 scale-[1.02] border-emerald-400 bg-slate-900'
          : 'border-emerald-950/70 hover:border-emerald-700/80 bg-slate-950/95 hover:bg-slate-900/95'
      } border shadow-md backdrop-blur-md p-3 font-sans`}
    >
      {/* Handles: Bottom connects to TX node top */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="relayed"
        className="!w-2.5 !h-2.5 !bg-emerald-400 !border-2 !border-slate-950 !-bottom-1.5 transition-transform hover:scale-125"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="in"
        className="!w-2.5 !h-2.5 !bg-emerald-400 !border-2 !border-slate-950 !-top-1.5 transition-transform hover:scale-125"
      />

      {/* Header */}
      <div className="flex items-center justify-between gap-1.5 mb-2 pb-1.5 border-b border-emerald-950/80">
        <div className="flex items-center gap-1.5 min-w-0">
          <div className="p-1.5 rounded-md bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/30 flex-shrink-0">
            <Globe className="w-3.5 h-3.5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[10px] font-bold tracking-wider uppercase text-emerald-300 truncate">
              {isTor ? 'Tor Relay Relay' : isVpn ? 'VPN / DataCenter' : 'Broadcasting IP'}
            </span>
          </div>
        </div>

        <RiskBadge score={riskScore} />
      </div>

      {/* IP & Country */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs font-mono font-bold text-slate-100 truncate" title={rawIp}>
          {rawIp}
        </span>
        <span className="text-xs flex-shrink-0 flex items-center gap-1 font-mono text-slate-400">
          <span>{getFlagEmoji(country)}</span>
          <span className="text-[10px] font-sans font-semibold text-slate-300">{country.toUpperCase()}</span>
        </span>
      </div>

      {/* ASN / ISP info */}
      <div className="text-[11px] bg-slate-900/90 rounded p-1.5 border border-emerald-950/50 font-mono space-y-1">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-slate-500 font-sans">Autonomous Sys</span>
          <span className="text-emerald-400 font-semibold">{asn || 'AS—'}</span>
        </div>
        {asnOrg && (
          <div className="text-[10px] text-slate-400 truncate" title={asnOrg}>
            {asnOrg}
          </div>
        )}
      </div>

      {/* Tor / Proxy Indicators */}
      {(isTor || isVpn) && (
        <div className="mt-2 text-[10px] font-sans font-medium text-rose-300 bg-rose-950/60 border border-rose-800/50 rounded px-1.5 py-0.5 flex items-center gap-1">
          <Radio className="w-3 h-3 flex-shrink-0 text-rose-400 animate-pulse" />
          <span className="truncate">{isTor ? 'Darknet Onion Exit Node' : 'Known Commercial Proxy'}</span>
        </div>
      )}
    </div>
  );
});
IpNode.displayName = 'IpNode';

// Export custom node types object for ReactFlow
export const customNodeTypes = {
  wallet: WalletNode,
  transaction: TransactionNode,
  ip: IpNode,
};
