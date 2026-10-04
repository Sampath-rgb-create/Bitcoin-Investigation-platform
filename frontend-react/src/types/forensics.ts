export type ScoreStream = 'composite' | 'supervised' | 'unsupervised' | 'graph_flow' | 'custom_rules';

export type AlertSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface ScoreBreakdown {
  compositeScore: number;
  supervisedMlScore: number;
  unsupervisedIfScore: number;
  graphFlowScore: number;
  customRulesScore: number;
}

export interface DeviationReason {
  feature: string;
  expectedValue: string | number;
  observedValue: string | number;
  contribution: number; // percentage or impact score e.g. +34%
  description: string;
}

export interface ForensicAlert {
  id: string;
  txHash: string;
  targetAddress: string;
  timestamp: string;
  amountBtc: number;
  amountUsd: number;
  severity: AlertSeverity;
  scores: ScoreBreakdown;
  narrative: string;
  tags: string[];
  deviationReasons: DeviationReason[];
  rawSource: {
    inputsCount: number;
    outputsCount: number;
    feeSats: number;
    lockTime: number;
    version: number;
    ringCount?: number;
    peelingChainLength?: number;
    firstSeenBlock: number;
  };
}

export interface CaseSummary {
  id: string;
  name: string;
  targetAddress: string;
  createdDate: string;
  status: 'ACTIVE' | 'ARCHIVED' | 'ANALYZING';
  datasetCount: number;
  alertCount: number;
  criticalAlertCount: number;
}

export interface AttachedDataset {
  name: string;
  type: 'transactions' | 'inputs' | 'outputs' | 'network';
  filename: string;
  rowsCount: number;
  fileSizeBytes: number;
  uploadedAt: string;
  status: 'READY' | 'INGESTING' | 'ERROR';
}

export interface CustomRule {
  id: string;
  name: string;
  target: 'TRANSACTION' | 'ADDRESS' | 'EDGE';
  field: string;
  operator: '>' | '<' | '==' | '!=' | 'CONTAINS' | 'MATCHES_REGEX';
  threshold: string | number;
  severity: AlertSeverity;
  weight: number; // 0.0 - 1.0 weight on composite
  isActive: boolean;
}

export interface PipelineStage {
  id: string;
  name: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  progressPercent: number;
  detail?: string;
}

export * from './graph';

