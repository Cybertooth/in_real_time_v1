const state = {
  studio: null,
  pipeline: null,
  pipelineCatalog: [],
  selectedBlockId: null,
  runs: [],
  activeRun: null,
  comparison: null,
  settingsPayload: null,
  uiLogs: [],
  requestSeq: 0,
};

const LOCAL_SETTINGS_KEY = "director_studio_provider_settings_v1";
const UI_LOG_STORAGE_KEY = "director_studio_ui_activity_log_v1";
const UI_LOG_LIMIT = 500;
const FALLBACK_PIPELINE_DEFAULT_MODELS = {
  GEMINI: "gemini-2.5-flash",
  OPENAI: "gpt-5.4-mini",
};

const els = {
  pipelineCanvas: document.getElementById("pipelineCanvas"),
  templateRail: document.getElementById("templateRail"),
  pipelineNameInput: document.getElementById("pipelineNameInput"),
  pipelineDescriptionInput: document.getElementById("pipelineDescriptionInput"),
  pipelineLibrarySelect: document.getElementById("pipelineLibrarySelect"),
  pipelineGeminiModelInput: document.getElementById("pipelineGeminiModelInput"),
  pipelineOpenaiModelInput: document.getElementById("pipelineOpenaiModelInput"),
  loadPipelineBtn: document.getElementById("loadPipelineBtn"),
  saveNamedPipelineBtn: document.getElementById("saveNamedPipelineBtn"),
  savePipelineBtn: document.getElementById("savePipelineBtn"),
  snapshotPipelineBtn: document.getElementById("snapshotPipelineBtn"),
  runPipelineBtn: document.getElementById("runPipelineBtn"),
  resetPipelineBtn: document.getElementById("resetPipelineBtn"),
  refreshStudioBtn: document.getElementById("refreshStudioBtn"),
  runsList: document.getElementById("runsList"),
  runDetails: document.getElementById("runDetails"),
  baselineRunSelect: document.getElementById("baselineRunSelect"),
  candidateRunSelect: document.getElementById("candidateRunSelect"),
  compareRunsBtn: document.getElementById("compareRunsBtn"),
  compareResult: document.getElementById("compareResult"),
  runStatusLabel: document.getElementById("runStatusLabel"),
  qualityScoreLabel: document.getElementById("qualityScoreLabel"),
  toast: document.getElementById("toast"),
  inspectorEmpty: document.getElementById("inspectorEmpty"),
  blockInspector: document.getElementById("blockInspector"),
  blockIdInput: document.getElementById("blockIdInput"),
  blockNameInput: document.getElementById("blockNameInput"),
  blockTypeInput: document.getElementById("blockTypeInput"),
  blockEnabledInput: document.getElementById("blockEnabledInput"),
  blockProviderInput: document.getElementById("blockProviderInput"),
  blockModelSourceInput: document.getElementById("blockModelSourceInput"),
  blockModelInput: document.getElementById("blockModelInput"),
  blockModelHint: document.getElementById("blockModelHint"),
  providerModelList: document.getElementById("providerModelList"),
  blockTempInput: document.getElementById("blockTempInput"),
  blockSchemaInput: document.getElementById("blockSchemaInput"),
  blockSystemInstructionInput: document.getElementById("blockSystemInstructionInput"),
  blockPromptTemplateInput: document.getElementById("blockPromptTemplateInput"),
  dependencyCheckboxes: document.getElementById("dependencyCheckboxes"),
  moveBlockLeftBtn: document.getElementById("moveBlockLeftBtn"),
  moveBlockRightBtn: document.getElementById("moveBlockRightBtn"),
  duplicateBlockBtn: document.getElementById("duplicateBlockBtn"),
  deleteBlockBtn: document.getElementById("deleteBlockBtn"),
  settingsDialog: document.getElementById("settingsDialog"),
  openSettingsBtn: document.getElementById("openSettingsBtn"),
  cancelSettingsBtn: document.getElementById("cancelSettingsBtn"),
  saveSettingsBtn: document.getElementById("saveSettingsBtn"),
  freshStartBtn: document.getElementById("freshStartBtn"),
  geminiKeyInput: document.getElementById("geminiKeyInput"),
  openaiKeyInput: document.getElementById("openaiKeyInput"),
  googleCredPathInput: document.getElementById("googleCredPathInput"),
  settingsStatusBadges: document.getElementById("settingsStatusBadges"),
  clearUiLogBtn: document.getElementById("clearUiLogBtn"),
  copyUiLogBtn: document.getElementById("copyUiLogBtn"),
  uiLogPanel: document.getElementById("uiLogPanel"),
};

function getLocalSettings() {
  try {
    const raw = window.localStorage.getItem(LOCAL_SETTINGS_KEY);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return {};
    }
    return parsed;
  } catch (_error) {
    return {};
  }
}

function setLocalSettings(settings) {
  try {
    window.localStorage.setItem(LOCAL_SETTINGS_KEY, JSON.stringify(settings));
  } catch (_error) {
    // Ignore storage failures (private mode / browser policies).
  }
}

