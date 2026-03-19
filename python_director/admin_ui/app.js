const state = {
  studio: null,
  pipeline: null,
  selectedBlockId: null,
  runs: [],
  activeRun: null,
  comparison: null,
  settingsPayload: null,
};

const els = {
  pipelineCanvas: document.getElementById("pipelineCanvas"),
  templateRail: document.getElementById("templateRail"),
  pipelineNameInput: document.getElementById("pipelineNameInput"),
  pipelineDescriptionInput: document.getElementById("pipelineDescriptionInput"),
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
  blockModelInput: document.getElementById("blockModelInput"),
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
  geminiKeyInput: document.getElementById("geminiKeyInput"),
  openaiKeyInput: document.getElementById("openaiKeyInput"),
  googleCredPathInput: document.getElementById("googleCredPathInput"),
  settingsStatusBadges: document.getElementById("settingsStatusBadges"),
};

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

function showToast(message, isError = false) {
  els.toast.textContent = message;
  els.toast.classList.remove("hidden");
  els.toast.style.borderColor = isError ? "rgba(255,127,127,0.65)" : "rgba(112,245,194,0.45)";
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => {
    els.toast.classList.add("hidden");
  }, 2600);
}

async function request(path, options = {}) {
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
    throw new Error(data.detail || text || `Request failed: ${response.status}`);
  }
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

function renderPipelineMeta() {
  if (!state.pipeline) {
    return;
  }
  els.pipelineNameInput.value = state.pipeline.name || "";
  els.pipelineDescriptionInput.value = state.pipeline.description || "";
}

