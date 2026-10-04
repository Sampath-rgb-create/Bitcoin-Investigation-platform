export type GraphNodeType = 'wallet' | 'transaction' | 'ip' | 'asn' | 'country';

export interface WalletNodeAttributes {
  address?: string;
  balance?: number;
  balance_change?: number;
  total_received?: number;
  total_sent?: number;
  risk_score?: number;
  tags?: string[];
  entity?: string;
  is_mixer?: boolean;
  is_exchange?: boolean;
  is_sanctioned?: boolean;
  cluster_id?: string;
  pagerank?: number;
  in_degree?: number;
  out_degree?: number;
  [key: string]: unknown;
}

export interface TransactionNodeAttributes {
  txid?: string;
  timestamp?: string;
  fee?: number;
  fee_sats?: number;
  total_input?: number;
  total_output?: number;
  amount_btc?: number;
  script_type?: string;
  locktime?: number;
  version?: number;
  risk_score?: number;
  anomaly_flag?: boolean;
  is_coinjoin?: boolean;
  source_record_id?: string;
  pagerank?: number;
  in_degree?: number;
  out_degree?: number;
  [key: string]: unknown;
}

export interface IpNodeAttributes {
  ip?: string;
  asn?: string | number;
  asn_org?: string;
  country?: string;
  country_name?: string;
  country_code?: string;
  city?: string;
  tor_exit_node?: boolean;
  vpn_proxy?: boolean;
  isp?: string;
  threat_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  observation_count?: number;
  last_seen?: string;
  pagerank?: number;
  in_degree?: number;
  out_degree?: number;
  [key: string]: unknown;
}

export type AnyNodeAttributes = WalletNodeAttributes & TransactionNodeAttributes & IpNodeAttributes;

export interface GraphNode {
  id: string;
  type: GraphNodeType | string;
  label: string;
  attributes: AnyNodeAttributes;
}

export type EdgeType =
  | 'INPUT_TO'
  | 'SPENT_FROM'
  | 'OUTPUT_TO'
  | 'SENT_TO'
  | 'RELAYED_BY'
  | 'OBSERVED'
  | 'HOSTED_IN'
  | 'BELONGS_TO_ASN'
  | 'LOCATED_IN'
  | 'GEOLOCATED_TO'
  | 'NEXT_TX'
  | string;

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  basis?: string;
  source_record_ids?: string[];
  weight?: number;
  amount?: number;
  first_seen?: string;
  last_seen?: string;
  [key: string]: unknown;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  truncated?: boolean;
  total_nodes?: number;
  total_edges?: number;
}

export interface NodeNeighborhoodDetail {
  node: GraphNode;
  inDegree: number;
  outDegree: number;
  pageRank: number;
  incomingEdges: GraphEdge[];
  outgoingEdges: GraphEdge[];
  counterparties: {
    nodeId: string;
    label: string;
    type: string;
    relationship: string;
    amount?: number;
  }[];
}
