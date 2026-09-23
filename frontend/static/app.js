// Frontend client logic for Bitcoin Investigation Platform
let currentCaseId = null;
let currentRunId = null;
let alertsData = [];
let graphData = { nodes: [], edges: [] };
let selectedAlertId = null;

// Staged files for upload
let stagedFiles = {
  tx: null,
  net: null,
  comb: null,
};

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initGraphCanvas();
  initDropzones();
  loadCases();
  setupEventListeners();
});

function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".view-section").forEach((s) => s.classList.remove("active"));
      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetSection = document.getElementById(targetId);
      if (targetSection) targetSection.classList.add("active");

      if (targetId === "graph-view") {
        resizeCanvas();
        if (currentCaseId) loadCaseGraph(currentCaseId);
      } else if (targetId === "report-view") {
        if (currentCaseId) loadCaseReport(currentCaseId);
      } else if (targetId === "alerts-view") {
        if (currentCaseId) loadCaseAlerts(currentCaseId);
      }
    });
  });
}

function setupEventListeners() {
  // Case Selector on Alerts Tab
  const caseSelect = document.getElementById("case-select");
  if (caseSelect) {
    caseSelect.addEventListener("change", (e) => {
      const caseId = e.target.value;
      if (caseId) selectCase(caseId);
    });
  }

  // Case Selector on Upload Tab
  const uploadCaseSelect = document.getElementById("upload-case-select");
  if (uploadCaseSelect) {
    uploadCaseSelect.addEventListener("change", (e) => {
      const caseId = e.target.value;
      if (caseId) selectCase(caseId);
    });
  }

  // Filter buttons for Alerts
  document.querySelectorAll(".pill-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".pill-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const severity = btn.getAttribute("data-severity");
      filterAlerts(severity);
    });
  });

  // Execute Analysis Pipeline buttons (Sidebar and Upload view)
  const runBtn = document.getElementById("btn-trigger-run");
  if (runBtn) {
    runBtn.addEventListener("click", () => {
      if (currentCaseId) triggerAnalysisRun(currentCaseId);
    });
  }

  const uploadExecuteBtn = document.getElementById("btn-upload-execute-all");
  if (uploadExecuteBtn) {
    uploadExecuteBtn.addEventListener("click", async () => {
      if (!currentCaseId) {
        alert("Please select a case first.");
        return;
      }
      if (hasStagedFiles()) {
        await uploadStagedFiles(currentCaseId);
      }
      triggerAnalysisRun(currentCaseId);
    });
  }

  const uploadAndRunBtn = document.getElementById("btn-upload-and-run");
  if (uploadAndRunBtn) {
    uploadAndRunBtn.addEventListener("click", async () => {
      if (!currentCaseId) {
        alert("Please select a case first.");
        return;
      }
      if (hasStagedFiles()) {
        await uploadStagedFiles(currentCaseId);
      }
      triggerAnalysisRun(currentCaseId);
    });
  }

  const uploadOnlyBtn = document.getElementById("btn-upload-only");
  if (uploadOnlyBtn) {
    uploadOnlyBtn.addEventListener("click", async () => {
      if (!currentCaseId) {
        alert("Please select a case first.");
        return;
      }
      if (!hasStagedFiles()) {
        alert("No files selected to upload.");
        return;
      }
      await uploadStagedFiles(currentCaseId);
      loadCaseDatasets(currentCaseId);
    });
  }

  // Pre-packaged synthetic demo loader
  const loadSyntheticBtn = document.getElementById("btn-load-synthetic");
  if (loadSyntheticBtn) {
    loadSyntheticBtn.addEventListener("click", () => {
      if (currentCaseId) loadSyntheticDatasets(currentCaseId);
    });
  }

  // Create New Case Modal handlers
  const openCaseBtn = document.getElementById("btn-open-create-case");
  if (openCaseBtn) {
    openCaseBtn.addEventListener("click", openCreateCaseModal);
  }

  const submitCaseBtn = document.getElementById("btn-submit-create-case");
  if (submitCaseBtn) {
    submitCaseBtn.addEventListener("click", submitCreateCase);
  }

  // Graph control buttons
  const zoomInBtn = document.getElementById("btn-zoom-in");
  if (zoomInBtn) {
    zoomInBtn.addEventListener("click", zoomIn);
  }

  const zoomOutBtn = document.getElementById("btn-zoom-out");
  if (zoomOutBtn) {
    zoomOutBtn.addEventListener("click", zoomOut);
  }

  const resetZoomBtn = document.getElementById("btn-reset-zoom");
  if (resetZoomBtn) {
    resetZoomBtn.addEventListener("click", resetGraphView);
  }

  // Graph layout & limit dropdowns
  const layoutSelect = document.getElementById("graph-layout-mode");
  if (layoutSelect) {
    layoutSelect.addEventListener("change", (e) => {
      setGraphLayoutMode(e.target.value);
    });
  }

  const limitSelect = document.getElementById("graph-limit-select");
  if (limitSelect) {
    limitSelect.addEventListener("change", (e) => {
      setGraphLimit(e.target.value);
    });
  }

  // Graph Search
  const searchInput = document.getElementById("graph-search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchGraphNodes(e.target.value);
    });
  }

  const searchClearBtn = document.getElementById("btn-graph-search-clear");
  if (searchClearBtn) {
    searchClearBtn.addEventListener("click", () => {
      if (searchInput) searchInput.value = "";
      searchGraphNodes("");
    });
  }

  // Inspector Action Buttons
  const focusBtn = document.getElementById("btn-inspector-focus");
  if (focusBtn) {
    focusBtn.addEventListener("click", focusSelectedNode);
  }

  const egoBtn = document.getElementById("btn-inspector-ego");
  if (egoBtn) {
    egoBtn.addEventListener("click", isolateSelectedEgo);
  }

  const copyIdBtn = document.getElementById("btn-inspector-copy");
  if (copyIdBtn) {
    copyIdBtn.addEventListener("click", copyInspectorId);
  }

  // Report View Action Buttons
  const runSelect = document.getElementById("report-run-select");
  if (runSelect) {
    runSelect.addEventListener("change", (e) => {
      if (currentCaseId) loadCaseReport(currentCaseId, e.target.value);
    });
  }

  const dlMdBtn = document.getElementById("btn-download-report-md");
  if (dlMdBtn) {
    dlMdBtn.addEventListener("click", downloadReportMarkdown);
  }

  const dlJsonBtn = document.getElementById("btn-download-report-json");
  if (dlJsonBtn) {
    dlJsonBtn.addEventListener("click", downloadReportJson);
  }

  const copyReportBtn = document.getElementById("btn-copy-report");
  if (copyReportBtn) {
    copyReportBtn.addEventListener("click", copyReportText);
  }

  const refreshReportBtn = document.getElementById("btn-refresh-report");
  if (refreshReportBtn) {
    refreshReportBtn.addEventListener("click", () => {
      if (currentCaseId) loadCaseReport(currentCaseId);
    });
  }
}

// -------------------------------------------------------------
// Dropzones & Ingestion Handling
// -------------------------------------------------------------
function initDropzones() {
  setupSingleDropzone("dropzone-tx", "input-file-tx", "tx-file-status", "tx");
  setupSingleDropzone("dropzone-net", "input-file-net", "net-file-status", "net");
  setupSingleDropzone("dropzone-comb", "input-file-comb", "comb-file-status", "comb");
}

function setupSingleDropzone(dropzoneId, inputId, statusId, kindKey) {
  const dropzone = document.getElementById(dropzoneId);
  const fileInput = document.getElementById(inputId);
  const statusEl = document.getElementById(statusId);

  if (!dropzone || !fileInput) return;

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0], kindKey, statusEl);
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0], kindKey, statusEl);
    }
  });
}

function handleFileSelected(file, kindKey, statusEl) {
  stagedFiles[kindKey] = file;
  if (statusEl) {
    statusEl.textContent = `✓ Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  }
  updateUploadBarStatus();
}

function hasStagedFiles() {
  return stagedFiles.tx !== null || stagedFiles.net !== null || stagedFiles.comb !== null;
}

function updateUploadBarStatus() {
  const barText = document.getElementById("upload-status-text");
  if (!barText) return;
  const count = Object.values(stagedFiles).filter((f) => f !== null).length;
  barText.textContent = count > 0 ? `${count} file(s) staged for ingestion` : "No files queued";
}

async function uploadStagedFiles(caseId) {
  const statusEl = document.getElementById("upload-status-text");
  if (statusEl) statusEl.textContent = "Uploading datasets to case...";

  const uploads = [];
  if (stagedFiles.tx) {
    uploads.push(uploadSingleFile(caseId, stagedFiles.tx, "transaction"));
  }
  if (stagedFiles.net) {
    uploads.push(uploadSingleFile(caseId, stagedFiles.net, "network"));
  }
  if (stagedFiles.comb) {
    uploads.push(uploadSingleFile(caseId, stagedFiles.comb, "combined"));
  }

  try {
    await Promise.all(uploads);
    if (statusEl) statusEl.textContent = "✓ Ingestion complete. Files attached.";
    // Clear staged files
    stagedFiles = { tx: null, net: null, comb: null };
    document.querySelectorAll(".dropzone-file-status").forEach((el) => (el.textContent = ""));
    loadCaseDatasets(caseId);
  } catch (err) {
    alert("Upload error: " + err.message);
    if (statusEl) statusEl.textContent = "Upload failed";
  }
}

async function uploadSingleFile(caseId, file, kind) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("kind", kind);

  const res = await fetch(`/api/v1/cases/${caseId}/datasets`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed for ${file.name}`);
  }
  return await res.json();
}

