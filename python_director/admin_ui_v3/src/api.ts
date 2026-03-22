import type {
  StudioBootstrap,
  PipelineDefinition,
  PipelineCatalogItem,
  SettingsPayload,
  AppSettings,
  RunProgress,
  RunResult,
  RunComparison,
} from './types'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new ApiError(text, res.status)
  }
  return res.json() as Promise<T>
}

function json(body: unknown): RequestInit {
  return {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

export function getStudio(): Promise<StudioBootstrap> {
  return request<StudioBootstrap>('/api/studio')
}

export function savePipeline(pipeline: PipelineDefinition): Promise<PipelineDefinition> {
  return request<PipelineDefinition>('/api/pipeline', { method: 'PUT', ...json(pipeline) })
}

export function resetPipeline(): Promise<PipelineDefinition> {
  return request<PipelineDefinition>('/api/pipeline/reset', { method: 'POST' })
}

export function snapshotPipeline(
  pipeline: PipelineDefinition,
  label?: string,
): Promise<{ status: string; path: string }> {
  const body: Record<string, unknown> = { pipeline }
  if (label !== undefined) body.label = label
  return request<{ status: string; path: string }>('/api/pipeline/snapshot', {
    method: 'POST',
    ...json(body),
  })
}

export function saveNamedPipeline(
  name: string,
  pipeline: PipelineDefinition,
  set_active?: boolean,
): Promise<{
  pipeline: PipelineDefinition
  catalog_item: PipelineCatalogItem
  pipeline_catalog: PipelineCatalogItem[]
}> {
  const body: Record<string, unknown> = { name, pipeline }
  if (set_active !== undefined) body.set_active = set_active
  return request('/api/pipelines/save', { method: 'POST', ...json(body) })
}

export function loadNamedPipeline(
  name: string,
  set_active?: boolean,
): Promise<{ pipeline: PipelineDefinition; pipeline_catalog: PipelineCatalogItem[] }> {
  const body: Record<string, unknown> = { name }
  if (set_active !== undefined) body.set_active = set_active
  return request('/api/pipelines/load', { method: 'POST', ...json(body) })
}

export function deleteNamedPipeline(
  key: string,
): Promise<{ status: string; pipeline_catalog: PipelineCatalogItem[] }> {
  return request(`/api/pipelines/${encodeURIComponent(key)}`, { method: 'DELETE' })
}

export function saveSettings(settings: AppSettings): Promise<SettingsPayload> {
  return request<SettingsPayload>('/api/settings', { method: 'PUT', ...json(settings) })
}

export function startRun(
  pipeline: PipelineDefinition,
  seedPrompt?: string,
  tags?: string[],
): Promise<RunProgress> {
  const body: Record<string, unknown> = { pipeline }
  if (seedPrompt) body.seed_prompt = seedPrompt
  if (tags && tags.length > 0) body.tags = tags
  return request<RunProgress>('/api/runs/start', { method: 'POST', ...json(body) })
}

export function getRunStatus(runId: string): Promise<RunProgress> {
  return request<RunProgress>(`/api/runs/${encodeURIComponent(runId)}/status`)
}

export function getRun(runId: string): Promise<RunResult> {
  return request<RunResult>(`/api/runs/${encodeURIComponent(runId)}`)
}

export function getRunPipeline(runId: string): Promise<PipelineDefinition> {
  return request<PipelineDefinition>(`/api/runs/${encodeURIComponent(runId)}/pipeline`)
}

export function compareRuns(
  baselineRunId: string,
  candidateRunId: string,
): Promise<RunComparison> {
  return request<RunComparison>('/api/compare', {
    method: 'POST',
    ...json({ baseline_run_id: baselineRunId, candidate_run_id: candidateRunId }),
  })
}

export function uploadRun(
  runId: string,
): Promise<{ status: string; story_id: string }> {
  return request<{ status: string; story_id: string }>(
    `/api/upload/${encodeURIComponent(runId)}`,
    { method: 'POST' },
  )
}

export function rerunRun(
  runId: string,
  seedPrompt?: string | null,
  tags?: string[],
): Promise<RunProgress> {
  const body: Record<string, unknown> = { use_original_seed: seedPrompt === undefined }
  if (seedPrompt !== undefined) body.seed_prompt = seedPrompt
  if (tags !== undefined) body.tags = tags
  return request<RunProgress>(`/api/runs/${encodeURIComponent(runId)}/rerun`, {
    method: 'POST',
    ...json(body),
  })
}

export function deleteRun(runId: string): Promise<{ status: string; run_id: string }> {
  return request<{ status: string; run_id: string }>(
    `/api/runs/${encodeURIComponent(runId)}`,
    { method: 'DELETE' },
  )
}

export function retryBlock(runId: string, blockId: string): Promise<RunProgress> {
  return request<RunProgress>(
    `/api/runs/${encodeURIComponent(runId)}/retry-block/${encodeURIComponent(blockId)}`,
    { method: 'POST' },
  )
}

export function regenerateImage(
  runId: string,
  eventType: string,
  index: number,
  newPrompt: string,
): Promise<{ status: string; local_image_path: string }> {
  return request<{ status: string; local_image_path: string }>(
    `/api/runs/${encodeURIComponent(runId)}/regenerate-image`,
    {
      method: 'POST',
      ...json({ event_type: eventType, index, new_prompt: newPrompt }),
    },
  )
}