function renderPipelineCanvas() {
  const blocks = state.pipeline?.blocks || [];
  els.pipelineCanvas.innerHTML = "";
  blocks.forEach((block, index) => {
    const card = document.createElement("div");
    card.className = `block-card ${block.id === state.selectedBlockId ? "selected" : ""} ${block.enabled ? "" : "disabled"}`;
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start;">
        <strong>${escapeHtml(block.name)}</strong>
        <span class="chip">${escapeHtml(block.config.provider)}</span>
      </div>
      <div style="font-size:11px;color:var(--text-dim);margin-top:6px;">${escapeHtml(block.id)}</div>
      <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;">
        <span class="chip">${escapeHtml(block.type)}</span>
        <span class="chip">${escapeHtml(block.config.model_name)}</span>
        ${block.config.response_schema_name ? `<span class="chip">${escapeHtml(block.config.response_schema_name)}</span>` : ""}
      </div>
      ${
        block.input_blocks.length
          ? `<div style="margin-top:8px;color:var(--text-dim);font-size:11px;">in: ${escapeHtml(block.input_blocks.join(", "))}</div>`
          : ""
      }
    `;
    card.addEventListener("click", () => {
      state.selectedBlockId = block.id;
      renderInspector();
      renderPipelineCanvas();
    });
    els.pipelineCanvas.appendChild(card);

    if (index < blocks.length - 1) {
      const arrow = document.createElement("div");
      arrow.className = "block-arrow";
      arrow.textContent = "→";
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
  return {
    id: candidate,
    name: template.name,
    description: template.description || "",
    type: template.type,
    enabled: true,
    input_blocks: [],
    config: deepClone(template.config),
  };
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
      renderAll();
    });
    els.templateRail.appendChild(item);
  });
}

function refreshModelList(provider) {
  const options = state.studio?.provider_models?.[provider] || [];
  els.providerModelList.innerHTML = options.map((model) => `<option value="${model}"></option>`).join("");
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

  els.blockIdInput.value = selected.id;
  els.blockNameInput.value = selected.name;
  els.blockTypeInput.value = selected.type;
  els.blockEnabledInput.value = String(selected.enabled);
  els.blockProviderInput.value = selected.config.provider;
  refreshModelList(selected.config.provider);
  els.blockModelInput.value = selected.config.model_name;
  els.blockTempInput.value = selected.config.temperature;
  els.blockSystemInstructionInput.value = selected.config.system_instruction;
  els.blockPromptTemplateInput.value = selected.config.prompt_template;

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
    selected.id = nextId;
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

  els.blockEnabledInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.enabled = els.blockEnabledInput.value === "true";
    renderPipelineCanvas();
  });

  els.blockProviderInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.provider = els.blockProviderInput.value;
    refreshModelList(selected.config.provider);
    const preferred = (state.studio?.provider_models?.[selected.config.provider] || [])[0];
    if (preferred) {
      selected.config.model_name = preferred;
      els.blockModelInput.value = preferred;
    }
    renderPipelineCanvas();
  });

  els.blockModelInput.addEventListener("input", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.model_name = els.blockModelInput.value;
    renderPipelineCanvas();
  });

  els.blockTempInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.temperature = Number(els.blockTempInput.value || 0.7);
  });

  els.blockSchemaInput.addEventListener("change", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.response_schema_name = els.blockSchemaInput.value || null;
    selected.config.response_mime_type = selected.config.response_schema_name ? "application/json" : null;
    renderPipelineCanvas();
  });

  els.blockSystemInstructionInput.addEventListener("input", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.system_instruction = els.blockSystemInstructionInput.value;
  });

  els.blockPromptTemplateInput.addEventListener("input", () => {
    const selected = getSelectedBlock();
    if (!selected) {
      return;
    }
    selected.config.prompt_template = els.blockPromptTemplateInput.value;
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
  els.geminiKeyInput.value = payload.settings?.gemini_api_key || "";
  els.openaiKeyInput.value = payload.settings?.openai_api_key || "";
  els.googleCredPathInput.value = payload.settings?.google_application_credentials || "";
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
    const studio = await request("/studio");
    state.studio = studio;
    state.pipeline = deepClone(studio.pipeline);
    state.runs = studio.run_summaries || [];
    state.settingsPayload = studio.settings;
    state.selectedBlockId = state.pipeline.blocks?.[0]?.id || null;
    if (state.runs.length) {
      state.runStatusLabel.textContent = `Loaded ${state.runs.length} historical runs`;
    }
    renderAll();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function savePipeline() {
  try {
    state.pipeline.name = els.pipelineNameInput.value.trim() || "Found Phone Director";
    state.pipeline.description = els.pipelineDescriptionInput.value.trim();
    const saved = await request("/pipeline", {
      method: "PUT",
      body: jsonPretty(state.pipeline),
    });
    state.pipeline = saved;
    showToast("Pipeline saved.");
    renderAll();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function runPipeline() {
  try {
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
    showToast(`Dry run complete: ${run.run_id}`);
    renderAll();
  } catch (error) {
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

  els.snapshotPipelineBtn.addEventListener("click", async () => {
    try {
      await savePipeline();
      const result = await request("/pipeline/snapshot", {
        method: "POST",
        body: jsonPretty({
          pipeline: state.pipeline,
          label: state.pipeline.name,
        }),
      });
      showToast(`Snapshot saved: ${result.path}`);
    } catch (error) {
      showToast(error.message, true);
    }
  });

  els.resetPipelineBtn.addEventListener("click", async () => {
    try {
      const pipeline = await request("/pipeline/reset", { method: "POST", body: "{}" });
      state.pipeline = pipeline;
      state.selectedBlockId = pipeline.blocks?.[0]?.id || null;
      showToast("Pipeline reset to default.");
      renderAll();
    } catch (error) {
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
      state.comparison = await request("/compare", {
        method: "POST",
        body: jsonPretty({
          baseline_run_id: baselineRunId,
          candidate_run_id: candidateRunId,
        }),
      });
      renderComparison();
      showToast("Comparison ready.");
    } catch (error) {
      showToast(error.message, true);
    }
  });

  els.openSettingsBtn.addEventListener("click", () => {
    renderSettingsDialog();
    els.settingsDialog.showModal();
  });
  els.cancelSettingsBtn.addEventListener("click", () => els.settingsDialog.close());

  els.saveSettingsBtn.addEventListener("click", async () => {
    try {
      const payload = await request("/settings", {
        method: "PUT",
        body: jsonPretty({
          gemini_api_key: els.geminiKeyInput.value.trim() || null,
          openai_api_key: els.openaiKeyInput.value.trim() || null,
          google_application_credentials: els.googleCredPathInput.value.trim() || null,
        }),
      });
      state.settingsPayload = payload;
      renderSettingsDialog();
      showToast("Settings saved.");
      els.settingsDialog.close();
    } catch (error) {
      showToast(error.message, true);
    }
  });
}

bindInspectorEvents();
bindTopLevelEvents();
loadStudio();
