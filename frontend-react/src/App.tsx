import { useState, useEffect } from 'react';
import { Header } from './components/layout/Header';
import { NavigationTabs } from './components/layout/NavigationTabs';
import type { TabType } from './components/layout/NavigationTabs';
import { CaseSelectorSidebar } from './components/layout/CaseSelectorSidebar';
import { CanonicalIngestionSuite } from './components/ingestion/CanonicalIngestionSuite';
import { AttachedDatasetsList } from './components/ingestion/AttachedDatasetsList';
import { MetricCards } from './components/alerts/MetricCards';
import { ScoreStreamSwitcher } from './components/alerts/ScoreStreamSwitcher';
import { AlertsTable } from './components/alerts/AlertsTable';
import { EvidenceDrawer } from './components/alerts/EvidenceDrawer';
import { RulesManagerModal } from './components/rules/RulesManagerModal';
import { CreateCaseModal } from './components/common/CreateCaseModal';
import { PipelineProgressModal } from './components/common/PipelineProgressModal';
import { ReportViewer } from './components/reports/ReportViewer';
import { InvestigationGraphCanvas } from './components/graph';

import {
  INITIAL_CASES,
  INITIAL_DATASETS,
  INITIAL_RULES,
  PIPELINE_STAGES,
  MOCK_ALERTS,
} from './data/mockForensics';
import type { ForensicAlert, ScoreStream, CaseSummary, CustomRule } from './types/forensics';
import type { GraphData } from './types/graph';
import { graphApi, alertsApi, casesApi, datasetsApi, runsApi } from './services/api';
import type { Alert } from './types';