async function loadSyntheticDatasets(caseId) {
  const btn = document.getElementById("btn-load-synthetic");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Linking Synthetic Data...";
  }

  try {
    await apiFetch(`/cases/${caseId}/load-synthetic`, { method: "POST" });
    alert("Successfully attached synthetic Bitcoin transactions and network telemetry records!");
    loadCaseDatasets(caseId);
  } catch (err) {
    alert("Could not load synthetic data: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Load Pre-packaged Synthetic Datasets";
    }
  }
}

// -------------------------------------------------------------
// Case Creation Modal Functions
// -------------------------------------------------------------
function openCreateCaseModal() {
  const modal = document.getElementById("create-case-modal");
  if (modal) {
    modal.classList.add("active");
    const titleInput = document.getElementById("new-case-title");
    if (titleInput) {
      titleInput.value = "";
      titleInput.focus();
    }
    const descInput = document.getElementById("new-case-desc");
    if (descInput) descInput.value = "";
  }
}

function closeCreateCaseModal() {
  const modal = document.getElementById("create-case-modal");
  if (modal) modal.classList.remove("active");
}

async function submitCreateCase() {
  const titleInput = document.getElementById("new-case-title");
  const descInput = document.getElementById("new-case-desc");
  const name = titleInput ? titleInput.value.trim() : "";
  const description = descInput ? descInput.value.trim() : "";

  if (!name) {
    alert("Please enter a case title / name.");
    return;
  }

  const submitBtn = document.getElementById("btn-submit-create-case");
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = "Creating...";
  }

  try {
    const newCase = await apiFetch("/cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description }),
    });

    closeCreateCaseModal();
    // Reload cases and automatically select the newly created case
    await loadCases();
    selectCase(newCase.case_id);
    alert(`Case "${newCase.name}" created successfully!`);
  } catch (err) {
    alert("Could not create case: " + err.message);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Create & Open Case";
    }
  }
}

// -------------------------------------------------------------
// API Helpers & Case Management
// -------------------------------------------------------------
async function apiFetch(endpoint, options = {}) {
  try {
    const res = await fetch(`/api/v1${endpoint}`, options);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.message || `HTTP error ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    console.error("API error:", error);
    throw error;
  }
}

async function loadCases() {
  try {
    const cases = await apiFetch("/cases");
    const caseSelect = document.getElementById("case-select");
    const uploadCaseSelect = document.getElementById("upload-case-select");

    [caseSelect, uploadCaseSelect].forEach((select) => {
      if (!select) return;
      select.innerHTML = "";
      if (!cases || cases.length === 0) {
        select.innerHTML = `<option value="">No cases found</option>`;
      } else {
        cases.forEach((c) => {
          const opt = document.createElement("option");
          opt.value = c.case_id;
          opt.textContent = `${c.name} (${c.status.toUpperCase()})`;
          select.appendChild(opt);
        });
      }
    });

    if (cases && cases.length > 0) {
      selectCase(cases[0].case_id);
    }
  } catch (err) {
    console.warn("Failed to load cases:", err);
  }
}

async function selectCase(caseId) {
  currentCaseId = caseId;
  const caseSelect = document.getElementById("case-select");
  const uploadCaseSelect = document.getElementById("upload-case-select");
  if (caseSelect && caseSelect.value !== caseId) caseSelect.value = caseId;
  if (uploadCaseSelect && uploadCaseSelect.value !== caseId) uploadCaseSelect.value = caseId;

  try {
    const caseData = await apiFetch(`/cases/${caseId}`);
    
    // Update Alerts view case info
    const nameEl = document.getElementById("case-name");
    const statusEl = document.getElementById("case-status");
    const idEl = document.getElementById("case-id-display");
    const descEl = document.getElementById("case-desc");
    if (nameEl) nameEl.textContent = caseData.name;
    if (statusEl) statusEl.textContent = caseData.status.toUpperCase();
    if (idEl) idEl.textContent = caseData.case_id;
    if (descEl) descEl.textContent = caseData.description || "No description";

    // Update Upload view case info
    const uName = document.getElementById("upload-case-name");
    const uStatus = document.getElementById("upload-case-status");
    const uId = document.getElementById("upload-case-id");
    if (uName) uName.textContent = caseData.name;
    if (uStatus) uStatus.textContent = caseData.status.toUpperCase();
    if (uId) uId.textContent = caseData.case_id;

    // Load datasets, alerts
    loadCaseDatasets(caseId);
    loadCaseAlerts(caseId);
  } catch (err) {
    console.error("Could not fetch case details:", err);
  }
}

async function loadCaseDatasets(caseId) {
  try {
    const datasets = await apiFetch(`/cases/${caseId}/datasets`);
    const containers = [
      document.getElementById("case-datasets-list"),
      document.getElementById("upload-case-datasets-list"),
    ];

    containers.forEach((container) => {
      if (!container) return;
      if (!datasets || datasets.length === 0) {
        container.innerHTML = `<span class="text-muted">No datasets uploaded yet</span>`;
        return;
      }
      container.innerHTML = datasets
        .map(
          (d) => `
        <div style="font-size:0.75rem; margin-bottom: 0.35rem; display:flex; justify-content:space-between; align-items:center;">
          <div><span class="text-blue">●</span> <strong>${d.name}</strong></div>
          <span style="font-family:var(--font-mono); color:var(--text-secondary);">${d.row_count || 0} rows (${d.format.toUpperCase()})</span>
        </div>
      `
        )
        .join("");
    });
  } catch (err) {
    console.warn("Could not load datasets:", err);
  }
}

// -------------------------------------------------------------
// Pipeline Execution & Progress Modal
// -------------------------------------------------------------
async function triggerAnalysisRun(caseId) {
  const runBtn = document.getElementById("btn-trigger-run");
  if (runBtn) {
    runBtn.disabled = true;
    runBtn.textContent = "Pipeline Running...";
  }

  showPipelineModal();

  try {
    const runRes = await apiFetch(`/cases/${caseId}/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });

    currentRunId = runRes.run_id;
    document.getElementById("modal-run-id").textContent = currentRunId;
    pollRunStatus(caseId, currentRunId);
  } catch (err) {
    alert("Could not start pipeline run: " + err.message);
    closePipelineModal();
    if (runBtn) {
      runBtn.disabled = false;
      runBtn.textContent = "Execute Analysis Pipeline";
    }
  }
}

function showPipelineModal() {
  const modal = document.getElementById("pipeline-modal");
  if (modal) modal.classList.add("active");
  resetModalSteps();
}

function closePipelineModal() {
  const modal = document.getElementById("pipeline-modal");
  if (modal) modal.classList.remove("active");
}

function resetModalSteps() {
  const steps = [
    "step-ingestion",
    "step-normalization",
    "step-correlation",
    "step-graph_construction",
    "step-feature_extraction",
    "step-detection_and_scoring",
    "step-reporting_and_persistence",
  ];
  steps.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.className = "stage-step";
    }
  });
  const detailEl = document.getElementById("modal-stage-detail");
  if (detailEl) detailEl.textContent = "Starting analytical engine...";
  const closeBtn = document.getElementById("btn-close-modal");
  if (closeBtn) closeBtn.style.display = "none";
}

function updateModalStage(stage, progress) {
  const stageOrder = [
    "ingestion",
    "normalization",
    "correlation",
    "graph_construction",
    "feature_extraction",
    "detection_and_scoring",
    "reporting_and_persistence",
  ];

  const currentIdx = stageOrder.indexOf(stage);

  stageOrder.forEach((st, idx) => {
    const el = document.getElementById(`step-${st}`);
    if (!el) return;
    if (idx < currentIdx) {
      el.className = "stage-step completed";
    } else if (idx === currentIdx) {
      el.className = "stage-step active";
    } else {
      el.className = "stage-step";
    }
  });

  const detailEl = document.getElementById("modal-stage-detail");
  if (detailEl) {
    detailEl.textContent = `Stage: ${stage.toUpperCase()} (${progress}%) - Correlating telemetry & extracting anomaly features`;
  }
}

function pollRunStatus(caseId, runId) {
  const statusEl = document.getElementById("run-progress-status");
  const interval = setInterval(async () => {
    try {
      const run = await apiFetch(`/cases/${caseId}/runs/${runId}`);
      if (statusEl) {
        statusEl.textContent = `Stage: ${run.stage || 'running'} (${run.progress || 0}%)`;
      }

      updateModalStage(run.stage || "ingestion", run.progress || 10);

      if (run.status === "completed" || run.status === "failed") {
        clearInterval(interval);
        const runBtn = document.getElementById("btn-trigger-run");
        if (runBtn) {
          runBtn.disabled = false;
          runBtn.textContent = "Execute Analysis Pipeline";
        }
        if (statusEl) statusEl.textContent = `Status: ${run.status.toUpperCase()}`;

        // Complete modal
        const detailEl = document.getElementById("modal-stage-detail");
        const closeBtn = document.getElementById("btn-close-modal");
        if (run.status === "completed") {
          if (detailEl) {
            detailEl.textContent = "✓ Analysis pipeline successfully completed! All detectors, rules, and reports generated.";
            detailEl.style.color = "#10b981";
          }
          // Mark all steps completed
          document.querySelectorAll(".stage-step").forEach((s) => (s.className = "stage-step completed"));
        } else {
          if (detailEl) {
            detailEl.textContent = `⚠️ Pipeline run failed: ${run.error_message || 'Unexpected error'}`;
            detailEl.style.color = "#ef4444";
          }
        }
        if (closeBtn) closeBtn.style.display = "inline-flex";

        // Refresh alerts and switch to alerts tab
        loadCaseAlerts(caseId);
        loadCaseGraph(caseId);
      }
    } catch (e) {
      clearInterval(interval);
    }
  }, 1000);
}

