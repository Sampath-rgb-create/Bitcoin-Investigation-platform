/**
 * Domain models and schemas for Bitcoin Forensic Investigation Platform.
 * Matches backend FastAPI schemas in backend/app/schemas/
 */

export interface Case {
  case_id: string;
  name: string;
  description?: string | null;
  status: 'open' | 'archived' | string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface CaseCreate {
  name: string;
  description?: string | null;
}

export interface CaseUpdate {
  name?: string | null;
  description?: string | null;
  status?: 'open' | 'archived' | string | null;
}

export interface Dataset {
  dataset_id: string;
  case_id: string;
  name: string;
  kind: 'auto' | 'transaction' | 'network' | 'combined' | 'unknown' | string;
  format: 'csv' | 'json' | 'xml' | string;
  sha256: string;
  row_count: number;
  accepted_rows: number;
  rejected_rows: number;
  warning_count: number;
  status: 'validated' | 'processing' | 'error' | string;
  created_at: string;
}

export interface ValidationReportRow {
  row_number: number;
  record_id?: string | null;
  issue_type: 'error' | 'warning';
  code: string;
  message: string;
}

export interface ValidationReport {
  dataset_id: string;
  total_rows: number;
  accepted_rows: number;
  rejected_rows: number;
  warning_count: number;
  issues: ValidationReportRow[];
}

export interface DetectorConfig {
  isolation_forest?: boolean;
  behavior_rules?: boolean;
  graph_signals?: boolean;
  network_signals?: boolean;
}

export interface IsolationForestConfig {
  n_estimators?: number;
  contamination?: string | number;
  random_state?: number;
}

export interface CorrelationConfig {
  allow_temporal?: boolean;
  window_seconds?: number;
}

export interface AIConfig {
  enable_laya?: boolean;
  enable_ollama?: boolean;
}

export interface RunCreateRequest {
  detectors?: DetectorConfig;
  isolation_forest?: IsolationForestConfig;
  correlation?: CorrelationConfig;
  ai?: AIConfig;
}

export interface AnalysisRun {
  run_id: string;
  case_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'interrupted' | string;
  stage: string;
  progress: number;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  error_code?: string | null;
  error_message?: string | null;
}

export interface ScoreComponents {
  supervised_score?: number;
  unsupervised_score?: number;
  graph_score?: number;
  rule_score?: number;
  anomaly_score?: number;
  behavior_score?: number;
  network_score?: number;
}

export interface Alert {
  id?: string;
  alert_id?: string;
  run_id: string;
  entity_id: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  priority_score: number;
  supervised_score?: number;
  unsupervised_score?: number;
  graph_score?: number;
  rule_score?: number;
  network_score?: number;
  anomaly_score?: number;
  behavior_score?: number;
  correlation_strength?: number;
  score_components?: ScoreComponents;
  evidence_coverage?: number;
  top_reasons?: string[];
  reasons?: string[];
  reasons_json?: string | null;
  explanation_json?: string | null;
  laya?: Record<string, unknown> | null;
  ollama_summary?: string | null;
  created_at: string;
}

export interface AlertListResponse {
  items: Alert[];
  total: number;
  page: number;
  page_size: number;
}

export interface AlertQueryParams {
  run_id?: string;
  severity?: string;
  min_priority_score?: number;
  entity_type?: string;
  page?: number;
  page_size?: number;
  stream?: string;
}

export interface InvestigatorRule {
  id?: string;
  rule_id?: string;
  case_id?: string | null;
  name: string;
  description?: string | null;
  target?: 'wallet' | 'transaction' | string;
  target_entity?: 'wallet' | 'transaction' | string;
  field: string;
  operator: '>' | '>=' | '<' | '<=' | '==' | '!=' | 'contains' | string;
  threshold: number;
  severity: 'low' | 'medium' | 'high' | 'critical' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  weight: number;
  enabled: number | boolean;
  created_by?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface InvestigatorRuleCreate {
  name: string;
  description?: string | null;
  target_entity: 'wallet' | 'transaction' | string;
  field: string;
  operator: '>' | '>=' | '<' | '<=' | '==' | '!=' | 'contains' | string;
  threshold: number;
  severity?: 'low' | 'medium' | 'high' | 'critical' | string;
  weight?: number;
  enabled?: number;
}

export interface GraphNode {
  id: string;
  type: 'wallet' | 'transaction' | 'ip' | 'asn' | 'country' | string;
  label: string;
  attributes?: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: 'INPUT_TO' | 'OUTPUT_TO' | 'OBSERVED' | 'BELONGS_TO_ASN' | 'GEOLOCATED_TO' | 'NEXT_TX' | string;
  basis: string;
  source_record_ids?: string[];
  weight?: number;
  first_seen?: string | null;
  last_seen?: string | null;
}

export interface GraphStats {
  total_nodes: number;
  total_edges: number;
  truncated: boolean;
  wallet_count?: number;
  transaction_count?: number;
  ip_count?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  truncated: boolean;
  total_nodes: number;
  total_edges: number;
  stats?: GraphStats;
}

export interface GraphQueryParams {
  run_id?: string;
  min_priority_score?: number;
  node_type?: string;
  include_ips?: boolean;
  limit?: number;
}

export interface ReportSummary {
  alert_count?: number;
  [key: string]: unknown;
}

export interface ReportProvenance {
  generated_at?: string;
  offline_mode?: boolean;
  version?: string;
  [key: string]: unknown;
}

export interface Report {
  report_id?: string;
  case_id: string;
  case_name?: string;
  run_id?: string;
  status?: string;
  markdown?: string;
  json?: Record<string, unknown> | null;
  report_content?: string;
  available_runs?: string[];
  provenance?: ReportProvenance;
  summary?: ReportSummary;
}
