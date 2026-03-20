const state = {
  studio: null,
  pipeline: null,
  pipelineCatalog: [],
  selectedBlockId: null,
  runs: [],
  activeRun: null,
  activeRunProgress: null,
  activeTab: "tabMonitor",
  comparison: null,
  settingsPayload: null,
  uiLogs: [],
  requestSeq: 0,
  pollTimer: null,
};

const LOCAL_SETTINGS_KEY = "director_studio_provider_settings_v3";
const UI_LOG_STORAGE_KEY = "director_studio_ui_activity_log_v2";
const UI_LOG_LIMIT = 500;
const FALLBACK_PIPELINE_DEFAULT_MODELS = {
  GEMINI: "gemini-2.5-flash",
  OPENAI: "gpt-4o-mini",
};

const els = {
  // Sidebar (Library & Settings)
  pipelineNameInput: document.getElementById("pipelineNameInput"),
  pipelineDescriptionInput: document.getElementById("pipelineDescriptionInput"),
  pipelineLibrarySelect: document.getElementById("pipelineLibrarySelect"),
  loadPipelineBtn: document.getElementById("loadPipelineBtn"),
  saveNamedPipelineBtn: document.getElementById("saveNamedPipelineBtn"),
  pipelineGeminiModelInput: document.getElementById("pipelineGeminiModelInput"),
  pipelineOpenaiModelInput: document.getElementById("pipelineOpenaiModelInput"),
  pipelineCanvas: document.getElementById("pipelineCanvas"),
  templateRail: document.getElementById("templateRail"),
  savePipelineBtn: document.getElementById("savePipelineBtn"),

  // Topbar
  refreshStudioBtn: document.getElementById("refreshStudioBtn"),
  snapshotPipelineBtn: document.getElementById("snapshotPipelineBtn"),
  resetPipelineBtn: document.getElementById("resetPipelineBtn"),
  openSettingsBtn: document.getElementById("openSettingsBtn"),
  runPipelineBtn: document.getElementById("runPipelineBtn"),
  tabCompareBtn: document.getElementById("tabCompareBtn"),

  // Center (Command Center)
  activeRunBanner: document.getElementById("activeRunBanner"),
  runStatusLabel: document.getElementById("runStatusLabel"),
  runProgressText: document.getElementById("runProgressText"),
  runProgressFill: document.getElementById("runProgressFill"),
  inspectorEmpty: document.getElementById("inspectorEmpty"),
  blockInspector: document.getElementById("blockInspector"),
  currentBlockTitle: document.getElementById("currentBlockTitle"),
  blockIdBadge: document.getElementById("blockIdBadge"),
  blockStatusDot: document.getElementById("blockStatusDot"),
  
  blockIdInput: document.getElementById("blockIdInput"),
  blockNameInput: document.getElementById("blockNameInput"),
  blockTypeInput: document.getElementById("blockTypeInput"),
  blockEnabledInput: document.getElementById("blockEnabledInput"),
  blockProviderInput: document.getElementById("blockProviderInput"),
  blockModelSourceInput: document.getElementById("blockModelSourceInput"),
  blockModelInput: document.getElementById("blockModelInput"),
  blockModelHint: document.getElementById("blockModelHint"),
  blockTempInput: document.getElementById("blockTempInput"),
  blockSchemaInput: document.getElementById("blockSchemaInput"),
  blockSystemInstructionInput: document.getElementById("blockSystemInstructionInput"),
  blockPromptTemplateInput: document.getElementById("blockPromptTemplateInput"),
  dependencyCheckboxes: document.getElementById("dependencyCheckboxes"),
  
  moveBlockLeftBtn: document.getElementById("moveBlockLeftBtn"),
  moveBlockRightBtn: document.getElementById("moveBlockRightBtn"),
  duplicateBlockBtn: document.getElementById("duplicateBlockBtn"),
  deleteBlockBtn: document.getElementById("deleteBlockBtn"),

  // Right (Monitor)
  tabMonitorBtn: document.getElementById("tabMonitorBtn"),
  tabTimelineBtn: document.getElementById("tabTimelineBtn"),
  tabHistoryBtn: document.getElementById("tabHistoryBtn"),
  tabLogsBtn: document.getElementById("tabLogsBtn"),
  
  tabMonitor: document.getElementById("tabMonitor"),
  tabTimeline: document.getElementById("tabTimeline"),
  tabHistory: document.getElementById("tabHistory"),
  tabLogs: document.getElementById("tabLogs"),
  
  qualityScoreLabel: document.getElementById("qualityScoreLabel"),
  wordCountLabel: document.getElementById("wordCountLabel"),
  artifactFeed: document.getElementById("artifactFeed"),
  storyTimeline: document.getElementById("storyTimeline"),
  runsList: document.getElementById("runsList"),
  
  uiLogPanel: document.getElementById("uiLogPanel"),
  copyUiLogBtn: document.getElementById("copyUiLogBtn"),
  clearUiLogBtn: document.getElementById("clearUiLogBtn"),

  // Compare Overlay
  compareOverlay: document.getElementById("compareOverlay"),
  closeCompareBtn: document.getElementById("closeCompareBtn"),
  baselineRunSelect: document.getElementById("baselineRunSelect"),
  candidateRunSelect: document.getElementById("candidateRunSelect"),
  compareRunsBtn: document.getElementById("compareRunsBtn"),
  compareResult: document.getElementById("compareResult"),

  // Settings & Toast
  settingsDialog: document.getElementById("settingsDialog"),
  geminiKeyInput: document.getElementById("geminiKeyInput"),
  openaiKeyInput: document.getElementById("openaiKeyInput"),
  googleCredPathInput: document.getElementById("googleCredPathInput"),
  settingsStatusBadges: document.getElementById("settingsStatusBadges"),
  freshStartBtn: document.getElementById("freshStartBtn"),
  cancelSettingsBtn: document.getElementById("cancelSettingsBtn"),
  saveSettingsBtn: document.getElementById("saveSettingsBtn"),
  providerModelList: document.getElementById("providerModelList"),
  toast: document.getElementById("toast"),
};