// -------------------------------------------------------------
// Alerts & Evidence View
// -------------------------------------------------------------
async function loadCaseAlerts(caseId) {
  try {
    const res = await apiFetch(`/cases/${caseId}/alerts?page_size=150`);
    alertsData = res.items || [];
    renderMetrics(alertsData, res.total);
    renderAlertsTable(alertsData);
  } catch (err) {
    console.error("Could not load alerts:", err);
  }
}

function renderMetrics(alerts, total) {
  let criticalCount = 0;
  let highCount = 0;
  let mediumCount = 0;

  alerts.forEach((a) => {
    const sev = (a.severity || "").toUpperCase();
    if (sev === "CRITICAL") criticalCount++;
    else if (sev === "HIGH") highCount++;
    else if (sev === "MEDIUM") mediumCount++;
  });

  const totalEl = document.getElementById("metric-total-alerts");
  const critEl = document.getElementById("metric-critical");
  const highEl = document.getElementById("metric-high");
  const medEl = document.getElementById("metric-medium");

  if (totalEl) totalEl.textContent = total !== undefined ? total : alerts.length;
  if (critEl) critEl.textContent = criticalCount;
  if (highEl) highEl.textContent = highCount;
  if (medEl) medEl.textContent = mediumCount;
}

function renderAlertsTable(alerts) {
  const tbody = document.getElementById("alerts-table-body");
  if (!tbody) return;

  if (!alerts || alerts.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No alerts generated for this case yet. Click "Execute Analysis Pipeline".</td></tr>`;
    return;
  }

  tbody.innerHTML = alerts
    .map((a) => {
      const sevClass = `severity-${(a.severity || "low").toLowerCase()}`;
      const score = Math.round(a.priority_score || 0);
      let scoreColor = "#94a3b8";
      if (score >= 80) scoreColor = "#ef4444";
      else if (score >= 60) scoreColor = "#f97316";
      else if (score >= 40) scoreColor = "#f59e0b";

      const reasonsList = a.top_reasons || a.reasons || [];
      const reasons = (Array.isArray(reasonsList) && reasonsList.length > 0)
        ? reasonsList.join(" • ")
        : (typeof a.reasons === "string" ? a.reasons : (a.ollama_summary || "Multi-Dimensional Anomaly Signal"));

      return `
      <tr onclick="selectAlert('${a.alert_id}')" id="alert-row-${a.alert_id}">
        <td>
          <span class="severity-tag ${sevClass}">${a.severity}</span>
        </td>
        <td>
          <span class="score-bar-container">
            <span style="font-weight:700; color:${scoreColor}; font-family:var(--font-mono); width: 28px;">${score}</span>
            <span class="score-bar-bg">
              <span class="score-bar-fill" style="width: ${score}%; background: ${scoreColor};"></span>
            </span>
          </span>
        </td>
        <td>
          <span class="entity-id" title="${a.entity_id}">${a.entity_id}</span>
        </td>
        <td style="max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-secondary);" title="${escapeHtml(reasons)}">
          ${reasons}
        </td>
        <td style="text-align: right;">
          <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); inspectEntity('${a.entity_id}')">Investigate</button>
        </td>
      </tr>
    `;
    })
    .join("");

  if (alerts.length > 0 && !selectedAlertId) {
    selectAlert(alerts[0].alert_id);
  }
}

function filterAlerts(severity) {
  if (!severity || severity === "ALL") {
    renderAlertsTable(alertsData);
  } else {
    const filtered = alertsData.filter((a) => (a.severity || "").toUpperCase() === severity.toUpperCase());
    renderAlertsTable(filtered);
  }
}

let activeProvenanceRecords = [];

function updateScoreCards(comp) {
  const anom = comp && comp.anomaly_score !== undefined ? Number(comp.anomaly_score) : 0;
  const behav = comp && comp.behavior_score !== undefined ? Number(comp.behavior_score) : 0;
  const graph = comp && comp.graph_score !== undefined ? Number(comp.graph_score) : 0;
  const net = comp && comp.network_score !== undefined ? Number(comp.network_score) : 0;

  const elAnom = document.getElementById("score-anomaly");
  const elBehav = document.getElementById("score-behavior");
  const elGraph = document.getElementById("score-graph");
  const elNet = document.getElementById("score-network");
  if (elAnom) elAnom.textContent = anom.toFixed(2);
  if (elBehav) elBehav.textContent = behav.toFixed(2);
  if (elGraph) elGraph.textContent = graph.toFixed(2);
  if (elNet) elNet.textContent = net.toFixed(2);

  const elAnomPts = document.getElementById("score-anomaly-pts");
  const elBehavPts = document.getElementById("score-behavior-pts");
  const elGraphPts = document.getElementById("score-graph-pts");
  const elNetPts = document.getElementById("score-network-pts");
  if (elAnomPts) elAnomPts.textContent = `+${(anom * 40).toFixed(1)} pts`;
  if (elBehavPts) elBehavPts.textContent = `+${(behav * 30).toFixed(1)} pts`;
  if (elGraphPts) elGraphPts.textContent = `+${(graph * 20).toFixed(1)} pts`;
  if (elNetPts) elNetPts.textContent = `+${(net * 10).toFixed(1)} pts`;

  const barAnom = document.getElementById("score-anomaly-bar");
  const barBehav = document.getElementById("score-behavior-bar");
  const barGraph = document.getElementById("score-graph-bar");
  const barNet = document.getElementById("score-network-bar");
  if (barAnom) barAnom.style.width = `${Math.min(100, Math.max(0, anom * 100))}%`;
  if (barBehav) barBehav.style.width = `${Math.min(100, Math.max(0, behav * 100))}%`;
  if (barGraph) barGraph.style.width = `${Math.min(100, Math.max(0, graph * 100))}%`;
  if (barNet) barNet.style.width = `${Math.min(100, Math.max(0, net * 100))}%`;
}

function toggleProvenanceList(total) {
  const hiddenDiv = document.getElementById("prov-hidden-records");
  const btn = document.getElementById("btn-toggle-prov");
  if (!hiddenDiv || !btn) return;
  if (hiddenDiv.style.display === "none") {
    hiddenDiv.style.display = "flex";
    btn.textContent = "- Show fewer records";
  } else {
    hiddenDiv.style.display = "none";
    btn.textContent = `+ Show all ${total} records`;
  }
}

function copyAllProvenanceIds() {
  if (!activeProvenanceRecords || activeProvenanceRecords.length === 0) return;
  navigator.clipboard.writeText(activeProvenanceRecords.join(", ")).then(() => {
    const btn = document.getElementById("btn-copy-prov");
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = "✓ Copied!";
      setTimeout(() => (btn.innerHTML = orig), 2000);
    }
  });
}

async function selectAlert(alertId) {
  selectedAlertId = alertId;
  document.querySelectorAll("#alerts-table-body tr").forEach((tr) => tr.classList.remove("selected"));
  const row = document.getElementById(`alert-row-${alertId}`);
  if (row) row.classList.add("selected");

  const alert = alertsData.find((a) => a.alert_id === alertId);
  if (!alert) return;

  const drawer = document.getElementById("evidence-drawer");
  if (!drawer) return;
  drawer.style.display = "block";

  document.getElementById("evidence-entity-id").textContent = alert.entity_id;
  const sevEl = document.getElementById("evidence-priority-tier");
  if (sevEl) {
    sevEl.textContent = `${alert.severity} (${alert.priority_score.toFixed(1)} / 100)`;
    sevEl.className = `severity-tag severity-${(alert.severity || "low").toLowerCase()}`;
  }

  const btnInvestigate = document.getElementById("btn-evidence-investigate");
  if (btnInvestigate) {
    btnInvestigate.onclick = () => inspectEntity(alert.entity_id);
  }

  // Pre-fill score cards immediately with available data (zero latency/flicker)
  const initialComp = alert.score_components || {
    anomaly_score: alert.anomaly_score || 0,
    behavior_score: alert.behavior_score || 0,
    graph_score: alert.graph_score || 0,
    network_score: alert.network_score || 0
  };
  updateScoreCards(initialComp);

  try {
    const evidencePack = await apiFetch(`/cases/${currentCaseId}/alerts/${alertId}/evidence`);
    
    // Components
    const comp = evidencePack.score_components || initialComp;
    updateScoreCards(comp);

    // Explanations
    const reasonsContainer = document.getElementById("evidence-reasons-list");
    reasonsContainer.innerHTML = "";
    const rawReasons = (evidencePack.reasons && evidencePack.reasons.length > 0)
      ? evidencePack.reasons
      : (alert.top_reasons || alert.reasons || []);

    if (rawReasons && rawReasons.length > 0) {
      rawReasons.forEach((r, idx) => {
        const item = document.createElement("div");
        
        let ruleCode = "RULE_FORENSIC_SIGNAL";
        let headline = "Forensic Finding";
        let explanation = "";
        let observed = null;
        let threshold = null;
        let unit = "";
        let type = "rule";

        if (typeof r === "string") {
          explanation = r;
          if (r.includes("peeling") || r.includes("Peeling")) {
            ruleCode = "RULE_PEELING_CHAIN";
            headline = "Peeling Chain Transfer Pattern";
          } else if (r.includes("fan-out") || r.includes("Fan-out") || r.includes("dispersal")) {
            ruleCode = "RULE_HIGH_FAN_OUT";
            headline = "High Fan-Out Dispersal Pattern";
          } else if (r.includes("repeated") || r.includes("Repeated")) {
            ruleCode = "RULE_REPEATED_VALUE";
            headline = "Repeated Identical Value Transfers";
          } else if (r.includes("dust") || r.includes("Dust")) {
            ruleCode = "RULE_DUST_ATTACK";
            headline = "Sub-Dust Threshold UTXO Splitting";
          } else if (r.includes("Isolation Forest") || r.includes("outlier") || r.includes("percentile")) {
            ruleCode = "DETECTOR_ISOLATION_FOREST";
            headline = "Statistical Multi-Feature Outlier";
            type = "feature";
          } else if (r.includes("network") || r.includes("relay") || r.includes("IP")) {
            ruleCode = "NETWORK_CONCURRENCY";
            headline = "Multi-IP Relay & Port Dispersion";
            type = "network";
          } else {
            headline = "Forensic AML Rule Hit";
          }
        } else if (typeof r === "object" && r !== null) {
          ruleCode = r.rule_code || r.feature || "RULE";
          headline = r.headline || ruleCode.replace("RULE_", "").replace(/_/g, " ");
          explanation = r.explanation || r.text || "";
          observed = (r.observed_value !== undefined && r.observed_value !== null) ? r.observed_value : r.value;
          threshold = (r.threshold !== undefined && r.threshold !== null) ? r.threshold : r.threshold_or_baseline;
          unit = r.unit || "";
          type = r.type || "rule";
        }

        let tagColor = "#f97316";
        let tagBg = "rgba(249, 115, 22, 0.12)";
        let tagBorder = "rgba(249, 115, 22, 0.35)";
        let tagText = "RULE HIT";
        if (type === "feature" || ruleCode.includes("FOREST") || ruleCode.includes("ANOMALY")) {
          tagColor = "#38bdf8";
          tagBg = "rgba(56, 189, 248, 0.12)";
          tagBorder = "rgba(56, 189, 248, 0.35)";
          tagText = "ANOMALY";
        } else if (type === "network") {
          tagColor = "#10b981";
          tagBg = "rgba(16, 185, 129, 0.12)";
          tagBorder = "rgba(16, 185, 129, 0.35)";
          tagText = "NETWORK";
        } else if (type === "graph") {
          tagColor = "#818cf8";
          tagBg = "rgba(129, 140, 248, 0.12)";
          tagBorder = "rgba(129, 140, 248, 0.35)";
          tagText = "GRAPH";
        }

        let obsHtml = "";
        if (observed !== null && observed !== undefined) {
          const obsFmt = typeof observed === "number" ? (Number.isInteger(observed) ? observed : observed.toFixed(3)) : observed;
          const threshFmt = typeof threshold === "number" ? (Number.isInteger(threshold) ? threshold : threshold.toFixed(3)) : threshold;
          obsHtml = `
            <div style="margin-top: 0.45rem; display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.08); padding: 3px 8px; border-radius: 4px; font-family: var(--font-mono); font-size: 0.73rem;">
              <span style="color: var(--text-muted);">Observed:</span>
              <span style="color: #facc15; font-weight: 700;">${obsFmt} ${unit}</span>
              ${threshold !== null && threshold !== undefined ? `<span style="color: var(--text-muted); margin-left: 0.3rem;">| Threshold: <strong style="color: #94a3b8;">${threshFmt} ${unit}</strong></span>` : ''}
            </div>
          `;
        }

        item.style.cssText = `background: var(--bg-card); border: 1px solid var(--border-color); border-left: 3px solid ${tagColor}; border-radius: var(--radius-sm); padding: 0.75rem 0.9rem; margin-bottom: 0.6rem;`;
        item.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; margin-bottom: 0.25rem;">
            <div style="font-weight: 700; color: #fff; font-size: 0.85rem; display: flex; align-items: center; gap: 0.45rem;">
              <span>${headline}</span>
              <span style="font-size: 0.68rem; font-family: var(--font-mono); color: var(--text-muted);">[${ruleCode}]</span>
            </div>
            <span style="font-size: 0.65rem; font-weight: 700; color: ${tagColor}; background: ${tagBg}; border: 1px solid ${tagBorder}; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px;">${tagText}</span>
          </div>
          <div style="color: var(--text-secondary); font-size: 0.8rem; line-height: 1.45;">${explanation}</div>
          ${obsHtml}
        `;
        reasonsContainer.appendChild(item);
      });
    } else {
      reasonsContainer.innerHTML = `<div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 0.85rem; color: var(--text-secondary); font-size: 0.82rem;"><span style="color: var(--accent-blue); font-weight: 600;">Multi-Engine Evaluation:</span> High multi-dimensional feature divergence identified by the unsupervised Isolation Forest detector.</div>`;
    }

    // Provenance Records
    activeProvenanceRecords = (evidencePack.source_records && evidencePack.source_records.length > 0)
      ? evidencePack.source_records
      : (evidencePack.observed_evidence?.source_record_ids || []);

    const countBadge = document.getElementById("prov-count-badge");
    if (countBadge) {
      countBadge.textContent = `${activeProvenanceRecords.length} Records Verified`;
    }

    const provContainer = document.getElementById("evidence-provenance-chips");
    if (provContainer) {
      if (activeProvenanceRecords.length > 0) {
        const displayLimit = 24;
        const initial = activeProvenanceRecords.slice(0, displayLimit);
        const chipsHtml = initial.map((r) => `<span class="prov-record-chip" title="Immutable Parquet Record: ${r}">${r}</span>`).join("");
        let extraHtml = "";
        if (activeProvenanceRecords.length > displayLimit) {
          extraHtml = `
            <div id="prov-hidden-records" style="display: none; flex-wrap: wrap; gap: 0.35rem; width: 100%; margin-top: 0.35rem;">
              ${activeProvenanceRecords.slice(displayLimit).map((r) => `<span class="prov-record-chip">${r}</span>`).join("")}
            </div>
            <button id="btn-toggle-prov" class="btn btn-outline btn-sm" style="margin-top: 0.5rem; font-size: 0.72rem; padding: 2px 8px;" onclick="toggleProvenanceList(${activeProvenanceRecords.length})">
              + Show all ${activeProvenanceRecords.length} records
            </button>
          `;
        }
        provContainer.innerHTML = `
          <div style="display: flex; flex-wrap: wrap; gap: 0.35rem; width: 100%;">
            ${chipsHtml}
          </div>
          ${extraHtml}
        `;
      } else {
        provContainer.innerHTML = `<span style="color: var(--text-muted); font-size: 0.8rem;">No direct raw source record IDs linked to this entity.</span>`;
      }
    }
  } catch (err) {
    console.warn("Could not load full evidence pack:", err);
  }
}