function getStoredUiLogs() {
  try {
    const raw = window.localStorage.getItem(UI_LOG_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed
      .filter((entry) => entry && typeof entry.text === "string")
      .map((entry) => ({
        level: typeof entry.level === "string" ? entry.level : "info",
        text: entry.text,
      }))
      .slice(-UI_LOG_LIMIT);
  } catch (_error) {
    return [];
  }
}

function setStoredUiLogs(logs) {
  try {
    window.localStorage.setItem(UI_LOG_STORAGE_KEY, JSON.stringify(logs.slice(-UI_LOG_LIMIT)));
  } catch (_error) {
    // Ignore storage failures (private mode / browser policies).
  }
}

function clearBrowserCacheState() {
  try {
    window.localStorage.removeItem(LOCAL_SETTINGS_KEY);
    window.localStorage.removeItem(UI_LOG_STORAGE_KEY);
  } catch (_error) {
    // Ignore storage failures.
  }
  state.uiLogs = [];
  renderUiLogs();
}

function uid(prefix) {
  return `${prefix}_${Math.random().toString(36).slice(2, 7)}`;
}

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function formatDate(value) {
  try {
    return new Date(value).toLocaleString();
  } catch (_error) {
    return value;
  }
}

function jsonPretty(value) {
  return JSON.stringify(value, null, 2);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function safeJson(value) {
  return escapeHtml(jsonPretty(value));
}

function ensurePipelineDefaults(pipeline) {
  if (!pipeline) {
    return pipeline;
  }
  if (!pipeline.default_models || typeof pipeline.default_models !== "object") {
    pipeline.default_models = {};
  }
  Object.entries(FALLBACK_PIPELINE_DEFAULT_MODELS).forEach(([provider, model]) => {
    if (!pipeline.default_models[provider]) {
      pipeline.default_models[provider] = model;
    }
  });
  (pipeline.blocks || []).forEach((block) => {
    if (!block.config) {
      block.config = {};
    }
    if (typeof block.config.use_pipeline_default_model !== "boolean") {
      block.config.use_pipeline_default_model = false;
    }
    if (block.config.use_pipeline_default_model) {
      block.config.model_name = pipeline.default_models[block.config.provider] || block.config.model_name || null;
    } else if (block.config.model_name === undefined) {
      block.config.model_name = null;
    }
  });
  return pipeline;
}

function getPipelineDefaultModel(provider) {
  return (
    state.pipeline?.default_models?.[provider] ||
    state.studio?.pipeline?.default_models?.[provider] ||
    FALLBACK_PIPELINE_DEFAULT_MODELS[provider] ||
    ""
  );
}

function getEffectiveModelForBlock(block) {
  if (!block) {
    return "";
  }
  if (block.config.use_pipeline_default_model) {
    return getPipelineDefaultModel(block.config.provider);
  }
  return block.config.model_name || getPipelineDefaultModel(block.config.provider);
}

function showToast(message, isError = false) {
  els.toast.textContent = message;
  els.toast.classList.remove("hidden");
  els.toast.style.borderColor = isError ? "rgba(255,127,127,0.65)" : "rgba(112,245,194,0.45)";
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => {
    els.toast.classList.add("hidden");
  }, 2600);
}

function uiLog(level, message, meta = null) {
  const timestamp = new Date().toISOString();
  const normalized = (level || "info").toLowerCase();
  let details = "";
  if (meta) {
    if (typeof meta === "string") {
      details = ` ${meta}`;
    } else {
      try {
        details = ` ${JSON.stringify(meta)}`;
      } catch (_error) {
        details = " [meta=unserializable]";
      }
    }
  }
  const line = `[${timestamp}] [${normalized.toUpperCase()}] ${message}${details}`;
  state.uiLogs.push({ level: normalized, text: line });
  if (state.uiLogs.length > UI_LOG_LIMIT) {
    state.uiLogs.splice(0, state.uiLogs.length - UI_LOG_LIMIT);
  }
  setStoredUiLogs(state.uiLogs);
  if (normalized === "error") {
    console.error(line);
  } else if (normalized === "warn") {
    console.warn(line);
  } else {
    console.log(line);
  }
  renderUiLogs();
}

function renderUiLogs() {
  if (!els.uiLogPanel) {
    return;
  }
  if (!state.uiLogs.length) {
    els.uiLogPanel.innerHTML = `<div class="ui-log-entry info">No UI activity logged yet.</div>`;
    return;
  }
  els.uiLogPanel.innerHTML = state.uiLogs
    .map((entry) => `<div class="ui-log-entry ${entry.level}">${escapeHtml(entry.text)}</div>`)
    .join("");
  els.uiLogPanel.scrollTop = els.uiLogPanel.scrollHeight;
}

async function request(path, options = {}) {
  const method = options.method || "GET";
  const requestId = ++state.requestSeq;
  uiLog("debug", `HTTP request #${requestId} ${method} ${path}`);
  const started = performance.now();
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  const text = await response.text();
  let data = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (_error) {
      data = { detail: text };
    }
  }
  if (!response.ok) {
    uiLog("error", `HTTP failure #${requestId} ${method} ${path}`, {
      status: response.status,
      detail: data.detail || text,
      elapsed_ms: Math.round(performance.now() - started),
    });
    throw new Error(data.detail || text || `Request failed: ${response.status}`);
  }
  uiLog("debug", `HTTP success #${requestId} ${method} ${path}`, {
    status: response.status,
    elapsed_ms: Math.round(performance.now() - started),
  });
  return data;
}

function getSelectedBlock() {
  if (!state.pipeline || !state.selectedBlockId) {
    return null;
  }
  return state.pipeline.blocks.find((block) => block.id === state.selectedBlockId) || null;
}

function blockAt(index) {
  return state.pipeline.blocks[index] || null;
}