/* --- Utilities & Storage --- */

function showToast(message, isError = false) {
  els.toast.textContent = message;
  els.toast.classList.remove("hidden");
  els.toast.style.borderColor = isError ? "var(--danger)" : "var(--mint)";
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => els.toast.classList.add("hidden"), 3000);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[m]));
}

function deepClone(v) { return JSON.parse(JSON.stringify(v)); }

function uid(prefix) { return `${prefix}_${Math.random().toString(36).slice(2, 7)}`; }

function getLocalSettings() {
  try {
    const raw = window.localStorage.getItem(LOCAL_SETTINGS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (e) { return {}; }
}

function setLocalSettings(settings) {
  try { window.localStorage.setItem(LOCAL_SETTINGS_KEY, JSON.stringify(settings)); } catch (e) {}
}

function getStoredUiLogs() {
  try {
    const raw = window.localStorage.getItem(UI_LOG_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (e) { return []; }
}

function setStoredUiLogs(logs) {
  try { window.localStorage.setItem(UI_LOG_STORAGE_KEY, JSON.stringify(logs.slice(-UI_LOG_LIMIT))); } catch (e) {}
}

function uiLog(level, message, meta = null) {
  const timestamp = new Date().toISOString();
  const normalized = (level || "info").toLowerCase();
  let details = meta ? ` ${typeof meta === 'string' ? meta : JSON.stringify(meta)}` : "";
  const line = `[${timestamp}] [${normalized.toUpperCase()}] ${message}${details}`;
  
  state.uiLogs.push({ level: normalized, text: line });
  if (state.uiLogs.length > UI_LOG_LIMIT) state.uiLogs.splice(0, state.uiLogs.length - UI_LOG_LIMIT);
  setStoredUiLogs(state.uiLogs);
  renderUiLogs();
}

function renderUiLogs() {
  if (!els.uiLogPanel) return;
  if (!state.uiLogs.length) {
    els.uiLogPanel.innerHTML = '<div class="ui-log-entry info">No UI activity logged yet.</div>';
    return;
  }
  els.uiLogPanel.innerHTML = state.uiLogs.map(e => `<div class="ui-log-entry ${e.level}">${escapeHtml(e.text)}</div>`).join("");
  els.uiLogPanel.scrollTop = els.uiLogPanel.scrollHeight;
}

async function request(path, options = {}) {
  const method = options.method || "GET";
  const reqId = ++state.requestSeq;
  uiLog("debug", `HTTP request #${reqId} ${method} ${path}`);
  const started = performance.now();
  
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  let data = {};
  if (text) { try { data = JSON.parse(text); } catch { data = { detail: text }; } }
  
  if (!response.ok) {
    uiLog("error", `HTTP failure #${reqId} ${method} ${path}`, { status: response.status, detail: data.detail });
    throw new Error(data.detail || text || `Request failed: ${response.status}`);
  }
  
  uiLog("debug", `HTTP success #${reqId} ${method} ${path}`, { status: response.status, elapsed_ms: Math.round(performance.now() - started) });
  return data;
}

/* --- Core Pipeline Logic --- */

function ensurePipelineDefaults(pipeline) {
  if (!pipeline) return pipeline;
  if (!pipeline.default_models) pipeline.default_models = {};
  Object.entries(FALLBACK_PIPELINE_DEFAULT_MODELS).forEach(([provider, model]) => {
    if (!pipeline.default_models[provider]) pipeline.default_models[provider] = model;
  });
  (pipeline.blocks || []).forEach(block => {
    if (!block.config) block.config = {};
    if (typeof block.config.use_pipeline_default_model !== "boolean") block.config.use_pipeline_default_model = false;
    if (block.config.use_pipeline_default_model) {
      block.config.model_name = pipeline.default_models[block.config.provider] || block.config.model_name || null;
    } else if (block.config.model_name === undefined) {
      block.config.model_name = null;
    }
  });
  return pipeline;
}

function getPipelineDefaultModel(provider) {
  return state.pipeline?.default_models?.[provider] || state.studio?.pipeline?.default_models?.[provider] || FALLBACK_PIPELINE_DEFAULT_MODELS[provider] || "";
}

function getEffectiveModelForBlock(block) {
  if (!block) return "";
  return block.config.use_pipeline_default_model ? getPipelineDefaultModel(block.config.provider) : (block.config.model_name || getPipelineDefaultModel(block.config.provider));
}

function getSelectedBlock() {
  return state.pipeline?.blocks.find(b => b.id === state.selectedBlockId) || null;
}

function selectBlock(blockId) {
  uiLog("info", `Selecting block ${blockId}`);
  state.selectedBlockId = blockId;
  renderPipelineCanvas();
  renderInspector();
}

function moveSelectedBlock(offset) {
  const selected = getSelectedBlock();
  if (!selected) return;
  const index = state.pipeline.blocks.findIndex(b => b.id === selected.id);
  const target = index + offset;
  if (target < 0 || target >= state.pipeline.blocks.length) return;
  const temp = state.pipeline.blocks[index];
  state.pipeline.blocks[index] = state.pipeline.blocks[target];
  state.pipeline.blocks[target] = temp;
  uiLog("info", "Block moved", { block_id: selected.id, from: index, to: target });
  renderPipelineCanvas();
}

/* --- Render Functions --- */

function renderPipelineMeta() {
  if (!state.pipeline) return;
  els.pipelineNameInput.value = state.pipeline.name || "";
  els.pipelineDescriptionInput.value = state.pipeline.description || "";
  
  const gOpts = state.studio?.provider_models?.GEMINI || [];
  const oOpts = state.studio?.provider_models?.OPENAI || [];
  const selG = getPipelineDefaultModel("GEMINI");
  const selO = getPipelineDefaultModel("OPENAI");
  
  els.pipelineGeminiModelInput.innerHTML = (!gOpts.includes(selG) && selG ? [selG, ...gOpts] : gOpts).map(m => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join("");
  els.pipelineOpenaiModelInput.innerHTML = (!oOpts.includes(selO) && selO ? [selO, ...oOpts] : oOpts).map(m => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join("");
  els.pipelineGeminiModelInput.value = selG;
  els.pipelineOpenaiModelInput.value = selO;
}

function renderPipelineLibrary() {
  if (!state.pipelineCatalog?.length) {
    els.pipelineLibrarySelect.innerHTML = `<option value="">No saved pipelines yet</option>`;
    return;
  }
  els.pipelineLibrarySelect.innerHTML = state.pipelineCatalog.map(i => `<option value="${escapeHtml(i.key)}">${escapeHtml(i.name)} (${i.block_count} blocks)</option>`).join("");
}

function renderPipelineCanvas() {
  const blocks = state.pipeline?.blocks || [];
  els.pipelineCanvas.innerHTML = "";
  
  blocks.forEach((block, idx) => {
    const trace = state.activeRunProgress?.block_traces?.[block.id];
    const statusClass = trace?.status?.toLowerCase() || (block.enabled ? "pending" : "skipped");
    const item = document.createElement("div");
    
    item.className = `block-nav-item ${block.id === state.selectedBlockId ? "active" : ""} ${statusClass} ${!block.enabled ? "dim" : ""}`;
    item.innerHTML = `
      <div class="status-dot"></div>
      <div style="flex: 1;">
        <div style="font-weight: 500; font-size: 0.9rem; display: flex; justify-content: space-between;">
          ${escapeHtml(block.name)}
          <span style="font-size: 0.7rem;" class="chip">${escapeHtml(block.type)}</span>
        </div>
        <div style="font-size: 0.75rem;" class="dim">${escapeHtml(block.id)}</div>
      </div>
      <div style="font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,0.05);">
        ${escapeHtml(block.config.provider)}
      </div>
    `;
    item.addEventListener("click", () => selectBlock(block.id));
    els.pipelineCanvas.appendChild(item);
    
    if (idx < blocks.length - 1) {
      const arr = document.createElement("div");
      arr.className = "block-arrow";
      arr.textContent = "↓";
      els.pipelineCanvas.appendChild(arr);
    }
  });
}

function createBlockFromTemplate(t) {
  const baseId = t.type.replaceAll("-", "_");
  const existing = new Set(state.pipeline.blocks.map(b => b.id));
  let candidate = baseId, idx = 1;
  while(existing.has(candidate)) { idx++; candidate = `${baseId}_${idx}`; }
  const block = { id: candidate, name: t.name, description: t.description || "", type: t.type, enabled: true, input_blocks: [], config: deepClone(t.config) };
  if(typeof block.config.use_pipeline_default_model !== "boolean") block.config.use_pipeline_default_model = false;
  if(block.config.model_name === undefined) block.config.model_name = null;
  return block;
}

function renderTemplateRail() {
  els.templateRail.innerHTML = "";
  (state.studio?.block_templates || []).forEach(t => {
    const item = document.createElement("div");
    item.className = "template-item";
    item.innerHTML = `<span class="chip">${escapeHtml(t.type)}</span><span style="font-size: 0.7rem; color: var(--text-dim); flex: 1; margin: 0 8px;">${escapeHtml(t.name)}</span><button class="btn" style="padding: 2px 6px; font-size: 0.7rem;">+ Add</button>`;
    item.querySelector("button").addEventListener("click", () => {
      const nb = createBlockFromTemplate(t);
      const sidx = state.pipeline.blocks.findIndex(b => b.id === state.selectedBlockId);
      state.pipeline.blocks.splice(sidx >= 0 ? sidx + 1 : state.pipeline.blocks.length, 0, nb);
      state.selectedBlockId = nb.id;
      uiLog("info", "Block added from template", { id: nb.id, type: nb.type });
      renderPipelineCanvas();
      renderInspector();
    });
    els.templateRail.appendChild(item);
  });
}

function refreshModelList(provider, selected = "") {
  const opts = state.studio?.provider_models?.[provider] || [];
  els.providerModelList.innerHTML = (!opts.includes(selected) && selected ? [selected, ...opts] : opts).map(m => `<option value="${escapeHtml(m)}"></option>`).join("");
}

function renderInspector() {
  const selected = getSelectedBlock();
  if (!selected) {
    els.inspectorEmpty.classList.remove("hidden");
    els.blockInspector.classList.add("hidden");
    return;
  }
  els.inspectorEmpty.classList.add("hidden");
  els.blockInspector.classList.remove("hidden");

  els.currentBlockTitle.textContent = selected.name;
  els.blockIdBadge.textContent = selected.id;
  
  const trace = state.activeRunProgress?.block_traces?.[selected.id];
  els.blockStatusDot.className = `status-dot ${trace?.status?.toLowerCase() || (selected.enabled ? "pending" : "skipped")}`;

  els.blockIdInput.value = selected.id;
  els.blockNameInput.value = selected.name;
  els.blockTypeInput.value = selected.type;
  els.blockEnabledInput.value = String(selected.enabled);
  els.blockProviderInput.value = selected.config.provider;
  refreshModelList(selected.config.provider, selected.config.model_name || "");
  els.blockModelSourceInput.value = selected.config.use_pipeline_default_model ? "default" : "custom";
  els.blockModelInput.value = selected.config.use_pipeline_default_model ? getEffectiveModelForBlock(selected) : (selected.config.model_name || "");
  els.blockModelInput.disabled = selected.config.use_pipeline_default_model;
  els.blockTempInput.value = selected.config.temperature;
  els.blockSystemInstructionInput.value = selected.config.system_instruction;
  els.blockPromptTemplateInput.value = selected.config.prompt_template;

  const pdm = getPipelineDefaultModel(selected.config.provider);
  const em = getEffectiveModelForBlock(selected);
  els.blockModelHint.textContent = selected.config.use_pipeline_default_model ? `Inheriting pipeline default: ${em || pdm || "not set"}` : `Override active. (Pipeline default is ${pdm || "not set"})`;

  const schemas = state.studio?.schemas || [];
  els.blockSchemaInput.innerHTML = `<option value="">None</option>${schemas.map(s => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`).join("")}`;
  els.blockSchemaInput.value = selected.config.response_schema_name || "";

  els.dependencyCheckboxes.innerHTML = "";
  state.pipeline.blocks.filter(c => c.id !== selected.id).forEach(c => {
    const w = document.createElement("div");
    w.className = "dependency-item";
    w.innerHTML = `<input type="checkbox" data-id="${escapeHtml(c.id)}" ${selected.input_blocks.includes(c.id) ? "checked" : ""}/> ${escapeHtml(c.name)}`;
    els.dependencyCheckboxes.appendChild(w);
  });
}

function bindInspectorEvents() {
  function renameId(oldId, newId) {
    if(!newId || oldId===newId) return true;
    if(state.pipeline.blocks.some(b => b.id === newId)) { showToast("ID exists", true); return false; }
    state.pipeline.blocks.forEach(b => b.input_blocks = b.input_blocks.map(v => v === oldId ? newId : v));
    state.selectedBlockId = newId;
    return true;
  }
  
  els.blockIdInput.addEventListener("change", e => {
    const b = getSelectedBlock();
    if(b && renameId(b.id, e.target.value.trim())) { uiLog("info", "ID changed", {to: b.id}); renderPipelineCanvas(); renderInspector(); }
    else if(b) e.target.value = b.id;
  });
  
  els.blockNameInput.addEventListener("input", e => { const b = getSelectedBlock(); if(b) { b.name = e.target.value; renderPipelineCanvas(); }});
  els.blockEnabledInput.addEventListener("change", e => { const b = getSelectedBlock(); if(b) { b.enabled = e.target.value === "true"; renderPipelineCanvas(); renderInspector(); }});
  
  els.blockProviderInput.addEventListener("change", e => {
    const b = getSelectedBlock();
    if(b) {
      b.config.provider = e.target.value;
      refreshModelList(b.config.provider);
      b.config.model_name = getPipelineDefaultModel(b.config.provider);
      renderPipelineCanvas(); renderInspector();
    }
  });
  
  els.blockModelSourceInput.addEventListener("change", e => {
    const b = getSelectedBlock();
    if(b) { b.config.use_pipeline_default_model = e.target.value === "default"; renderInspector(); }
  });
  
  els.blockModelInput.addEventListener("input", e => { const b = getSelectedBlock(); if(b) { b.config.model_name = e.target.value; }});
  els.blockTempInput.addEventListener("change", e => { const b = getSelectedBlock(); if(b) { b.config.temperature = Number(e.target.value); }});
  els.blockSchemaInput.addEventListener("change", e => { const b = getSelectedBlock(); if(b) { b.config.response_schema_name = e.target.value || null; b.config.response_mime_type = b.config.response_schema_name ? "application/json" : null; }});
  
  els.blockSystemInstructionInput.addEventListener("input", e => { const b = getSelectedBlock(); if(b) b.config.system_instruction = e.target.value; });
  els.blockPromptTemplateInput.addEventListener("input", e => { const b = getSelectedBlock(); if(b) b.config.prompt_template = e.target.value; });
  
  els.dependencyCheckboxes.addEventListener("change", () => {
    const b = getSelectedBlock();
    if(b) { b.input_blocks = Array.from(els.dependencyCheckboxes.querySelectorAll("input:checked")).map(i => i.dataset.id); renderPipelineCanvas(); }
  });

  els.moveBlockLeftBtn.addEventListener("click", () => moveSelectedBlock(-1));
  els.moveBlockRightBtn.addEventListener("click", () => moveSelectedBlock(1));
  
  els.duplicateBlockBtn.addEventListener("click", () => {
    const b = getSelectedBlock();
    if(!b) return;
    const d = deepClone(b);
    d.id = uid(`${b.id}_copy`); d.name = `${b.name} Copy`;
    state.pipeline.blocks.splice(state.pipeline.blocks.findIndex(x => x.id === b.id)+1, 0, d);
    state.selectedBlockId = d.id;
    uiLog("info", "Block duplicated");
    renderPipelineCanvas(); renderInspector();
  });
  
  els.deleteBlockBtn.addEventListener("click", () => {
    const b = getSelectedBlock();
    if(!b || state.pipeline.blocks.length <= 1) return;
    state.pipeline.blocks = state.pipeline.blocks.filter(x => x.id !== b.id);
    state.pipeline.blocks.forEach(x => x.input_blocks = x.input_blocks.filter(id => id !== b.id));
    state.selectedBlockId = state.pipeline.blocks[0].id;
    uiLog("warn", "Block deleted", {id: b.id});
    renderPipelineCanvas(); renderInspector();
  });
}

/* --- Runs & Monitor Logic --- */

function renderArtifactFeed() {
  const traces = state.activeRunProgress?.block_traces || {};
  const seq = state.activeRunProgress?.block_sequence || [];
  els.artifactFeed.innerHTML = seq.map(id => {
    const t = traces[id];
    if(!t || !t.output) return "";
    return `<div class="artifact-card"><div class="artifact-header"><span style="font-weight: 600;">${escapeHtml(id)}</span><span class="dim" style="font-size: 0.7rem;">${escapeHtml(t.model_name)}</span></div><div class="artifact-body"><pre style="white-space: pre-wrap; font-size: 0.8rem;">${typeof t.output === 'string' ? escapeHtml(t.output) : escapeHtml(JSON.stringify(t.output, null, 2))}</pre></div></div>`;
  }).join("");
  els.artifactFeed.scrollTop = els.artifactFeed.scrollHeight;
}

function renderStoryTimeline() {
  const timeline = state.activeRunProgress?.timeline || [];
  if (!timeline.length) { els.storyTimeline.innerHTML = '<div class="empty">No narrative events yet.</div>'; return; }
  els.storyTimeline.innerHTML = timeline.map(e => `
    <div class="timeline-row">
      <div class="time-stamp">${escapeHtml(e.day)}<br/>${escapeHtml(e.time)}</div>
      <div class="timeline-marker"></div>
      <div class="timeline-content">
        <div style="font-weight: 600; margin-bottom: 4px;">${escapeHtml(e.title)}</div>
        <div class="dim" style="font-size: 0.75rem;">${escapeHtml(e.event_type)} (${escapeHtml(e.block_id)})</div>
      </div>
    </div>
  `).join("");
}

function renderRunsList() {
  els.runsList.innerHTML = state.runs.length ? state.runs.map(run => `
    <div class="run-card">
      <div style="font-weight: 600; font-size: 0.85rem;">${escapeHtml(run.final_title || "Untitled Run")}</div>
      <div class="dim" style="font-size: 0.7rem; margin-top: 4px;">${new Date(run.timestamp).toLocaleString()}</div>
      <div class="dim" style="font-size: 0.7rem;">Score: ${run.final_metrics?.quality_proxy_score || "-"} | Words: ${run.stats?.total_words || 0}</div>
      <button class="btn ghost" style="font-size: 0.7rem; padding: 4px; margin-top: 8px;" onclick="loadHistoricalRun('${run.run_id}')">Inspect</button>
    </div>
  `).join("") : '<div class="empty">No past runs yet.</div>';
}

window.loadHistoricalRun = async function(runId) {
  try {
    const detail = await request(`/runs/${runId}`);
    state.activeRunProgress = detail;
    switchTab("tabMonitor");
    renderPipelineCanvas(); renderInspector(); renderMonitor();
  } catch (err) { showToast(err.message, true); }
}

function renderMonitor() {
  const p = state.activeRunProgress;
  if (!p) return;
  els.qualityScoreLabel.textContent = p.final_metrics?.quality_proxy_score || "-";
  els.wordCountLabel.textContent = p.stats?.total_words || "0";
  renderArtifactFeed();
  renderStoryTimeline();
}

function switchTab(tabId) {
  state.activeTab = tabId;
  ["tabMonitor", "tabTimeline", "tabHistory", "tabLogs"].forEach(t => {
    els[t].classList.toggle("hidden", t !== tabId);
    els[t + "Btn"].classList.toggle("active", t === tabId);
  });
}

async function startRun() {
  try {
    await savePipeline();
    els.runPipelineBtn.disabled = true;
    els.activeRunBanner.classList.remove("hidden");
    els.runProgressFill.style.width = "0%"; els.runProgressText.textContent = "0%";
    
    const initial = await request("/runs/start", { method: "POST", body: JSON.stringify({ pipeline: state.pipeline, persist_pipeline: true }) });
    state.activeRunProgress = initial;
    switchTab("tabMonitor");
    
    if (state.pollTimer) clearInterval(state.pollTimer);
    state.pollTimer = setInterval(async () => {
      try {
        const p = await request(`/runs/${initial.run_id}/status`);
        state.activeRunProgress = p;
        const done = Object.values(p.block_traces || {}).filter(t => t.status === 'SUCCEEDED' || t.status === 'SKIPPED').length;
        const total = p.block_sequence.length;
        const pct = total > 0 ? Math.round((done / total) * 100) : 0;
        
        els.runProgressFill.style.width = `${pct}%`; els.runProgressText.textContent = `${pct}%`;
        els.runStatusLabel.textContent = p.status.toUpperCase();
        
        renderPipelineCanvas(); renderInspector(); renderMonitor();

        if (p.status === 'succeeded' || p.status === 'failed') {
          clearInterval(state.pollTimer); state.pollTimer = null;
          els.runPipelineBtn.disabled = false;
          showToast(p.status === 'succeeded' ? "Run Complete" : "Run Failed", p.status === 'failed');
          setTimeout(() => els.activeRunBanner.classList.add("hidden"), 3000);
          loadStudio();
        }
      } catch (e) { console.error("Poll error", e); }
    }, 1000);
  } catch (err) { showToast(err.message, true); els.runPipelineBtn.disabled = false; }
}

/* --- App Initialization & Bindings --- */

async function savePipeline() {
  state.pipeline.name = els.pipelineNameInput.value.trim() || "Untitled Pipeline";
  state.pipeline.description = els.pipelineDescriptionInput.value.trim();
  ensurePipelineDefaults(state.pipeline);
  const saved = await request("/pipeline", { method: "PUT", body: JSON.stringify(state.pipeline) });
  state.pipeline = ensurePipelineDefaults(saved);
  showToast("Pipeline Saved");
  uiLog("info", "Pipeline saved", { name: saved.name });
  renderPipelineCanvas(); renderPipelineMeta();
}

function renderSettingsDialog() {
  const p = state.settingsPayload;
  if (!p) return;
  const local = getLocalSettings();
  els.geminiKeyInput.value = p.settings?.gemini_api_key || local.gemini_api_key || "";
  els.openaiKeyInput.value = p.settings?.openai_api_key || local.openai_api_key || "";
  els.googleCredPathInput.value = p.settings?.google_application_credentials || local.google_application_credentials || "";
  
  els.settingsStatusBadges.innerHTML = [
    ["Gemini", p.status?.gemini_configured],
    ["OpenAI", p.status?.openai_configured],
    ["Google", p.status?.google_credentials_configured],
  ].map(([l, ok]) => `<span class="badge ${ok ? 'success' : 'error'}">${l}: ${ok ? 'READY' : 'MISSING'}</span>`).join("");
}

function renderComparison() {
  if (!state.comparison) { els.compareResult.innerHTML = ''; return; }
  const c = state.comparison;
  
  const metricsHtml = c.metrics.map(m => {
    const d = parseFloat(m.delta);
    return `<div class="stat-card"><div class="stat-label">${escapeHtml(m.label)}</div><div class="stat-val">${m.candidate}</div><div class="dim" style="font-size: 0.7rem;">vs ${m.baseline} (<span class="${d>0?'mint':d<0?'danger':''}">${d>0?'+':''}${m.delta}</span>)</div></div>`;
  }).join("");

  els.compareResult.innerHTML = `
    <div class="summary-stats" style="margin-bottom: 24px;">${metricsHtml}</div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div class="glass-panel" style="padding: 16px;">
        <h4 class="dim" style="margin-bottom: 12px; font-size: 0.8rem;">BASELINE: ${escapeHtml(c.baseline_run_id)}</h4>
        <pre style="white-space: pre-wrap; font-size: 0.75rem;">${typeof c.baseline_output === 'string' ? escapeHtml(c.baseline_output) : escapeHtml(JSON.stringify(c.baseline_output, null, 2))}</pre>
      </div>
      <div class="glass-panel" style="padding: 16px;">
        <h4 class="dim" style="margin-bottom: 12px; font-size: 0.8rem;">CANDIDATE: ${escapeHtml(c.candidate_run_id)}</h4>
        <pre style="white-space: pre-wrap; font-size: 0.75rem;">${typeof c.candidate_output === 'string' ? escapeHtml(c.candidate_output) : escapeHtml(JSON.stringify(c.candidate_output, null, 2))}</pre>
      </div>
    </div>
  `;
}

function bindTopLevelEvents() {
  els.refreshStudioBtn.addEventListener("click", loadStudio);
  els.savePipelineBtn.addEventListener("click", savePipeline);
  els.runPipelineBtn.addEventListener("click", startRun);
  
  els.tabMonitorBtn.addEventListener("click", () => switchTab("tabMonitor"));
  els.tabTimelineBtn.addEventListener("click", () => switchTab("tabTimeline"));
  els.tabHistoryBtn.addEventListener("click", () => switchTab("tabHistory"));
  els.tabLogsBtn.addEventListener("click", () => switchTab("tabLogs"));
  
  els.pipelineGeminiModelInput.addEventListener("change", e => { state.pipeline.default_models.GEMINI = e.target.value; savePipeline(); });
  els.pipelineOpenaiModelInput.addEventListener("change", e => { state.pipeline.default_models.OPENAI = e.target.value; savePipeline(); });
  
  els.saveNamedPipelineBtn.addEventListener("click", async () => {
    const name = window.prompt("Save pipeline as name:", state.pipeline.name);
    if (!name || !name.trim()) return;
    try {
      await request("/pipelines/save", { method: "POST", body: JSON.stringify({ name: name.trim(), pipeline: state.pipeline, set_active: true }) });
      uiLog("info", "Named pipeline saved", { name });
      showToast(`Saved: ${name}`);
      loadStudio();
    } catch (e) { showToast(e.message, true); }
  });
  
  els.loadPipelineBtn.addEventListener("click", async () => {
    const name = els.pipelineLibrarySelect.value;
    if (!name) return;
    try {
      await request("/pipelines/load", { method: "POST", body: JSON.stringify({ name, set_active: true }) });
      uiLog("info", "Loaded pipeline", { name });
      showToast(`Loaded: ${name}`);
      loadStudio();
    } catch (e) { showToast(e.message, true); }
  });
  
  els.snapshotPipelineBtn.addEventListener("click", async () => {
    try {
      await savePipeline();
      const r = await request("/pipeline/snapshot", { method: "POST", body: JSON.stringify({ pipeline: state.pipeline, label: state.pipeline.name }) });
      showToast("Snapshot created"); uiLog("info", "Snapshot created", {path: r.path});
    } catch (e) { showToast(e.message, true); }
  });
  
  els.resetPipelineBtn.addEventListener("click", async () => {
    try {
      await request("/pipeline/reset", { method: "POST", body: "{}" });
      showToast("Pipeline reset"); uiLog("info", "Pipeline reset");
      loadStudio();
    } catch (e) { showToast(e.message, true); }
  });

  els.tabCompareBtn.addEventListener("click", () => {
    els.compareOverlay.classList.remove("hidden");
    const opts = state.runs.map(r => `<option value="${r.run_id}">${r.run_id} | ${r.final_title || 'Untitled'}</option>`).join("");
    els.baselineRunSelect.innerHTML = opts; els.candidateRunSelect.innerHTML = opts;
  });
  els.closeCompareBtn.addEventListener("click", () => els.compareOverlay.classList.add("hidden"));
  els.compareRunsBtn.addEventListener("click", async () => {
    try {
      state.comparison = await request("/compare", {
        method: "POST",
        body: JSON.stringify({ baseline_run_id: els.baselineRunSelect.value, candidate_run_id: els.candidateRunSelect.value })
      });
      renderComparison(); uiLog("info", "Runs compared");
    } catch (err) { showToast(err.message, true); }
  });

  els.openSettingsBtn.addEventListener("click", () => { renderSettingsDialog(); els.settingsDialog.showModal(); });
  els.cancelSettingsBtn.addEventListener("click", () => els.settingsDialog.close());
  els.saveSettingsBtn.addEventListener("click", async () => {
    const s = { gemini_api_key: els.geminiKeyInput.value, openai_api_key: els.openaiKeyInput.value, google_application_credentials: els.googleCredPathInput.value };
    setLocalSettings(s);
    try {
      state.settingsPayload = await request("/settings", { method: "PUT", body: JSON.stringify(s) });
      els.settingsDialog.close(); showToast("Settings Saved");
    } catch (err) { showToast(err.message, true); }
  });
  
  els.freshStartBtn.addEventListener("click", async () => {
    if(!window.confirm("Fresh start? Wipes local cache + pipeline.")) return;
    try {
      window.localStorage.removeItem(LOCAL_SETTINGS_KEY); window.localStorage.removeItem(UI_LOG_STORAGE_KEY);
      state.uiLogs = [];
      await request("/pipeline/reset", { method: "POST", body: "{}" });
      els.settingsDialog.close(); showToast("Fresh start complete");
      loadStudio();
    } catch (e) { showToast(e.message, true); }
  });
  
  els.clearUiLogBtn.addEventListener("click", () => { state.uiLogs = []; setStoredUiLogs([]); renderUiLogs(); });
  els.copyUiLogBtn.addEventListener("click", () => { navigator.clipboard.writeText(state.uiLogs.map(l => l.text).join('\n')); showToast("Logs copied"); });
}

async function loadStudio() {
  try {
    const s = await request("/studio");
    state.studio = s;
    state.pipeline = ensurePipelineDefaults(deepClone(s.pipeline));
    state.pipelineCatalog = s.pipeline_catalog || [];
    state.runs = s.run_summaries || [];
    state.settingsPayload = s.settings;
    if (!state.selectedBlockId) state.selectedBlockId = state.pipeline.blocks?.[0]?.id || null;
    
    renderPipelineMeta();
    renderPipelineLibrary();
    renderPipelineCanvas();
    renderTemplateRail();
    renderInspector();
    renderRunsList();
    renderSettingsDialog();
  } catch (err) { uiLog("error", "Failed to load studio", err.message); }
}

bindInspectorEvents();
bindTopLevelEvents();
state.uiLogs = getStoredUiLogs();
renderUiLogs();
uiLog("info", "Creative Workspace v3 Bootstrapped");
loadStudio();