// -------------------------------------------------------------
// Interactive Forensic Entity Graph Visualizer & Engine
// -------------------------------------------------------------
let canvas, ctx;
let graphNodes = [];
let graphEdges = [];
let nodePositions = new Map(); // id -> { x, y, vx, vy, radius, node, isFlagged }
let adjacencyMap = new Map();  // id -> { inEdges: [], outEdges: [], neighbors: Set }
let selectedNodeId = null;
let hoveredNodeId = null;
let graphFilterType = "ALL";   // 'ALL', 'wallet', 'transaction', 'ip', 'FLAGGED'
let graphLayoutMode = "force"; // 'force', 'flow', 'cluster'
let graphLimit = 250;
let graphSearchTerm = "";
let zoom = 1.0;
let panX = 0;
let panY = 0;
let isDragging = false;
let draggedNode = null;
let lastMouseX = 0;
let lastMouseY = 0;
let rawReportMarkdown = "";

function initGraphCanvas() {
  canvas = document.getElementById("graph-canvas");
  if (!canvas) return;
  ctx = canvas.getContext("2d");

  window.addEventListener("resize", resizeCanvas);
  resizeCanvas();

  canvas.addEventListener("mousedown", onMouseDown);
  canvas.addEventListener("mousemove", onMouseMove);
  canvas.addEventListener("mouseup", onMouseUp);
  canvas.addEventListener("wheel", onWheel, { passive: false });
  canvas.addEventListener("dblclick", onDoubleClick);
}

function resizeCanvas() {
  if (!canvas) return;
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
  drawGraph();
}

async function loadCaseGraph(caseId) {
  try {
    const res = await apiFetch(`/cases/${caseId}/graph?limit=${graphLimit}`);
    graphData = res;
    processGraphData(res.nodes || [], res.edges || []);
  } catch (err) {
    console.error("Could not load case graph:", err);
  }
}