function selectBlock(blockId, scrollInspector = false) {
  uiLog("info", `Selecting block ${blockId}`);
  state.selectedBlockId = blockId;
  renderInspector();
  renderPipelineCanvas();
  if (scrollInspector) {
    els.blockInspector.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function renderPipelineMeta() {
  if (!state.pipeline) {
    return;
  }
  ensurePipelineDefaults(state.pipeline);
  els.pipelineNameInput.value = state.pipeline.name || "";
  els.pipelineDescriptionInput.value = state.pipeline.description || "";
  const geminiOptions = state.studio?.provider_models?.GEMINI || [];
  const openaiOptions = state.studio?.provider_models?.OPENAI || [];
  const selectedGeminiModel = getPipelineDefaultModel("GEMINI");
  const selectedOpenaiModel = getPipelineDefaultModel("OPENAI");
  const normalizedGeminiOptions = selectedGeminiModel && !geminiOptions.includes(selectedGeminiModel)
    ? [selectedGeminiModel, ...geminiOptions]
    : geminiOptions;
  const normalizedOpenaiOptions = selectedOpenaiModel && !openaiOptions.includes(selectedOpenaiModel)
    ? [selectedOpenaiModel, ...openaiOptions]
    : openaiOptions;
  els.pipelineGeminiModelInput.innerHTML = normalizedGeminiOptions
    .map((model) => `<option value="${escapeHtml(model)}">${escapeHtml(model)}</option>`)
    .join("");
  els.pipelineOpenaiModelInput.innerHTML = normalizedOpenaiOptions
    .map((model) => `<option value="${escapeHtml(model)}">${escapeHtml(model)}</option>`)
    .join("");
  els.pipelineGeminiModelInput.value = selectedGeminiModel;
  els.pipelineOpenaiModelInput.value = selectedOpenaiModel;
}

function renderPipelineLibrary() {
  const catalog = state.pipelineCatalog || [];
  if (!catalog.length) {
    els.pipelineLibrarySelect.innerHTML = `<option value="">No saved pipelines yet</option>`;
    return;
  }
  els.pipelineLibrarySelect.innerHTML = catalog
    .map(
      (item) =>
        `<option value="${escapeHtml(item.key)}">${escapeHtml(item.name)} (${item.block_count} blocks)</option>`,
    )
    .join("");
}

function renderPipelineCanvas() {
  const blocks = state.pipeline?.blocks || [];
  els.pipelineCanvas.innerHTML = "";
  blocks.forEach((block, index) => {
    const effectiveModel = getEffectiveModelForBlock(block);
    const modelModeLabel = block.config.use_pipeline_default_model ? "default" : "override";
    const card = document.createElement("div");
    card.className = `block-card ${block.id === state.selectedBlockId ? "selected" : ""} ${block.enabled ? "" : "disabled"}`;
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start;">
        <strong>${escapeHtml(block.name)}</strong>
        <div style="display:flex;gap:6px;align-items:center;">
          <span class="chip">${escapeHtml(block.config.provider)}</span>
          <button type="button" class="block-edit-btn" data-edit="${escapeHtml(block.id)}">✎ Edit</button>
        </div>
      </div>
      <div style="font-size:11px;color:var(--text-dim);margin-top:6px;">${escapeHtml(block.id)}</div>
      <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;">
        <span class="chip">${escapeHtml(block.type)}</span>
        <span class="chip">${escapeHtml(modelModeLabel)}: ${escapeHtml(effectiveModel)}</span>
        ${block.config.response_schema_name ? `<span class="chip">${escapeHtml(block.config.response_schema_name)}</span>` : ""}
      </div>
      ${
        block.input_blocks.length
          ? `<div style="margin-top:8px;color:var(--text-dim);font-size:11px;">in: ${escapeHtml(block.input_blocks.join(", "))}</div>`
          : ""
      }
    `;
    card.addEventListener("click", () => {
      selectBlock(block.id);
    });
    const editBtn = card.querySelector(".block-edit-btn");
    if (editBtn) {
      editBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        selectBlock(block.id, true);
      });
    }
    els.pipelineCanvas.appendChild(card);

    if (index < blocks.length - 1) {
      const arrow = document.createElement("div");
      arrow.className = "block-arrow";
      arrow.textContent = "↓";
      els.pipelineCanvas.appendChild(arrow);
    }
  });
}

function createBlockFromTemplate(template) {
  const baseId = template.type.replaceAll("-", "_");
  const existing = new Set(state.pipeline.blocks.map((block) => block.id));
  let candidate = baseId;
  let index = 1;
  while (existing.has(candidate)) {
    index += 1;
    candidate = `${baseId}_${index}`;
  }
  const block = {
    id: candidate,
    name: template.name,
    description: template.description || "",
    type: template.type,
    enabled: true,
    input_blocks: [],
    config: deepClone(template.config),
  };
  if (typeof block.config.use_pipeline_default_model !== "boolean") {
    block.config.use_pipeline_default_model = false;
  }
  if (block.config.model_name === undefined) {
    block.config.model_name = null;
  }
  return block;
}

function renderTemplateRail() {
  els.templateRail.innerHTML = "";
  (state.studio?.block_templates || []).forEach((template) => {
    const item = document.createElement("div");
    item.className = "template-item";
    item.innerHTML = `
      <span class="chip">${escapeHtml(template.type)}</span>
      <span style="font-size:12px;color:var(--text-dim);">${escapeHtml(template.name)}</span>
      <button class="btn ghost" type="button">Add</button>
    `;
    item.querySelector("button").addEventListener("click", () => {
      const newBlock = createBlockFromTemplate(template);
      const selectedIndex = state.pipeline.blocks.findIndex((block) => block.id === state.selectedBlockId);
      const insertIndex = selectedIndex >= 0 ? selectedIndex + 1 : state.pipeline.blocks.length;
      state.pipeline.blocks.splice(insertIndex, 0, newBlock);
      state.selectedBlockId = newBlock.id;
      uiLog("info", "Added block from template", { block_id: newBlock.id, type: newBlock.type });
      renderAll();
    });
    els.templateRail.appendChild(item);
  });
}

function refreshModelList(provider, selectedModel = "") {
  const options = state.studio?.provider_models?.[provider] || [];
  const normalizedOptions = selectedModel && !options.includes(selectedModel) ? [selectedModel, ...options] : options;
  els.providerModelList.innerHTML = normalizedOptions.map((model) => `<option value="${model}"></option>`).join("");
}

function renderInspector() {
  const selected = getSelectedBlock();
  if (!selected) {
    els.inspectorEmpty.classList.remove("hidden");
    els.blockInspector.classList.add("hidden");
    if (els.blockModelHint) {
      els.blockModelHint.textContent = "";
    }
    return;
  }
  els.inspectorEmpty.classList.add("hidden");
  els.blockInspector.classList.remove("hidden");

  els.blockIdInput.value = selected.id;
  els.blockNameInput.value = selected.name;
  els.blockTypeInput.value = selected.type;
  els.blockEnabledInput.value = String(selected.enabled);
  els.blockProviderInput.value = selected.config.provider;
  refreshModelList(selected.config.provider, selected.config.model_name || "");
  els.blockModelSourceInput.value = selected.config.use_pipeline_default_model ? "default" : "custom";
  els.blockModelInput.value = selected.config.use_pipeline_default_model
    ? getEffectiveModelForBlock(selected)
    : selected.config.model_name || "";
  els.blockModelInput.disabled = selected.config.use_pipeline_default_model;
  els.blockTempInput.value = selected.config.temperature;
  els.blockSystemInstructionInput.value = selected.config.system_instruction;
  els.blockPromptTemplateInput.value = selected.config.prompt_template;
  const pipelineDefaultModel = getPipelineDefaultModel(selected.config.provider);
  const effectiveModel = getEffectiveModelForBlock(selected);
  els.blockModelHint.textContent = selected.config.use_pipeline_default_model
    ? `Using pipeline default model for ${selected.config.provider}: ${effectiveModel || pipelineDefaultModel || "not set"}`
    : `Override active. Pipeline default for ${selected.config.provider}: ${pipelineDefaultModel || "not set"}`;

  const schemas = state.studio?.schemas || [];
  els.blockSchemaInput.innerHTML = `<option value="">None</option>${schemas
    .map((schema) => `<option value="${schema}">${schema}</option>`)
    .join("")}`;
  els.blockSchemaInput.value = selected.config.response_schema_name || "";

  els.dependencyCheckboxes.innerHTML = "";
  state.pipeline.blocks
    .filter((candidate) => candidate.id !== selected.id)
    .forEach((candidate) => {
      const wrapper = document.createElement("label");
      wrapper.className = "dependency-item";
      const checked = selected.input_blocks.includes(candidate.id) ? "checked" : "";
      wrapper.innerHTML = `<input type="checkbox" data-id="${candidate.id}" ${checked}/> ${candidate.name}`;
      els.dependencyCheckboxes.appendChild(wrapper);
    });
}

function renameBlockId(oldId, newId) {
  if (!newId || oldId === newId) {
    return true;
  }
  if (state.pipeline.blocks.some((block) => block.id === newId)) {
    showToast(`Block id '${newId}' already exists.`, true);
    return false;
  }
  state.pipeline.blocks.forEach((block) => {
    block.input_blocks = block.input_blocks.map((value) => (value === oldId ? newId : value));
  });
  state.selectedBlockId = newId;
  return true;
}

function bindInspectorEvents() {
  els.blockIdInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    const nextId = els.blockIdInput.value.trim();
    if (!nextId) {
      els.blockIdInput.value = selected.id;
      return;
    }
    if (!renameBlockId(selected.id, nextId)) {
      els.blockIdInput.value = selected.id;
      return;
    }
    const oldId = selected.id;
    selected.id = nextId;
    uiLog("info", "Block ID changed", { from: oldId, to: nextId });
    renderPipelineCanvas();
    renderInspector();
  });

  els.blockNameInput.addEventListener("input", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.name = els.blockNameInput.value;
    renderPipelineCanvas();
  });
  els.blockNameInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    uiLog("debug", "Block name updated", { block_id: selected.id, name: selected.name });
  });

  els.blockEnabledInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.enabled = els.blockEnabledInput.value === "true";
    uiLog("info", "Block enabled state changed", { block_id: selected.id, enabled: selected.enabled });
    renderPipelineCanvas();
  });

  els.blockProviderInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.provider = els.blockProviderInput.value;
    refreshModelList(selected.config.provider, selected.config.model_name || "");
    const preferred = getPipelineDefaultModel(selected.config.provider) || (state.studio?.provider_models?.[selected.config.provider] || [])[0];
    if (!selected.config.use_pipeline_default_model && preferred) {
      selected.config.model_name = preferred;
      els.blockModelInput.value = preferred;
    }
    uiLog("info", "Block provider changed", {
      block_id: selected.id,
      provider: selected.config.provider,
      model_name: getEffectiveModelForBlock(selected),
      using_pipeline_default_model: selected.config.use_pipeline_default_model,
    });
    renderPipelineCanvas();
    renderInspector();
  });

  els.blockModelSourceInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.use_pipeline_default_model = els.blockModelSourceInput.value === "default";
    if (selected.config.use_pipeline_default_model) {
      selected.config.model_name = getPipelineDefaultModel(selected.config.provider);
    } else if (!selected.config.model_name) {
      selected.config.model_name = getPipelineDefaultModel(selected.config.provider);
    }
    uiLog("info", "Block model source changed", {
      block_id: selected.id,
      use_pipeline_default_model: selected.config.use_pipeline_default_model,
      effective_model: getEffectiveModelForBlock(selected),
    });
    renderPipelineCanvas();
    renderInspector();
  });

  els.blockModelInput.addEventListener("input", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.model_name = els.blockModelInput.value;
    uiLog("debug", "Block model updated", {
      block_id: selected.id,
      model_name: selected.config.model_name,
    });
    renderPipelineCanvas();
    renderInspector();
  });

  els.blockTempInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.temperature = Number(els.blockTempInput.value || 0.7);
    uiLog("debug", "Block temperature updated", {
      block_id: selected.id,
      temperature: selected.config.temperature,
    });
  });

  els.blockSchemaInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.response_schema_name = els.blockSchemaInput.value || null;
    selected.config.response_mime_type = selected.config.response_schema_name ? "application/json" : null;
    uiLog("info", "Block schema changed", {
      block_id: selected.id,
      response_schema_name: selected.config.response_schema_name,
    });
    renderPipelineCanvas();
  });

  els.blockSystemInstructionInput.addEventListener("input", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.system_instruction = els.blockSystemInstructionInput.value;
  });
  els.blockSystemInstructionInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    uiLog("debug", "System instruction edited", {
      block_id: selected.id,
      chars: selected.config.system_instruction.length,
    });
  });

  els.blockPromptTemplateInput.addEventListener("input", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.prompt_template = els.blockPromptTemplateInput.value;
  });
  els.blockPromptTemplateInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    uiLog("debug", "Prompt template edited", {
      block_id: selected.id,
      chars: selected.config.prompt_template.length,
    });
  });

  els.dependencyCheckboxes.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    const checked = [...els.dependencyCheckboxes.querySelectorAll("input[type='checkbox']:checked")].map(
      (input) => input.dataset.id,
    );
    selected.input_blocks = checked;
    uiLog("info", "Block dependencies changed", {
      block_id: selected.id,
      input_blocks: checked,
    });
    renderPipelineCanvas();
  });

  els.moveBlockLeftBtn.addEventListener("click", () => moveSelectedBlock(-1));
  els.moveBlockRightBtn.addEventListener("click", () => moveSelectedBlock(1));

  els.duplicateBlockBtn.addEventListener("click", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    const duplicate = deepClone(selected);
    duplicate.id = uid(`${selected.id}_copy`);
    duplicate.name = `${selected.name} Copy`;
    const index = state.pipeline.blocks.findIndex((block) => block.id === selected.id);
    state.pipeline.blocks.splice(index + 1, 0, duplicate);
    state.selectedBlockId = duplicate.id;
    uiLog("info", "Block duplicated", { source_block_id: selected.id, new_block_id: duplicate.id });
    renderAll();
  });

  els.deleteBlockBtn.addEventListener("click", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    if (state.pipeline.blocks.length <= 1) {
      showToast("Pipeline must keep at least one block.", true);
      return;
    }
    state.pipeline.blocks = state.pipeline.blocks.filter((block) => block.id !== selected.id);
    state.pipeline.blocks.forEach((block) => {
      block.input_blocks = block.input_blocks.filter((value) => value !== selected.id);
    });
    state.selectedBlockId = state.pipeline.blocks[0]?.id || null;
    uiLog("warn", "Block deleted", { block_id: selected.id });
    renderAll();
  });
}

function moveSelectedBlock(offset) {
  const selected = getSelectedBlock();
  if (!selected) {
    return;
  }
  const index = state.pipeline.blocks.findIndex((block) => block.id === selected.id);
  const target = index + offset;
  if (target < 0 || target >= state.pipeline.blocks.length) {
    return;
  }
  const temp = state.pipeline.blocks[index];
  state.pipeline.blocks[index] = state.pipeline.blocks[target];
  state.pipeline.blocks[target] = temp;
  uiLog("info", "Block moved", {
    block_id: selected.id,
    from_index: index,
    to_index: target,
  });
  renderPipelineCanvas();
}

function renderRuns() {
  els.runsList.innerHTML = "";
  if (!state.runs.length) {
    els.runsList.innerHTML = `<div class="empty">No dry runs yet. Save and run to start quality iteration.</div>`;
  }
  state.runs.forEach((run) => {
    const card = document.createElement("div");
    card.className = `run-card ${state.activeRun?.run_id === run.run_id ? "active" : ""}`;
    card.innerHTML = `
      <strong>${escapeHtml(run.final_title || "Untitled Output")}</strong>
      <div style="margin-top:6px;font-size:12px;color:var(--text-dim);">${escapeHtml(run.run_id)}</div>
      <div style="font-size:11px;color:var(--text-dim);">${formatDate(run.timestamp)}</div>
      <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap;">
        <span class="chip">${run.block_count} blocks</span>
        <span class="chip">score: ${run.final_metrics?.quality_proxy_score ?? "-"}</span>
      </div>
    `;
    card.addEventListener("click", async () => {
      try {
        uiLog("info", "Loading run details", { run_id: run.run_id });
        const detail = await request(`/runs/${run.run_id}`);
        state.activeRun = detail;
        state.runStatusLabel.textContent = `Loaded ${run.run_id} (${formatDate(run.timestamp)})`;
        state.qualityScoreLabel.textContent = String(detail.final_metrics?.quality_proxy_score ?? "-");
        renderRuns();
        renderRunDetails();
      } catch (error) {
        showToast(error.message, true);
      }
    });
    els.runsList.appendChild(card);
  });
}

function renderRunDetails() {
  if (!state.activeRun) {
    els.runDetails.innerHTML = `<div class="empty">Select a run to inspect prompts, block outputs, and generated artifacts.</div>`;
    return;
  }

  const run = state.activeRun;
  const blockIds = run.block_sequence || Object.keys(run.outputs || {});
  const detailsHtml = blockIds
    .map((blockId) => {
      const trace = run.block_traces?.[blockId];
      const output = run.outputs?.[blockId];
      return `
        <details>
          <summary>${escapeHtml(blockId)}</summary>
          ${
            trace
              ? `<div style="margin:6px 0;color:var(--text-dim);font-size:12px;">
                  ${escapeHtml(trace.provider)} / ${escapeHtml(trace.model_name)} / temp ${trace.temperature}
                </div>
                <pre>${safeJson(trace.resolved_prompt)}</pre>`
              : ""
          }
          <pre>${safeJson(output)}</pre>
        </details>
      `;
    })
    .join("");

  const artifacts = (run.artifacts || [])
    .map(
      (artifact) =>
        `<li><a class="artifact-link" target="_blank" href="/runs/${encodeURIComponent(run.run_id)}/artifacts/${encodeURIComponent(artifact.name)}">${escapeHtml(artifact.name)}</a> (${artifact.size_bytes} bytes)</li>`,
    )
    .join("");

  els.runDetails.innerHTML = `
    <div style="margin-bottom:8px;">
      <strong>Final Artifact</strong>
      <pre>${safeJson(run.final_output)}</pre>
    </div>
    <div style="margin-bottom:8px;">
      <strong>Block Traces</strong>
      ${detailsHtml || '<div class="empty">No block details found.</div>'}
    </div>
    <div>
      <strong>Saved Files</strong>
      <ul>${artifacts || "<li>No artifacts found.</li>"}</ul>
    </div>
  `;
}

function renderCompareSelectors() {
  const options = state.runs
    .map((run) => `<option value="${run.run_id}">${run.run_id} | ${run.final_title || "Untitled"}</option>`)
    .join("");
  els.baselineRunSelect.innerHTML = options;
  els.candidateRunSelect.innerHTML = options;

  if (state.runs.length > 1) {
    els.baselineRunSelect.value = state.runs[1].run_id;
    els.candidateRunSelect.value = state.runs[0].run_id;
  } else if (state.runs.length === 1) {
    els.baselineRunSelect.value = state.runs[0].run_id;
    els.candidateRunSelect.value = state.runs[0].run_id;
  }
}

function renderComparison() {
  if (!state.comparison) {
    els.compareResult.innerHTML = `<div class="empty">Pick two runs and compare final artifacts.</div>`;
    return;
  }
  const metrics = state.comparison.metrics
    .map((metric) => {
      const deltaClass = Number(metric.delta) >= 0 ? "delta-up" : "delta-down";
      const deltaSign = Number(metric.delta) >= 0 ? "+" : "";
      return `<tr>
        <td>${escapeHtml(metric.label)}</td>
        <td>${metric.baseline}</td>
        <td>${metric.candidate}</td>
        <td class="${deltaClass}">${deltaSign}${metric.delta}</td>
      </tr>`;
    })
    .join("");
  const notes = (state.comparison.quality_notes || [])
    .map((note) => `<li>${escapeHtml(note)}</li>`)
    .join("");

  els.compareResult.innerHTML = `
    ${notes ? `<ul>${notes}</ul>` : ""}
    <table class="metrics-table">
      <thead>
        <tr><th>Metric</th><th>Baseline</th><th>Candidate</th><th>Delta</th></tr>
      </thead>
      <tbody>${metrics}</tbody>
    </table>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px;">
      <div>
        <strong>Baseline: ${escapeHtml(state.comparison.baseline_title || state.comparison.baseline_run_id)}</strong>
        <pre>${safeJson(state.comparison.baseline_output)}</pre>
      </div>
      <div>
        <strong>Candidate: ${escapeHtml(state.comparison.candidate_title || state.comparison.candidate_run_id)}</strong>
        <pre>${safeJson(state.comparison.candidate_output)}</pre>
      </div>
    </div>
  `;
}

function renderSettingsDialog() {
  const payload = state.settingsPayload;
  if (!payload) {
    return;
  }
  const local = getLocalSettings();
  const geminiKey = payload.settings?.gemini_api_key || local.gemini_api_key || "";
  const openaiKey = payload.settings?.openai_api_key || local.openai_api_key || "";
  const credPath =
    payload.settings?.google_application_credentials ||
    local.google_application_credentials ||
    "";

  els.geminiKeyInput.value = geminiKey;
  els.openaiKeyInput.value = openaiKey;
  els.googleCredPathInput.value = credPath;
  const status = payload.status || {};
  const badges = [
    ["Gemini", status.gemini_configured],
    ["OpenAI", status.openai_configured],
    ["Google Upload", status.google_credentials_configured],
  ];
  els.settingsStatusBadges.innerHTML = badges
    .map(([label, ok]) => `<span class="chip">${label}: ${ok ? "ready" : "missing"}</span>`)
    .join("");
}

function renderAll() {
  renderPipelineMeta();
  renderPipelineLibrary();
  renderPipelineCanvas();
  renderTemplateRail();
  renderInspector();
  renderRuns();
  renderRunDetails();
  renderCompareSelectors();
  renderComparison();
  renderSettingsDialog();
}

async function loadStudio() {
  try {
    uiLog("info", "Loading studio bootstrap payload");
    const studio = await request("/studio");
    state.studio = studio;
    state.pipeline = ensurePipelineDefaults(deepClone(studio.pipeline));
    state.pipelineCatalog = studio.pipeline_catalog || [];
    state.runs = studio.run_summaries || [];
    state.settingsPayload = studio.settings;
    state.selectedBlockId = state.pipeline.blocks?.[0]?.id || null;
    if (state.runs.length) {
      state.runStatusLabel.textContent = `Loaded ${state.runs.length} historical runs`;
    }
    uiLog("info", "Studio loaded", {
      blocks: state.pipeline.blocks.length,
      named_pipelines: state.pipelineCatalog.length,
      runs: state.runs.length,
    });
    renderAll();
  } catch (error) {
    uiLog("error", "Studio load failed", error.message);
    showToast(error.message, true);
  }
}

async function savePipeline() {
  try {
    state.pipeline.name = els.pipelineNameInput.value.trim() || "Found Phone Director";
    state.pipeline.description = els.pipelineDescriptionInput.value.trim();
    ensurePipelineDefaults(state.pipeline);
    const saved = await request("/pipeline", {
      method: "PUT",
      body: jsonPretty(state.pipeline),
    });
    state.pipeline = ensurePipelineDefaults(saved);
    uiLog("info", "Pipeline saved", { name: saved.name, blocks: saved.blocks.length });
    showToast("Pipeline saved.");
    renderAll();
  } catch (error) {
    uiLog("error", "Pipeline save failed", error.message);
    showToast(error.message, true);
  }
}

async function runPipeline() {
  try {
    uiLog("info", "Run requested", { pipeline: state.pipeline?.name });
    await savePipeline();
    els.runPipelineBtn.disabled = true;
    els.runStatusLabel.textContent = "Running dry run...";
    const run = await request("/run", {
      method: "POST",
      body: jsonPretty({
        pipeline: state.pipeline,
        persist_pipeline: true,
      }),
    });
    const runDetail = await request(`/runs/${run.run_id}`);
    state.activeRun = runDetail;
    state.runs.unshift(run);
    state.runStatusLabel.textContent = `Run complete: ${run.run_id}`;
    state.qualityScoreLabel.textContent = String(runDetail.final_metrics?.quality_proxy_score ?? "-");
    uiLog("info", "Run completed", {
      run_id: run.run_id,
      blocks: run.block_count,
      quality_proxy_score: runDetail.final_metrics?.quality_proxy_score ?? null,
    });
    showToast(`Dry run complete: ${run.run_id}`);
    renderAll();
  } catch (error) {
    uiLog("error", "Run failed", error.message);
    showToast(error.message, true);
    els.runStatusLabel.textContent = "Run failed.";
  } finally {
    els.runPipelineBtn.disabled = false;
  }
}

function bindTopLevelEvents() {
  els.savePipelineBtn.addEventListener("click", savePipeline);
  els.runPipelineBtn.addEventListener("click", runPipeline);
  els.refreshStudioBtn.addEventListener("click", loadStudio);
  els.pipelineGeminiModelInput.addEventListener("change", () => {
    if (!state.pipeline) {
      return;
    }
    ensurePipelineDefaults(state.pipeline);
    state.pipeline.default_models.GEMINI = els.pipelineGeminiModelInput.value;
    state.pipeline.blocks.forEach((block) => {
      if (block.config.provider === "GEMINI" && block.config.use_pipeline_default_model) {
        block.config.model_name = els.pipelineGeminiModelInput.value;
      }
    });
    uiLog("info", "Pipeline Gemini default model changed", { model_name: els.pipelineGeminiModelInput.value });
    renderPipelineCanvas();
    renderInspector();
  });
  els.pipelineOpenaiModelInput.addEventListener("change", () => {
    if (!state.pipeline) {
      return;
    }
    ensurePipelineDefaults(state.pipeline);
    state.pipeline.default_models.OPENAI = els.pipelineOpenaiModelInput.value;
    state.pipeline.blocks.forEach((block) => {
      if (block.config.provider === "OPENAI" && block.config.use_pipeline_default_model) {
        block.config.model_name = els.pipelineOpenaiModelInput.value;
      }
    });
    uiLog("info", "Pipeline OpenAI default model changed", { model_name: els.pipelineOpenaiModelInput.value });
    renderPipelineCanvas();
    renderInspector();
  });

  els.saveNamedPipelineBtn.addEventListener("click", async () => {
    if (!state.pipeline) {
      return;
    }
    const suggested = (els.pipelineNameInput.value || state.pipeline.name || "").trim();
    const name = window.prompt("Save pipeline as name:", suggested);
    if (!name || !name.trim()) {
      return;
    }
    try {
      uiLog("info", "Saving named pipeline", { name: name.trim() });
      const result = await request("/pipelines/save", {
        method: "POST",
        body: jsonPretty({
          name: name.trim(),
          pipeline: state.pipeline,
          set_active: true,
        }),
      });
      state.pipeline = ensurePipelineDefaults(result.pipeline);
      state.pipelineCatalog = result.pipeline_catalog || state.pipelineCatalog;
      uiLog("info", "Named pipeline saved", { name: name.trim() });
      showToast(`Saved named pipeline: ${name.trim()}`);
      renderAll();
    } catch (error) {
      uiLog("error", "Save named pipeline failed", error.message);
      showToast(error.message, true);
    }
  });

  els.loadPipelineBtn.addEventListener("click", async () => {
    const key = els.pipelineLibrarySelect.value;
    if (!key) {
      showToast("Pick a saved pipeline first.", true);
      return;
    }
    try {
      uiLog("info", "Loading named pipeline", { key });
      const result = await request("/pipelines/load", {
        method: "POST",
        body: jsonPretty({
          name: key,
          set_active: true,
        }),
      });
      state.pipeline = ensurePipelineDefaults(result.pipeline);
      state.pipelineCatalog = result.pipeline_catalog || state.pipelineCatalog;
      state.selectedBlockId = state.pipeline.blocks?.[0]?.id || null;
      uiLog("info", "Named pipeline loaded", { key, blocks: state.pipeline.blocks.length });
      showToast(`Loaded pipeline: ${key}`);
      renderAll();
    } catch (error) {
      uiLog("error", "Load named pipeline failed", error.message);
      showToast(error.message, true);
    }
  });

  els.snapshotPipelineBtn.addEventListener("click", async () => {
    try {
      uiLog("info", "Creating pipeline snapshot");
      await savePipeline();
      const result = await request("/pipeline/snapshot", {
        method: "POST",
        body: jsonPretty({
          pipeline: state.pipeline,
          label: state.pipeline.name,
        }),
      });
      showToast(`Snapshot saved: ${result.path}`);
      uiLog("info", "Snapshot created", { path: result.path });
    } catch (error) {
      uiLog("error", "Snapshot failed", error.message);
      showToast(error.message, true);
    }
  });

  els.resetPipelineBtn.addEventListener("click", async () => {
    try {
      uiLog("warn", "Resetting pipeline to default");
      const pipeline = await request("/pipeline/reset", { method: "POST", body: "{}" });
      state.pipeline = ensurePipelineDefaults(pipeline);
      state.selectedBlockId = pipeline.blocks?.[0]?.id || null;
      showToast("Pipeline reset to default.");
      uiLog("info", "Pipeline reset complete", { blocks: pipeline.blocks.length });
      renderAll();
    } catch (error) {
      uiLog("error", "Pipeline reset failed", error.message);
      showToast(error.message, true);
    }
  });

  els.compareRunsBtn.addEventListener("click", async () => {
    const baselineRunId = els.baselineRunSelect.value;
    const candidateRunId = els.candidateRunSelect.value;
    if (!baselineRunId || !candidateRunId) {
      showToast("Select two runs first.", true);
      return;
    }
    try {
      uiLog("info", "Comparing runs", { baselineRunId, candidateRunId });
      state.comparison = await request("/compare", {
        method: "POST",
        body: jsonPretty({
          baseline_run_id: baselineRunId,
          candidate_run_id: candidateRunId,
        }),
      });
      renderComparison();
      showToast("Comparison ready.");
      uiLog("info", "Run comparison complete", { metrics: state.comparison.metrics.length });
    } catch (error) {
      uiLog("error", "Run comparison failed", error.message);
      showToast(error.message, true);
    }
  });

  els.openSettingsBtn.addEventListener("click", () => {
    uiLog("info", "Opening settings dialog");
    renderSettingsDialog();
    els.settingsDialog.showModal();
  });
  els.cancelSettingsBtn.addEventListener("click", () => {
    uiLog("info", "Closing settings dialog");
    els.settingsDialog.close();
  });

  els.saveSettingsBtn.addEventListener("click", async () => {
    const nextSettings = {
      gemini_api_key: els.geminiKeyInput.value.trim() || null,
      openai_api_key: els.openaiKeyInput.value.trim() || null,
      google_application_credentials: els.googleCredPathInput.value.trim() || null,
    };
    setLocalSettings(nextSettings);
    uiLog("info", "Saving settings", {
      gemini_set: Boolean(nextSettings.gemini_api_key),
      openai_set: Boolean(nextSettings.openai_api_key),
      creds_set: Boolean(nextSettings.google_application_credentials),
    });
    try {
      const payload = await request("/settings", {
        method: "PUT",
        body: jsonPretty(nextSettings),
      });
      state.settingsPayload = payload;
      renderSettingsDialog();
      showToast("Settings saved (local + backend).");
      uiLog("info", "Settings saved (local + backend)");
      els.settingsDialog.close();
    } catch (error) {
      uiLog("warn", "Settings saved locally but backend sync failed", error.message);
      showToast(`Saved locally. Backend sync failed: ${error.message}`, true);
    }
  });

  if (els.freshStartBtn) {
    els.freshStartBtn.addEventListener("click", async () => {
      const confirmed = window.confirm(
        "Fresh Start will clear browser cache (saved keys + UI logs), reset active pipeline to default, and reload studio. Continue?",
      );
      if (!confirmed) {
        return;
      }
      try {
        clearBrowserCacheState();
        uiLog("warn", "Fresh start requested: browser cache cleared");
        await request("/pipeline/reset", { method: "POST", body: "{}" });
        uiLog("info", "Active pipeline reset to default");
        await loadStudio();
        showToast("Fresh start complete.");
        els.settingsDialog.close();
      } catch (error) {
        uiLog("error", "Fresh start failed", error.message);
        showToast(`Fresh start failed: ${error.message}`, true);
      }
    });
  }

  if (els.clearUiLogBtn) {
    els.clearUiLogBtn.addEventListener("click", () => {
      state.uiLogs = [];
      setStoredUiLogs([]);
      renderUiLogs();
      uiLog("info", "UI activity log cleared");
    });
  }

  if (els.copyUiLogBtn) {
    els.copyUiLogBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(state.uiLogs.map((entry) => entry.text).join("\n"));
        showToast("Copied UI logs to clipboard.");
        uiLog("info", "Copied UI activity logs to clipboard", { lines: state.uiLogs.length });
      } catch (error) {
        uiLog("warn", "Failed to copy UI logs", error.message);
        showToast("Could not copy logs to clipboard.", true);
      }
    });
  }
}

bindInspectorEvents();
bindTopLevelEvents();
state.uiLogs = getStoredUiLogs();
renderUiLogs();
uiLog("info", "Director Studio UI bootstrapping");
loadStudio();
