import type {
  Case,
  CaseCreate,
  Dataset,
  AnalysisRun,
  RunCreateRequest,
  AlertListResponse,
  InvestigatorRule,
  InvestigatorRuleCreate,
  GraphData,
  GraphQueryParams,
  Report,
} from '../types/index.ts';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export class ApiError extends Error {
  public status: number;
  public data: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Base HTTP fetch wrapper with JSON serialization and robust error handling.
 */
async function fetchClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const headers = new Headers(options.headers || {});

  // Set default Accept header
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  // Set Content-Type to application/json only when sending non-FormData body
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  let data: unknown;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const errorMessage =
      (data && typeof data === 'object' && 'detail' in data && typeof (data as { detail: unknown }).detail === 'string')
        ? (data as { detail: string }).detail
        : response.statusText || `Request failed with status ${response.status}`;
    throw new ApiError(response.status, errorMessage, data);
  }

  return data as T;
}

/**
 * Cases API
 */
export const casesApi = {
  /**
   * List all investigative cases
   */
  async getCases(): Promise<Case[]> {
    return fetchClient<Case[]>('/cases');
  },

  /**
   * Create a new forensic investigation case
   */
  async createCase(payload: CaseCreate): Promise<Case> {
    return fetchClient<Case>('/cases', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Retrieve metadata for a specific case
   */
  async getCase(caseId: string): Promise<Case> {
    return fetchClient<Case>(`/cases/${encodeURIComponent(caseId)}`);
  },
};

/**
 * Datasets API
 */
export const datasetsApi = {
  /**
   * Upload dataset file (CSV, JSON, XML) to a case
   */
  async uploadDataset(
    caseId: string,
    file: File | Blob,
    kind: 'auto' | 'transaction' | 'network' | 'combined' | string = 'auto'
  ): Promise<Dataset> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('kind', kind);

    return fetchClient<Dataset>(`/cases/${encodeURIComponent(caseId)}/datasets`, {
      method: 'POST',
      body: formData,
    });
  },

  /**
   * Load pre-generated synthetic datasets for demonstration
   */
  async loadSyntheticDemo(caseId: string): Promise<{ message: string; datasets: Dataset[] }> {
    return fetchClient<{ message: string; datasets: Dataset[] }>(
      `/cases/${encodeURIComponent(caseId)}/datasets/synthetic-demo`,
      {
        method: 'POST',
      }
    );
  },

  /**
   * List all datasets associated with a case
   */
  async listDatasets(caseId: string): Promise<Dataset[]> {
    return fetchClient<Dataset[]>(`/cases/${encodeURIComponent(caseId)}/datasets`);
  },
};

/**
 * Runs API
 */
export const runsApi = {
  /**
   * Trigger an analysis run across all ingested data in a case
   */
  async startAnalysisRun(caseId: string, config?: RunCreateRequest): Promise<AnalysisRun> {
    return fetchClient<AnalysisRun>(`/cases/${encodeURIComponent(caseId)}/runs`, {
      method: 'POST',
      body: JSON.stringify(config || {}),
    });
  },

  /**
   * Check status and progress of an analysis run
   */
  async getRunStatus(caseId: string, runId: string): Promise<AnalysisRun> {
    return fetchClient<AnalysisRun>(`/cases/${encodeURIComponent(caseId)}/runs/${encodeURIComponent(runId)}`);
  },
};

/**
 * Alerts API
 */
export const alertsApi = {
  /**
   * Retrieve prioritized alerts for a case
   */
  async getAlerts(
    caseId: string,
    stream?: string,
    pageSize: number = 50,
    page: number = 1
  ): Promise<AlertListResponse> {
    const params = new URLSearchParams();
    if (stream) {
      params.append('stream', stream);
    }
    if (pageSize) {
      params.append('page_size', pageSize.toString());
    }
    if (page) {
      params.append('page', page.toString());
    }

    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetchClient<AlertListResponse>(`/cases/${encodeURIComponent(caseId)}/alerts${qs}`);

    // Normalize items so both id and alert_id are populated
    const items = (res.items || []).map((item) => ({
      ...item,
      id: item.id || item.alert_id,
      alert_id: item.alert_id || item.id,
      reasons_json: item.reasons_json ?? (item.reasons ? JSON.stringify(item.reasons) : null),
      explanation_json: item.explanation_json ?? item.ollama_summary ?? null,
    }));

    return {
      ...res,
      items,
    };
  },
};

/**
 * Graph API
 */
export const graphApi = {
  /**
   * Retrieve graph nodes, edges, and statistics for graph visualization
   */
  async getGraph(caseId: string, params?: GraphQueryParams): Promise<GraphData> {
    const query = new URLSearchParams();
    if (params?.run_id) query.append('run_id', params.run_id);
    if (params?.min_priority_score !== undefined) query.append('min_priority_score', params.min_priority_score.toString());
    if (params?.node_type) query.append('node_type', params.node_type);
    if (params?.include_ips !== undefined) query.append('include_ips', params.include_ips.toString());
    if (params?.limit !== undefined) query.append('limit', params.limit.toString());

    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await fetchClient<{
      nodes: GraphData['nodes'];
      edges: GraphData['edges'];
      truncated: boolean;
      total_nodes: number;
      total_edges: number;
    }>(`/cases/${encodeURIComponent(caseId)}/graph${qs}`);

    return {
      nodes: res.nodes || [],
      edges: res.edges || [],
      truncated: res.truncated || false,
      total_nodes: res.total_nodes ?? (res.nodes ? res.nodes.length : 0),
      total_edges: res.total_edges ?? (res.edges ? res.edges.length : 0),
      stats: {
        total_nodes: res.total_nodes ?? (res.nodes ? res.nodes.length : 0),
        total_edges: res.total_edges ?? (res.edges ? res.edges.length : 0),
        truncated: res.truncated || false,
        wallet_count: res.nodes ? res.nodes.filter((n) => n.type === 'wallet').length : 0,
        transaction_count: res.nodes ? res.nodes.filter((n) => n.type === 'transaction').length : 0,
        ip_count: res.nodes ? res.nodes.filter((n) => n.type === 'ip').length : 0,
      },
    };
  },
};

/**
 * Rules API
 */
export const rulesApi = {
  /**
   * List all custom rules defined for a case
   */
  async getRules(caseId: string): Promise<InvestigatorRule[]> {
    const rules = await fetchClient<InvestigatorRule[]>(`/cases/${encodeURIComponent(caseId)}/rules`);
    return rules.map((r) => ({
      ...r,
      rule_id: r.rule_id || r.id,
      id: r.id || r.rule_id,
      target: r.target || r.target_entity,
      target_entity: r.target_entity || r.target,
    }));
  },

  /**
   * Create a new investigator rule
   */
  async createRule(
    caseId: string,
    rule: InvestigatorRuleCreate | Partial<InvestigatorRule>
  ): Promise<InvestigatorRule> {
    const payload = {
      name: rule.name || 'Unnamed Rule',
      description: rule.description || null,
      target_entity: ('target_entity' in rule && rule.target_entity) ? rule.target_entity : (('target' in rule && rule.target) ? rule.target : 'wallet'),
      field: rule.field || 'total_received',
      operator: rule.operator || '>',
      threshold: typeof rule.threshold === 'number' ? rule.threshold : parseFloat(String(rule.threshold || 0)),
      severity: (rule.severity || 'medium').toLowerCase(),
      weight: typeof rule.weight === 'number' ? rule.weight : 1.0,
      enabled: rule.enabled === false || rule.enabled === 0 ? 0 : 1,
    };

    const created = await fetchClient<InvestigatorRule>(`/cases/${encodeURIComponent(caseId)}/rules`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    return {
      ...created,
      rule_id: created.rule_id || created.id,
      id: created.id || created.rule_id,
      target: created.target || created.target_entity,
      target_entity: created.target_entity || created.target,
    };
  },

  /**
   * Delete an investigator rule
   */
  async deleteRule(caseId: string, ruleId: string): Promise<void> {
    await fetchClient<void>(`/cases/${encodeURIComponent(caseId)}/rules/${encodeURIComponent(ruleId)}`, {
      method: 'DELETE',
    });
  },
};

/**
 * Reports API
 */
export const reportsApi = {
  /**
   * Retrieve latest forensic case report in markdown and JSON format
   */
  async getLatestReport(caseId: string): Promise<Report> {
    // Fetch both markdown and json representations concurrently
    const [markdownRes, jsonRes] = await Promise.allSettled([
      fetchClient<{
        report_content?: string;
        run_id?: string;
        case_id: string;
        case_name?: string;
        available_runs?: string[];
      }>(`/cases/${encodeURIComponent(caseId)}/report?format=markdown`),
      fetchClient<Record<string, unknown>>(`/cases/${encodeURIComponent(caseId)}/report?format=json`),
    ]);

    const mdData = markdownRes.status === 'fulfilled' ? markdownRes.value : null;
    const jsonData = jsonRes.status === 'fulfilled' ? jsonRes.value : null;

    const report: Report = {
      case_id: caseId,
      case_name: mdData?.case_name || (jsonData?.case_name as string) || undefined,
      run_id: mdData?.run_id || (jsonData?.run_id as string) || undefined,
      status: (jsonData?.status as string) || undefined,
      markdown: mdData?.report_content || '',
      json: jsonData,
      report_content: mdData?.report_content || '',
      available_runs: mdData?.available_runs || (jsonData?.available_runs as string[]) || [],
      summary: (jsonData?.summary as Report['summary']) || undefined,
      provenance: (jsonData?.provenance as Report['provenance']) || undefined,
    };

    return report;
  },
};