function processGraphData(nodes, edges) {
  graphNodes = nodes;
  graphEdges = edges;

  // Build adjacency map for 1-hop neighborhood & ego isolation
  adjacencyMap.clear();
  nodes.forEach((n) => {
    adjacencyMap.set(n.id, { inEdges: [], outEdges: [], neighbors: new Set() });
  });

  edges.forEach((e) => {
    const s = adjacencyMap.get(e.source);
    const t = adjacencyMap.get(e.target);
    if (s) {
      s.outEdges.push(e);
      s.neighbors.add(e.target);
    }
    if (t) {
      t.inEdges.push(e);
      t.neighbors.add(e.source);
    }
  });

  applyLayout();
}

function setGraphLayoutMode(mode) {
  graphLayoutMode = mode;
  applyLayout();
}

function setGraphLimit(limit) {
  graphLimit = parseInt(limit, 10) || 250;
  if (currentCaseId) loadCaseGraph(currentCaseId);
}

function filterGraphType(type) {
  graphFilterType = type;
  document.querySelectorAll("#graph-view .pill-btn").forEach((b) => b.classList.remove("active"));
  const btn = document.getElementById(`btn-graph-filter-${type.toLowerCase()}`);
  if (btn) btn.classList.add("active");
  drawGraph();
}

function searchGraphNodes(term) {
  graphSearchTerm = (term || "").trim().toLowerCase();
  if (graphSearchTerm) {
    // Find first matching node and center view
    for (const [id, pos] of nodePositions.entries()) {
      if (id.toLowerCase().includes(graphSearchTerm) || (pos.node.label && pos.node.label.toLowerCase().includes(graphSearchTerm))) {
        panToNode(pos);
        selectNode(pos.node);
        break;
      }
    }
  }
  drawGraph();
}

function panToNode(pos) {
  if (!canvas) return;
  zoom = 1.35;
  panX = canvas.width / 2 - pos.x * zoom;
  panY = canvas.height / 2 - pos.y * zoom;
  updateZoomBadge();
}

// -------------------------------------------------------------
// Layout Algorithms (Force-Directed, Flow/Sankey, Clusters)
// -------------------------------------------------------------
function applyLayout() {
  if (!canvas || graphNodes.length === 0) return;

  nodePositions.clear();
  const width = canvas.width || 900;
  const height = canvas.height || 680;
  const centerX = width / 2;
  const centerY = height / 2;

  // Initialize initial positions
  graphNodes.forEach((n, idx) => {
    let radius = 12;
    if (n.type === "wallet") radius = 15;
    else if (n.type === "transaction") radius = 13;
    else if (n.type === "ip") radius = 11;

    // Check if entity has an alert
    const isFlagged = alertsData.some((a) => a.entity_id === n.id || a.entity_id === `wallet:${n.id}`);

    // Seed in a loose circle to start
    const angle = (idx / Math.max(graphNodes.length, 1)) * 2 * Math.PI;
    const spread = 200 + (idx % 5) * 40;
    const x = centerX + spread * Math.cos(angle);
    const y = centerY + spread * Math.sin(angle);

    nodePositions.set(n.id, {
      x,
      y,
      vx: 0,
      vy: 0,
      radius,
      node: n,
      isFlagged,
    });
  });

  if (graphLayoutMode === "flow") {
    computeFlowLayout(width, height);
  } else if (graphLayoutMode === "cluster") {
    computeClusterLayout(width, height);
  } else {
    computeForceLayout(centerX, centerY);
  }

  fitGraphToViewport();
}

// Organic Spring-Embedder Simulation with Collision Detection
function computeForceLayout(centerX, centerY) {
  const nodes = Array.from(nodePositions.values());
  const edges = graphEdges;
  const iterations = 85;
  const k = Math.sqrt((800 * 600) / Math.max(nodes.length, 1)) * 0.9;

  for (let iter = 0; iter < iterations; iter++) {
    // 1. Repulsion between all node pairs with collision boundary
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const u = nodes[i];
        const v = nodes[j];
        let dx = v.x - u.x;
        let dy = v.y - u.y;
        let dist = Math.sqrt(dx * dx + dy * dy) || 1;

        const minDist = u.radius + v.radius + 36; // Collision threshold
        let force = (k * k) / dist;
        if (dist < minDist) {
          force *= 3.5; // Strong bounce repulsion if overlapping
        }

        const fx = (dx / dist) * force * 0.12;
        const fy = (dy / dist) * force * 0.12;

        u.vx -= fx;
        u.vy -= fy;
        v.vx += fx;
        v.vy += fy;
      }
    }

    // 2. Spring Attraction along Edges
    for (let e of edges) {
      const u = nodePositions.get(e.source);
      const v = nodePositions.get(e.target);
      if (!u || !v) continue;

      let dx = v.x - u.x;
      let dy = v.y - u.y;
      let dist = Math.sqrt(dx * dx + dy * dy) || 1;

      const restLength = 90;
      const force = ((dist - restLength) * 0.05);

      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      u.vx += fx;
      u.vy += fy;
      v.vx -= fx;
      v.vy -= fy;
    }

    // 3. Gentle Centering Gravity & Velocity Damping
    const temp = 0.85 * (1 - iter / iterations);
    for (let n of nodes) {
      const dxCenter = centerX - n.x;
      const dyCenter = centerY - n.y;
      n.vx += dxCenter * 0.015;
      n.vy += dyCenter * 0.015;

      n.x += n.vx * temp;
      n.y += n.vy * temp;
      n.vx *= 0.75;
      n.vy *= 0.75;
    }
  }
}

// Structured Forensic Flow (Source Wallets -> Transactions -> Destination Wallets -> Relays)
function computeFlowLayout(width, height) {
  const tiers = {
    inputs: [],
    transactions: [],
    outputs: [],
    relays: [],
  };

  graphNodes.forEach((n) => {
    const adj = adjacencyMap.get(n.id);
    if (n.type === "transaction") {
      tiers.transactions.push(n.id);
    } else if (n.type === "ip" || n.type === "asn" || n.type === "country") {
      tiers.relays.push(n.id);
    } else if (adj && adj.outEdges.length > 0 && adj.inEdges.length === 0) {
      tiers.inputs.push(n.id);
    } else {
      tiers.outputs.push(n.id);
    }
  });

  const columns = [
    { name: "inputs", nodes: tiers.inputs, x: 120 },
    { name: "transactions", nodes: tiers.transactions, x: 380 },
    { name: "outputs", nodes: tiers.outputs, x: 640 },
    { name: "relays", nodes: tiers.relays, x: 900 },
  ];

  columns.forEach((col) => {
    const count = col.nodes.length;
    const spacing = Math.max(50, Math.min(height / Math.max(count, 1), 70));
    const startY = Math.max(60, (height - count * spacing) / 2);

    col.nodes.forEach((nid, idx) => {
      const pos = nodePositions.get(nid);
      if (pos) {
        pos.x = col.x + (Math.random() - 0.5) * 15;
        pos.y = startY + idx * spacing;
      }
    });
  });
}

// Community Cluster Layout
function computeClusterLayout(width, height) {
  const visited = new Set();
  const clusters = [];

  graphNodes.forEach((n) => {
    if (!visited.has(n.id)) {
      const comp = [];
      const queue = [n.id];
      visited.add(n.id);
      while (queue.length > 0) {
        const curr = queue.shift();
        comp.push(curr);
        const adj = adjacencyMap.get(curr);
        if (adj) {
          adj.neighbors.forEach((neigh) => {
            if (!visited.has(neigh) && nodePositions.has(neigh)) {
              visited.add(neigh);
              queue.push(neigh);
            }
          });
        }
      }
      clusters.push(comp);
    }
  });

  // Sort clusters largest first
  clusters.sort((a, b) => b.length - a.length);

  const centerX = width / 2;
  const centerY = height / 2;
  const clusterCount = Math.min(clusters.length, 8);

  clusters.slice(0, clusterCount).forEach((comp, cIdx) => {
    const angle = (cIdx / clusterCount) * 2 * Math.PI;
    const clusterDist = clusterCount > 1 ? 260 : 0;
    const cx = centerX + clusterDist * Math.cos(angle);
    const cy = centerY + clusterDist * Math.sin(angle);

    comp.forEach((nid, idx) => {
      const pos = nodePositions.get(nid);
      if (pos) {
        if (idx === 0) {
          pos.x = cx;
          pos.y = cy;
        } else {
          const subAngle = (idx / comp.length) * 2 * Math.PI;
          const subRadius = 45 + Math.floor(idx / 8) * 40;
          pos.x = cx + subRadius * Math.cos(subAngle);
          pos.y = cy + subRadius * Math.sin(subAngle);
        }
      }
    });
  });
}

function fitGraphToViewport() {
  if (!canvas || nodePositions.size === 0) return;

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  nodePositions.forEach((pos) => {
    if (pos.x < minX) minX = pos.x;
    if (pos.x > maxX) maxX = pos.x;
    if (pos.y < minY) minY = pos.y;
    if (pos.y > maxY) maxY = pos.y;
  });

  const graphWidth = maxX - minX || 400;
  const graphHeight = maxY - minY || 400;

  const scaleX = (canvas.width * 0.85) / graphWidth;
  const scaleY = (canvas.height * 0.85) / graphHeight;
  zoom = Math.min(Math.max(Math.min(scaleX, scaleY), 0.25), 2.0);

  panX = (canvas.width - (minX + maxX) * zoom) / 2;
  panY = (canvas.height - (minY + maxY) * zoom) / 2;

  updateZoomBadge();
  drawGraph();
}