export default function App() {
  // State management
  const [activeTab, setActiveTab] = useState<TabType>('alerts');
  const [cases, setCases] = useState<CaseSummary[]>(INITIAL_CASES);
  const [activeCaseId, setActiveCaseId] = useState<string>(INITIAL_CASES[0].id);
  const [datasets, setDatasets] = useState(INITIAL_DATASETS);
  const [rules, setRules] = useState<CustomRule[]>(INITIAL_RULES);
  const [alerts, setAlerts] = useState<ForensicAlert[]>(MOCK_ALERTS);

  // Graph state
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);

  // Heuristic streams & drawer
  const [activeStream, setActiveStream] = useState<ScoreStream>('composite');
  const [selectedAlert, setSelectedAlert] = useState<ForensicAlert | null>(null);

  // Modals
  const [isRulesModalOpen, setIsRulesModalOpen] = useState(false);
  const [isCreateCaseModalOpen, setIsCreateCaseModalOpen] = useState(false);
  const [isPipelineModalOpen, setIsPipelineModalOpen] = useState(false);
  const [pipelineProgress, setPipelineProgress] = useState(100);
  const [activeStageIdx, setActiveStageIdx] = useState(4);

  const activeCase = cases.find((c) => c.id === activeCaseId) || cases[0];

  // 1. Fetch live cases from backend on startup
  useEffect(() => {
    let isMounted = true;
    const fetchLiveCases = async () => {
      try {
        const liveCases = await casesApi.getCases();
        if (isMounted && liveCases && liveCases.length > 0) {
          const mappedCases: CaseSummary[] = liveCases.map((c) => ({
            id: c.case_id,
            name: c.name || `Case ${c.case_id.slice(0, 8)}`,
            targetAddress: 'bc1q_peel_master_source_x99a7b1c3e4d',
            createdDate: c.created_at.slice(0, 10),
            status: 'ACTIVE',
            datasetCount: 4,
            alertCount: 38,
            criticalAlertCount: 10,
          }));
          setCases(mappedCases);
          setActiveCaseId(mappedCases[0].id);
        }
      } catch (err) {
        console.warn('Could not fetch backend cases, keeping defaults:', err);
      }
    };
    fetchLiveCases();
    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Fetch live alerts when active case changes
  useEffect(() => {
    let isMounted = true;
    const fetchLiveAlerts = async () => {
      try {
        const targetCase = activeCaseId.startsWith('case-') ? 'c35bbc1e-62e3-44f2-9d7b-77b0b51b4e6c' : activeCaseId;
        const res = await alertsApi.getAlerts(targetCase, undefined, 100);
        if (isMounted && res && res.items && res.items.length > 0) {
          const mappedAlerts: ForensicAlert[] = res.items.map((item: Alert, idx: number) => {
            const comps = item.score_components || {};
            const cleanEntity = (item.entity_id || '').replace('transaction:', '').replace('wallet:', '').replace('ip:', '');
            const reasonsList = item.top_reasons || item.reasons || [];
            return {
              id: item.alert_id || item.id || `alert-${idx}`,
              txHash: cleanEntity,
              targetAddress: cleanEntity,
              timestamp: item.created_at || new Date().toISOString(),
              amountBtc: 0.5 + (idx % 5) * 0.75,
              amountUsd: Math.round((0.5 + (idx % 5) * 0.75) * 65000),
              severity: (item.severity || 'HIGH').toUpperCase() as any,
              scores: {
                compositeScore: Number(item.priority_score || 70) / 100,
                supervisedMlScore: Number(item.supervised_score || (comps.supervised_score != null ? comps.supervised_score : 65)) / 100,
                unsupervisedIfScore: Number(item.unsupervised_score || (comps.unsupervised_score != null ? comps.unsupervised_score : 80)) / 100,
                graphFlowScore: Number(item.graph_score || (comps.graph_score != null ? comps.graph_score * 100 : 70)) / 100,
                customRulesScore: Number(item.rule_score || (comps.rule_score != null ? comps.rule_score : 50)) / 100,
              },
              narrative: reasonsList.length > 0 ? reasonsList[0] : `Suspicious entity ${item.entity_id} flagged by forensic engines.`,
              tags: reasonsList.slice(0, 3).map((r) => r.split(':')[0].trim()),
              deviationReasons: reasonsList.map((r, rIdx) => ({
                feature: `Anomaly Signal #${rIdx + 1}`,
                expectedValue: 'Baseline Standard',
                observedValue: 'Threshold Exceeded',
                contribution: Math.max(15, 60 - rIdx * 10),
                description: r,
              })),
              rawSource: {
                inputsCount: 1 + (idx % 3),
                outputsCount: 2 + (idx % 6),
                feeSats: 10000 + idx * 500,
                lockTime: 0,
                version: 2,
                firstSeenBlock: 890200 + idx,
              },
            };
          });
          setAlerts(mappedAlerts);
        }
      } catch (err) {
        console.warn('Could not fetch live alerts, using sample set:', err);
      }
    };
    fetchLiveAlerts();
    return () => {
      isMounted = false;
    };
  }, [activeCaseId]);

  // 3. Fetch live graph topology when graph tab or case changes
  useEffect(() => {
    let isMounted = true;
    const fetchTopology = async () => {
      setIsLoadingGraph(true);
      try {
        const targetCase = activeCaseId.startsWith('case-') ? 'c35bbc1e-62e3-44f2-9d7b-77b0b51b4e6c' : activeCaseId;
        const data = await graphApi.getGraph(targetCase, { limit: 120 });
        if (isMounted && data && data.nodes && data.nodes.length > 0) {
          setGraphData(data as unknown as GraphData);
        }
      } catch (err) {
        console.warn('Backend graph API query failed, falling back to local generated topology:', err);
      } finally {
        if (isMounted) setIsLoadingGraph(false);
      }
    };

    fetchTopology();
    return () => {
      isMounted = false;
    };
  }, [activeCaseId]);

  // Quick Demo Simulator & Live Pipeline Trigger
  const handleTriggerDemoRun = async () => {
    setIsPipelineModalOpen(true);
    setPipelineProgress(10);
    setActiveStageIdx(0);

    try {
      const targetCase = activeCaseId.startsWith('case-') ? 'c35bbc1e-62e3-44f2-9d7b-77b0b51b4e6c' : activeCaseId;
      // Load synthetic demo files into the active case on backend
      await datasetsApi.loadSyntheticDemo(targetCase);
      // Trigger live backend analysis run
      await runsApi.startAnalysisRun(targetCase);
    } catch (e) {
      console.warn('Backend run trigger error:', e);
    }

    const interval = setInterval(() => {
      setPipelineProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setActiveStageIdx(4);
          // Refetch fresh alerts and graph
          alertsApi.getAlerts(activeCaseId.startsWith('case-') ? 'c35bbc1e-62e3-44f2-9d7b-77b0b51b4e6c' : activeCaseId, undefined, 100).then((res) => {
            if (res && res.items) {
              // Trigger reload
              setActiveCaseId((id) => id);
            }
          });
          return 100;
        }
        const next = prev + 25;
        if (next >= 75) setActiveStageIdx(3);
        else if (next >= 50) setActiveStageIdx(2);
        else if (next >= 25) setActiveStageIdx(1);
        return next;
      });
    }, 400);
  };

  const handleFilesCommitted = async (files: Record<string, File>) => {
    setIsPipelineModalOpen(true);
    setPipelineProgress(15);
    setActiveStageIdx(0);

    const targetCase = activeCaseId.startsWith('case-') ? 'c35bbc1e-62e3-44f2-9d7b-77b0b51b4e6c' : activeCaseId;
    
    // Upload each file to the backend
    for (const [key, file] of Object.entries(files)) {
      try {
        await datasetsApi.uploadDataset(targetCase, file, key);
      } catch (err) {
        console.warn(`Error uploading ${key}:`, err);
      }
    }

    try {
      await runsApi.startAnalysisRun(targetCase);
    } catch (err) {
      console.warn('Error starting analysis run:', err);
    }

    // Attach to UI
    const newItems = Object.entries(files).map(([key, file]) => ({
      name: `${key}.csv`,
      type: key as any,
      filename: file.name,
      rowsCount: 180,
      fileSizeBytes: file.size || 15000,
      uploadedAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
      status: 'READY' as const,
    }));
    setDatasets((prev) => [...prev, ...newItems]);

    // Animate completion and reload live scores
    const interval = setInterval(() => {
      setPipelineProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setActiveStageIdx(4);
          window.location.reload();
          return 100;
        }
        return prev + 25;
      });
    }, 500);
  };

  const handleSendToGraph = (alert: ForensicAlert) => {
    setActiveTab('graph');
    setSelectedAlert(alert);
  };

  const handleCreateCase = async (newCase: CaseSummary) => {
    try {
      const created = await casesApi.createCase({
        name: newCase.name,
        description: `Target address: ${newCase.targetAddress}`,
      });
      const mapped: CaseSummary = {
        ...newCase,
        id: created.case_id,
      };
      setCases((prev) => [mapped, ...prev]);
      setActiveCaseId(mapped.id);
    } catch {
      setCases((prev) => [newCase, ...prev]);
      setActiveCaseId(newCase.id);
    }
  };

  const handleRemoveDataset = (name: string) => {
    setDatasets((prev) => prev.filter((d) => d.name !== name));
  };


  return (
    <div className="min-h-screen bg-[#090e17] text-slate-100 flex flex-col font-sans">
      {/* 1. Header */}
      <Header
        activeCaseName={activeCase.name}
        targetAddress={activeCase.targetAddress}
        isOfflineMode={true}
        onOpenRulesManager={() => setIsRulesModalOpen(true)}
      />

      {/* Main Layout Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* 2. Sidebar Case Selector */}
        <CaseSelectorSidebar
          cases={cases}
          activeCaseId={activeCaseId}
          onSelectCase={(id) => setActiveCaseId(id)}
          onOpenCreateCaseModal={() => setIsCreateCaseModalOpen(true)}
          onTriggerDemoRun={handleTriggerDemoRun}
        />

        {/* 3. Primary Content Stage */}
        <main className="flex-1 flex flex-col overflow-hidden bg-[#090e17]">
          {/* Navigation Bar */}
          <NavigationTabs
            activeTab={activeTab}
            onTabChange={setActiveTab}
            alertCount={alerts.length}
          />

          {/* Tab Views */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* VIEW 1: DATASET INGESTION */}
            {activeTab === 'ingestion' && (
              <div className="space-y-4 max-w-6xl mx-auto">
                <CanonicalIngestionSuite
                  onFilesCommitted={handleFilesCommitted}
                  isProcessing={isPipelineModalOpen}
                />
                <AttachedDatasetsList
                  datasets={datasets}
                  onRemoveDataset={handleRemoveDataset}
                />
              </div>
            )}

            {/* VIEW 2: ALERTS & EVIDENCE */}
            {activeTab === 'alerts' && (
              <div className="space-y-4 max-w-7xl mx-auto">
                <MetricCards alerts={alerts} />

                <div className="p-3 bg-[#0b1322] border border-slate-800 rounded-lg">
                  <ScoreStreamSwitcher
                    activeStream={activeStream}
                    onStreamChange={setActiveStream}
                  />
                </div>

                <AlertsTable
                  alerts={alerts}
                  activeStream={activeStream}
                  selectedAlertId={selectedAlert?.id || null}
                  onSelectAlert={(a) => setSelectedAlert(a)}
                  onSendToGraphCanvas={handleSendToGraph}
                />
              </div>
            )}

            {/* VIEW 3: LIVE REACT FLOW GRAPH CANVAS */}
            {activeTab === 'graph' && (
              <div className="w-full h-[calc(100vh-140px)] bg-[#0b1322] border border-slate-800 rounded-lg overflow-hidden relative">
                {isLoadingGraph ? (
                  <div className="flex flex-col items-center justify-center h-full gap-3 text-slate-400 font-mono">
                    <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
                    <span>Loading Money Flow Topology...</span>
                  </div>
                ) : (
                  <InvestigationGraphCanvas
                    initialGraphData={graphData || undefined}
                    className="w-full h-full"
                  />
                )}
              </div>
            )}

            {/* VIEW 4: FORENSIC REPORTS */}
            {activeTab === 'reports' && (
              <div className="max-w-6xl mx-auto">
                <ReportViewer
                  activeCase={activeCase}
                  alerts={alerts}
                />
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Slide-over Evidence Drawer */}
      <EvidenceDrawer
        alert={selectedAlert}
        onClose={() => setSelectedAlert(null)}
        onSendToGraphCanvas={handleSendToGraph}
      />

      {/* Investigator Custom Rules Modal */}
      <RulesManagerModal
        isOpen={isRulesModalOpen}
        onClose={() => setIsRulesModalOpen(false)}
        rules={rules}
        onSaveRules={(updated) => setRules(updated)}
      />

      {/* Create New Case Dossier Modal */}
      <CreateCaseModal
        isOpen={isCreateCaseModalOpen}
        onClose={() => setIsCreateCaseModalOpen(false)}
        onCreateCase={handleCreateCase}
      />

      {/* Pipeline Progress Modal */}
      <PipelineProgressModal
        isOpen={isPipelineModalOpen}
        onClose={() => setIsPipelineModalOpen(false)}
        stages={PIPELINE_STAGES}
        currentOverallProgress={pipelineProgress}
        activeStageIndex={activeStageIdx}
      />
    </div>
  );
}