function resetGraphView() {
  fitGraphToViewport();
}

function zoomIn() {
  if (!canvas) return;
  zoomAt(canvas.width / 2, canvas.height / 2, 1.25);
}

function zoomOut() {
  if (!canvas) return;
  zoomAt(canvas.width / 2, canvas.height / 2, 0.8);
}

function zoomAt(canvasX, canvasY, factor) {
  const worldX = (canvasX - panX) / zoom;
  const worldY = (canvasY - panY) / zoom;
  const newZoom = Math.min(Math.max(zoom * factor, 0.15), 4.5);
  panX = canvasX - worldX * newZoom;
  panY = canvasY - worldY * newZoom;
  zoom = newZoom;
  updateZoomBadge();
  drawGraph();
}

function updateZoomBadge() {
  const badge = document.getElementById("graph-zoom-level");
  if (badge) {
    badge.textContent = `${Math.round(zoom * 100)}%`;
  }
}

// -------------------------------------------------------------
// Canvas Drawing & Highlighting
// -------------------------------------------------------------
function drawGraph() {
  if (!ctx || !canvas) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Background grid
  ctx.save();
  ctx.strokeStyle = "rgba(255, 255, 255, 0.02)";
  ctx.lineWidth = 1;
  const gridSize = 40 * zoom;
  const startX = panX % gridSize;
  const startY = panY % gridSize;
  for (let x = startX; x < canvas.width; x += gridSize) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.stroke();
  }
  for (let y = startY; y < canvas.height; y += gridSize) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.stroke();
  }
  ctx.restore();

  ctx.save();
  ctx.translate(panX, panY);
  ctx.scale(zoom, zoom);

  // Determine Ego Neighbors Set
  let egoSet = null;
  let egoEdges = null;
  if (selectedNodeId && adjacencyMap.has(selectedNodeId)) {
    egoSet = new Set(adjacencyMap.get(selectedNodeId).neighbors);
    egoSet.add(selectedNodeId);
    egoEdges = new Set([
      ...adjacencyMap.get(selectedNodeId).inEdges,
      ...adjacencyMap.get(selectedNodeId).outEdges,
    ]);
  }

  // Draw Edges
  graphEdges.forEach((e) => {
    const sPos = nodePositions.get(e.source);
    const tPos = nodePositions.get(e.target);
    if (!sPos || !tPos) return;

    // Filter check
    if (!isNodeVisible(sPos.node) || !isNodeVisible(tPos.node)) return;

    let isEgoEdge = false;
    let opacity = 0.4;
    let lineWidth = 1.2;

    if (egoSet) {
      if (egoEdges && (e.source === selectedNodeId || e.target === selectedNodeId)) {
        isEgoEdge = true;
        opacity = 1.0;
        lineWidth = 2.5;
      } else {
        opacity = 0.08;
      }
    }

    ctx.lineWidth = lineWidth;
    if (e.type === "SPENT_FROM") {
      ctx.strokeStyle = `rgba(239, 68, 68, ${opacity})`;
    } else if (e.type === "SENT_TO") {
      ctx.strokeStyle = `rgba(56, 189, 248, ${opacity})`;
    } else if (e.type === "RELAYED_BY") {
      ctx.strokeStyle = `rgba(245, 158, 11, ${opacity})`;
    } else {
      ctx.strokeStyle = `rgba(148, 163, 184, ${opacity})`;
    }

    ctx.beginPath();
    ctx.moveTo(sPos.x, sPos.y);
    ctx.lineTo(tPos.x, tPos.y);
    ctx.stroke();

    // Draw Arrowhead
    const angle = Math.atan2(tPos.y - sPos.y, tPos.x - sPos.x);
    const arrowDist = tPos.radius + 6;
    const arrowX = tPos.x - arrowDist * Math.cos(angle);
    const arrowY = tPos.y - arrowDist * Math.sin(angle);

    ctx.fillStyle = ctx.strokeStyle;
    ctx.beginPath();
    ctx.moveTo(arrowX, arrowY);
    ctx.lineTo(arrowX - 8 * Math.cos(angle - Math.PI / 6), arrowY - 8 * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(arrowX - 8 * Math.cos(angle + Math.PI / 6), arrowY - 8 * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();

    // Edge Amount Badge on ego edges
    if (isEgoEdge && e.weight && e.weight > 0) {
      const midX = (sPos.x + tPos.x) / 2;
      const midY = (sPos.y + tPos.y) / 2;
      ctx.fillStyle = "rgba(10, 14, 23, 0.85)";
      ctx.fillRect(midX - 22, midY - 8, 44, 16);
      ctx.fillStyle = "#f59e0b";
      ctx.font = "9px monospace";
      ctx.textAlign = "center";
      ctx.fillText(`${e.weight.toFixed(3)} BTC`, midX, midY + 4);
    }
  });

  // Draw Nodes
  nodePositions.forEach((pos) => {
    const n = pos.node;
    if (!isNodeVisible(n)) return;

    let isSelected = selectedNodeId === n.id;
    let isEgo = egoSet ? egoSet.has(n.id) : true;
    let isHovered = hoveredNodeId === n.id;

    let alpha = 1.0;
    if (egoSet && !isEgo) alpha = 0.15;

    ctx.globalAlpha = alpha;

    // Glowing Halo for selected or hovered node
    if (isSelected) {
      ctx.save();
      ctx.shadowBlur = 18;
      ctx.shadowColor = "#f59e0b";
      ctx.strokeStyle = "#f59e0b";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, pos.radius + 6, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.restore();
    } else if (isHovered) {
      ctx.save();
      ctx.shadowBlur = 12;
      ctx.shadowColor = "#38bdf8";
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, pos.radius + 4, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.restore();
    }

    // Flagged Warning Ring
    if (pos.isFlagged) {
      ctx.save();
      ctx.strokeStyle = "#f97316";
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, pos.radius + 4, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.restore();
    }

    // Node Body
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, pos.radius, 0, 2 * Math.PI);

    if (n.type === "wallet") {
      ctx.fillStyle = "#38bdf8";
    } else if (n.type === "transaction") {
      ctx.fillStyle = "#f59e0b";
    } else if (n.type === "ip") {
      ctx.fillStyle = "#ef4444";
    } else {
      ctx.fillStyle = "#a855f7";
    }
    ctx.fill();

    ctx.strokeStyle = isSelected ? "#ffffff" : "rgba(255, 255, 255, 0.7)";
    ctx.lineWidth = isSelected ? 2 : 1.2;
    ctx.stroke();

    // Node Labels
    const shouldShowLabel = isSelected || isHovered || pos.isFlagged || zoom >= 0.75;
    if (shouldShowLabel && alpha > 0.3) {
      const label = n.label || n.id;
      const shortText = label.length > 14 ? `${label.slice(0, 7)}...${label.slice(-4)}` : label;

      ctx.font = isSelected ? "bold 11px monospace" : "10px monospace";
      ctx.textAlign = "center";

      // Pill backdrop for selected or hovered
      if (isSelected || isHovered) {
        const textWidth = ctx.measureText(shortText).width;
        ctx.fillStyle = "rgba(10, 14, 23, 0.88)";
        ctx.fillRect(pos.x - textWidth / 2 - 4, pos.y + pos.radius + 3, textWidth + 8, 14);
      }

      ctx.fillStyle = isSelected ? "#38bdf8" : pos.isFlagged ? "#fdba74" : "#e2e8f0";
      ctx.fillText(shortText, pos.x, pos.y + pos.radius + 14);
    }

    ctx.globalAlpha = 1.0;
  });

  ctx.restore();
}

function isNodeVisible(node) {
  if (graphFilterType === "wallet" && node.type !== "wallet") return false;
  if (graphFilterType === "transaction" && node.type !== "transaction") return false;
  if (graphFilterType === "ip" && node.type !== "ip") return false;
  if (graphFilterType === "FLAGGED") {
    const isAlert = alertsData.some((a) => a.entity_id === node.id || a.entity_id === `wallet:${node.id}`);
    if (!isAlert) return false;
  }
  if (graphSearchTerm) {
    const matchId = node.id.toLowerCase().includes(graphSearchTerm);
    const matchLabel = node.label && node.label.toLowerCase().includes(graphSearchTerm);
    if (!matchId && !matchLabel) return false;
  }
  return true;
}

function getNodeAt(x, y) {
  const worldX = (x - panX) / zoom;
  const worldY = (y - panY) / zoom;

  for (const [id, pos] of nodePositions.entries()) {
    if (!isNodeVisible(pos.node)) continue;
    const dx = worldX - pos.x;
    const dy = worldY - pos.y;
    if (Math.sqrt(dx * dx + dy * dy) <= pos.radius + 6) {
      return pos;
    }
  }
  return null;
}

// -------------------------------------------------------------
// Mouse & Touch Controls
// -------------------------------------------------------------
function onMouseDown(e) {
  const rect = canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  draggedNode = getNodeAt(mouseX, mouseY);
  isDragging = true;
  lastMouseX = mouseX;
  lastMouseY = mouseY;

  if (draggedNode) {
    selectNode(draggedNode.node);
  } else {
    // Clicked background -> clear selection if not dragging
  }
}

function onMouseMove(e) {
  const rect = canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  if (isDragging) {
    const dx = mouseX - lastMouseX;
    const dy = mouseY - lastMouseY;

    if (draggedNode) {
      draggedNode.x += dx / zoom;
      draggedNode.y += dy / zoom;
    } else {
      panX += dx;
      panY += dy;
    }

    lastMouseX = mouseX;
    lastMouseY = mouseY;
    drawGraph();
  } else {
    // Hover check
    const hover = getNodeAt(mouseX, mouseY);
    if (hover) {
      canvas.style.cursor = "pointer";
      if (hoveredNodeId !== hover.node.id) {
        hoveredNodeId = hover.node.id;
        showTooltip(hover.node, e.clientX, e.clientY);
        drawGraph();
      }
    } else {
      canvas.style.cursor = "default";
      if (hoveredNodeId !== null) {
        hoveredNodeId = null;
        hideTooltip();
        drawGraph();
      }
    }
  }
}

function onMouseUp(e) {
  isDragging = false;
  draggedNode = null;
}

function onWheel(e) {
  e.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  const factor = e.deltaY < 0 ? 1.15 : 0.85;
  zoomAt(mouseX, mouseY, factor);
}

function onDoubleClick(e) {
  const rect = canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  const target = getNodeAt(mouseX, mouseY);
  if (target) {
    panToNode(target);
    selectNode(target.node);
    drawGraph();
  }
}

function showTooltip(node, clientX, clientY) {
  const tip = document.getElementById("graph-tooltip");
  if (!tip) return;
  const alert = alertsData.find((a) => a.entity_id === node.id || a.entity_id === `wallet:${node.id}`);
  const score = alert ? `${alert.priority_score.toFixed(1)}/100 (${alert.severity})` : "Standard";

  tip.innerHTML = `
    <div style="font-weight:700; color:#fff; text-transform:uppercase; font-size:0.7rem;">${node.type}</div>
    <div style="font-family:var(--font-mono); color:var(--accent-blue); margin: 0.2rem 0;">${node.label || node.id}</div>
    <div style="color:var(--text-secondary); font-size:0.72rem;">Score: <span style="color:${alert ? '#ef4444' : '#10b981'}; font-weight:700;">${score}</span></div>
  `;
  tip.style.display = "block";
  tip.style.left = `${clientX + 14}px`;
  tip.style.top = `${clientY + 14}px`;
}

function hideTooltip() {
  const tip = document.getElementById("graph-tooltip");
  if (tip) tip.style.display = "none";
}

// -------------------------------------------------------------
// Interactive Node Inspector
// -------------------------------------------------------------
function selectNode(node) {
  selectedNodeId = node.id;
  showNodeInspector(node);
  drawGraph();
}

function closeNodeInspector() {
  selectedNodeId = null;
  const inspector = document.getElementById("graph-inspector");
  if (inspector) inspector.style.display = "none";
  drawGraph();
}

async function showNodeInspector(node) {
  const inspector = document.getElementById("graph-inspector");
  if (!inspector) return;
  inspector.style.display = "block";

  const typeEl = document.getElementById("inspector-node-type");
  const idEl = document.getElementById("inspector-node-id");
  const badgeEl = document.getElementById("inspector-severity-badge");
  const detailsEl = document.getElementById("inspector-node-details");

  if (typeEl) typeEl.textContent = (node.type || "ENTITY").toUpperCase();
  if (idEl) idEl.textContent = node.id;

  // Check alert match
  const alertMatch = alertsData.find((a) => a.entity_id === node.id || a.entity_id === `wallet:${node.id}`);
  if (badgeEl) {
    const sev = alertMatch ? alertMatch.severity : "LOW";
    badgeEl.textContent = sev;
    badgeEl.className = `severity-tag severity-${sev.toLowerCase()}`;
  }

  detailsEl.innerHTML = `<div style="text-align:center; padding:1rem; color:var(--text-muted); font-size:0.8rem;">Querying entity ledger...</div>`;

  try {
    const data = await apiFetch(`/cases/${currentCaseId}/entities/${encodeURIComponent(node.id)}`);
    renderInspectorDetails(node, data, alertMatch);
  } catch (err) {
    detailsEl.innerHTML = `
      <div class="case-info-row"><span class="key">Type</span><span class="val">${node.type}</span></div>
      <div class="case-info-row"><span class="key">ID</span><span class="val">${node.id}</span></div>
      <div class="case-info-row"><span class="key">Connected Peers</span><span class="val">${adjacencyMap.get(node.id)?.neighbors.size || 0}</span></div>
    `;
  }
}

function renderInspectorDetails(node, data, alertMatch) {
  const detailsEl = document.getElementById("inspector-node-details");
  if (!detailsEl) return;

  const adj = adjacencyMap.get(node.id);
  const peerCount = adj ? adj.neighbors.size : 0;

  let html = "";

  // 1. Alert Lead Section if present
  if (alertMatch) {
    const reasonsList = alertMatch.top_reasons || alertMatch.reasons || [];
    const reasons = (Array.isArray(reasonsList) && reasonsList.length > 0)
      ? reasonsList.join(" • ")
      : (typeof alertMatch.reasons === "string" ? alertMatch.reasons : (alertMatch.ollama_summary || "High Risk Behavioral Signal"));
    html += `
      <div class="inspector-section" style="border-top:none; margin-top:0; padding-top:0;">
        <div class="inspector-section-title" style="color:var(--accent-orange);">⚠️ Flagged Forensic Lead</div>
        <div class="inspector-card" style="border-color: rgba(249,115,22,0.4); margin-bottom: 0.75rem;">
          <div style="font-size: 0.8rem; font-weight: 700; color: #fff;">Priority Score: <span style="color:var(--accent-red);">${alertMatch.priority_score.toFixed(1)}/100</span></div>
          <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">${reasons}</div>
          <button class="btn btn-outline btn-sm" style="width: 100%; margin-top: 0.5rem; font-size: 0.72rem;" onclick="jumpToAlertEvidence('${alertMatch.alert_id}')">View Evidence Pack →</button>
        </div>
      </div>
    `;
  }

  // 2. Entity-specific intelligence
  if (node.type === "wallet" || data.type === "wallet") {
    const f = data.features || {};
    html += `
      <div class="inspector-section">
        <div class="inspector-section-title">Wallet Financial Flow</div>
        <div class="inspector-grid">
          <div class="inspector-card">
            <div class="kpi-label">Balance</div>
            <div class="kpi-val text-green">${(f.balance || 0).toFixed(4)} BTC</div>
          </div>
          <div class="inspector-card">
            <div class="kpi-label">Transactions</div>
            <div class="kpi-val">${f.transaction_count || peerCount}</div>
          </div>
          <div class="inspector-card">
            <div class="kpi-label">Total Received</div>
            <div class="kpi-val text-blue">${(f.total_incoming || 0).toFixed(4)} BTC</div>
          </div>
          <div class="inspector-card">
            <div class="kpi-label">Total Sent</div>
            <div class="kpi-val text-high">${(f.total_outgoing || 0).toFixed(4)} BTC</div>
          </div>
        </div>
      </div>

      <div class="inspector-section">
        <div class="inspector-section-title">Forensic Topology</div>
        <div class="case-info-row"><span class="key">Counterparties</span><span class="val">${f.unique_counterparties || peerCount}</span></div>
        <div class="case-info-row"><span class="key">Fan-Out Ratio</span><span class="val">${f.fan_out || 0}</span></div>
        <div class="case-info-row"><span class="key">Associated IPs</span><span class="val">${f.connected_ip_count || 0}</span></div>
      </div>
    `;
  } else if (node.type === "transaction" || data.type === "transaction") {
    const fee = data.fee ? `${data.fee.toFixed(6)} BTC` : "0.0001 BTC";
    html += `
      <div class="inspector-section">
        <div class="inspector-section-title">Transaction Ledger Data</div>
        <div class="inspector-grid">
          <div class="inspector-card">
            <div class="kpi-label">Total Input</div>
            <div class="kpi-val text-blue">${(data.total_input || 0).toFixed(4)} BTC</div>
          </div>
          <div class="inspector-card">
            <div class="kpi-label">Total Output</div>
            <div class="kpi-val text-gold">${(data.total_output || 0).toFixed(4)} BTC</div>
          </div>
        </div>
        <div class="case-info-row"><span class="key">Mining Fee</span><span class="val">${fee}</span></div>
        <div class="case-info-row"><span class="key">Script Type</span><span class="val">${data.script_type || 'P2WPKH'}</span></div>
        <div class="case-info-row"><span class="key">Timestamp</span><span class="val" style="font-size:0.72rem;">${data.timestamp || 'Recorded'}</span></div>
      </div>

      ${data.relayed_by_ips && data.relayed_by_ips.length > 0 ? `
        <div class="inspector-section">
          <div class="inspector-section-title">Relayed By Peer IPs</div>
          <div style="font-size:0.75rem; font-family:var(--font-mono); color:var(--text-secondary);">
            ${data.relayed_by_ips.map(ip => `<div>🌐 ${ip.ip} (${ip.country || 'N/A'}, ${ip.asn || 'AS'})</div>`).join("")}
          </div>
        </div>
      ` : ''}
    `;
  } else if (node.type === "ip" || data.type === "ip") {
    html += `
      <div class="inspector-section">
        <div class="inspector-section-title">Network Peer Intelligence</div>
        <div class="case-info-row"><span class="key">Country</span><span class="val">${data.country || 'CH'}</span></div>
        <div class="case-info-row"><span class="key">Autonomous System</span><span class="val">${data.asn || 'AS13335'}</span></div>
        <div class="case-info-row"><span class="key">Relayed Transactions</span><span class="val">${data.relayed_tx_count || peerCount}</span></div>
      </div>
    `;
  }

  // 3. Counterparty Nodes in Graph
  if (adj && adj.neighbors.size > 0) {
    const neighborList = Array.from(adj.neighbors).slice(0, 8);
    html += `
      <div class="inspector-section">
        <div class="inspector-section-title">Direct Connected Entities (${adj.neighbors.size})</div>
        <div style="display:flex; flex-direction:column; gap:0.25rem;">
          ${neighborList.map(nid => {
            const shortNid = nid.length > 20 ? `${nid.slice(0, 10)}...${nid.slice(-6)}` : nid;
            return `
              <div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-card); padding:0.25rem 0.5rem; border-radius:var(--radius-sm); font-size:0.72rem; font-family:var(--font-mono);">
                <span>${shortNid}</span>
                <button class="btn btn-outline btn-sm" style="padding:0.1rem 0.35rem; font-size:0.65rem;" onclick="focusNodeById('${nid}')">View</button>
              </div>
            `;
          }).join("")}
        </div>
      </div>
    `;
  }

  detailsEl.innerHTML = html;
}

function focusNodeById(nodeId) {
  const pos = nodePositions.get(nodeId);
  if (pos) {
    panToNode(pos);
    selectNode(pos.node);
  }
}

function focusSelectedNode() {
  if (selectedNodeId) {
    const pos = nodePositions.get(selectedNodeId);
    if (pos) panToNode(pos);
  }
}

async function isolateSelectedEgo() {
  if (!selectedNodeId || !currentCaseId) return;
  try {
    const res = await apiFetch(`/cases/${currentCaseId}/graph/neighborhood/${encodeURIComponent(selectedNodeId)}?hops=1`);
    if (res.nodes && res.nodes.length > 0) {
      processGraphData(res.nodes, res.edges || []);
      alert(`Loaded 1-hop ego network (${res.nodes.length} entities) for ${selectedNodeId}`);
    }
  } catch (err) {
    console.error("Could not load neighborhood:", err);
  }
}

function copyInspectorId() {
  const idEl = document.getElementById("inspector-node-id");
  if (!idEl) return;
  navigator.clipboard.writeText(idEl.textContent).then(() => {
    const btn = document.getElementById("btn-inspector-copy");
    if (btn) {
      btn.textContent = "✓ Copied";
      setTimeout(() => (btn.textContent = "Copy"), 2000);
    }
  });
}

function jumpToAlertEvidence(alertId) {
  const alertsTabBtn = document.querySelector('.tab-btn[data-tab="alerts-view"]');
  if (alertsTabBtn) {
    alertsTabBtn.click();
    selectAlert(alertId);
  }
}

function inspectEntity(entityId) {
  const graphTabBtn = document.querySelector('.tab-btn[data-tab="graph-view"]');
  if (graphTabBtn) {
    graphTabBtn.click();
    resizeCanvas();
    setTimeout(() => {
      // Find matching node
      let foundPos = null;
      for (const [id, pos] of nodePositions.entries()) {
        if (id === entityId || id === `wallet:${entityId}` || id.endsWith(entityId)) {
          foundPos = pos;
          break;
        }
      }
      if (foundPos) {
        panToNode(foundPos);
        selectNode(foundPos.node);
      } else {
        searchGraphNodes(entityId);
      }
    }, 250);
  }
}

// -------------------------------------------------------------
// Case Report Viewer & Forensic Markdown Parser
// -------------------------------------------------------------
async function loadCaseReport(caseId, runId = null) {
  const reportContainer = document.getElementById("report-markdown-content");
  if (!reportContainer) return;
  reportContainer.innerHTML = `<div style="text-align:center; padding:3rem; color:var(--text-secondary);"><span class="text-blue">●</span> Loading forensic intelligence report...</div>`;

  try {
    const url = runId
      ? `/cases/${caseId}/report?format=markdown&run_id=${encodeURIComponent(runId)}`
      : `/cases/${caseId}/report?format=markdown`;
    const res = await apiFetch(url);

    // Populate available runs dropdown
    const runSelect = document.getElementById("report-run-select");
    if (runSelect && res.available_runs && res.available_runs.length > 0) {
      const activeRun = res.run_id || res.available_runs[0];
      runSelect.innerHTML = res.available_runs
        .map((r) => `<option value="${r}" ${r === activeRun ? 'selected' : ''}>Run ${r.slice(0, 8)}...</option>`)
        .join("");
    }

    if (res.report_content) {
      rawReportMarkdown = res.report_content;
      reportContainer.innerHTML = renderMarkdown(res.report_content);
    } else {
      reportContainer.innerHTML = `<pre>${JSON.stringify(res, null, 2)}</pre>`;
    }
  } catch (err) {
    reportContainer.innerHTML = `
      <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: var(--radius-md); padding: 1.5rem; text-align: center;">
        <div style="font-weight: 700; color: var(--accent-red); margin-bottom: 0.5rem;">⚠️ Report Not Generated Yet</div>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1rem;">
          No completed analysis run was found for this case. Execute the analysis pipeline to generate the full forensic report.
        </p>
        <button class="btn btn-primary btn-sm" onclick="triggerAnalysisRun('${caseId}')">🚀 Execute Analysis Pipeline Now</button>
      </div>
    `;
  }
}

// Sleek deterministic markdown-to-HTML parser for tables, headings, and code
function renderMarkdown(md) {
  if (!md) return "";

  const lines = md.split("\n");
  let html = "";
  let inTable = false;
  let inCode = false;
  let codeBuffer = [];
  let tableHeaderParsed = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Code blocks
    if (line.startsWith("```")) {
      if (inCode) {
        html += `<pre><code>${escapeHtml(codeBuffer.join("\n"))}</code></pre>`;
        codeBuffer = [];
        inCode = false;
      } else {
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      codeBuffer.push(line);
      continue;
    }

    // Tables
    if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
      const cells = line.split("|").slice(1, -1).map((c) => c.trim());
      // Check if it's separator row
      if (cells.every((c) => /^:?-+:?$/.test(c))) {
        continue;
      }
      if (!inTable) {
        inTable = true;
        tableHeaderParsed = false;
        html += `<table>`;
      }
      if (!tableHeaderParsed) {
        html += `<thead><tr>${cells.map((c) => `<th>${formatInline(c)}</th>`).join("")}</tr></thead><tbody>`;
        tableHeaderParsed = true;
      } else {
        html += `<tr>${cells.map((c) => `<td>${formatInline(c)}</td>`).join("")}</tr>`;
      }
      continue;
    } else {
      if (inTable) {
        html += `</tbody></table>`;
        inTable = false;
      }
    }

    // Headings
    if (line.startsWith("### ")) {
      html += `<h3>${formatInline(line.slice(4))}</h3>`;
    } else if (line.startsWith("## ")) {
      html += `<h2>${formatInline(line.slice(3))}</h2>`;
    } else if (line.startsWith("# ")) {
      html += `<h1>${formatInline(line.slice(2))}</h1>`;
    } else if (line.trim().startsWith("- ")) {
      html += `<ul><li>${formatInline(line.trim().slice(2))}</li></ul>`;
    } else if (line.trim() === "---") {
      html += `<hr>`;
    } else if (line.trim().length > 0) {
      html += `<p>${formatInline(line)}</p>`;
    }
  }

  if (inTable) html += `</tbody></table>`;
  if (inCode) html += `<pre><code>${escapeHtml(codeBuffer.join("\n"))}</code></pre>`;

  return html;
}

function formatInline(str) {
  if (!str) return "";
  return str
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.*?)`/g, "<code>$1</code>");
}

function escapeHtml(text) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}

function downloadReportMarkdown() {
  if (!rawReportMarkdown) {
    alert("No report loaded to download.");
    return;
  }
  const blob = new Blob([rawReportMarkdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `forensic_investigation_report_${currentCaseId || 'case'}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

async function downloadReportJson() {
  if (!currentCaseId) return;
  try {
    const res = await apiFetch(`/cases/${currentCaseId}/report?format=json`);
    const blob = new Blob([JSON.stringify(res, null, 2)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `forensic_investigation_report_${currentCaseId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert("Could not download JSON report: " + err.message);
  }
}

function copyReportText() {
  if (!rawReportMarkdown) {
    alert("No report loaded to copy.");
    return;
  }
  navigator.clipboard.writeText(rawReportMarkdown).then(() => {
    const btn = document.getElementById("btn-copy-report");
    if (btn) {
      btn.textContent = "✓ Report Copied!";
      setTimeout(() => (btn.textContent = "📋 Copy Report"), 2500);
    }
  });
}

