import type {
  StudioBootstrap,
  PipelineDefinition,
  PipelineCatalogItem,
  SettingsPayload,
  AppSettings,
  RunProgress,
  RunResult,
  RunComparison,
  Story,
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

export function resetPipeline(templateKey: string): Promise<PipelineDefinition> {
  return request<PipelineDefinition>('/api/pipeline/reset', {
    method: 'POST',
    ...json({ template_key: templateKey }),
  })
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
  allowedLanguages?: string[],
  options?: {
    staged_workflow?: boolean
    target_dry_run_stage?: number
    delivery_profile?: 'standard' | 'on_demand'
  },
): Promise<RunProgress> {
  const body: Record<string, unknown> = { pipeline }
  if (seedPrompt) body.seed_prompt = seedPrompt
  if (tags && tags.length > 0) body.tags = tags
  if (allowedLanguages && allowedLanguages.length > 0) body.allowed_languages = allowedLanguages
  if (options?.staged_workflow !== undefined) body.staged_workflow = options.staged_workflow
  if (options?.target_dry_run_stage !== undefined) body.target_dry_run_stage = options.target_dry_run_stage
  if (options?.delivery_profile) body.delivery_profile = options.delivery_profile
  return request<RunProgress>('/api/runs/start', { method: 'POST', ...json(body) })
}

export function generateRandomSeedPrompt(
  tags?: string[],
  allowedLanguages?: string[],
): Promise<{ seed_prompt: string }> {
  const body: Record<string, unknown> = {}
  if (tags && tags.length > 0) body.tags = tags
  if (allowedLanguages && allowedLanguages.length > 0) body.allowed_languages = allowedLanguages
  return request<{ seed_prompt: string }>('/api/seed-prompt/random', {
    method: 'POST',
    ...json(body),
  })
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
  payload: {
    story_mode: 'live' | 'scheduled' | 'subscription'
    story_sub_mode?: 'default' | 'on_demand'
    scheduled_start_at?: string | null
    tts_tier: 'premium' | 'cheap'
  },
): Promise<{ status: string; story_id: string }> {
  const body: Record<string, unknown> = {
    story_mode: payload.story_mode,
    story_sub_mode: payload.story_sub_mode ?? 'default',
    tts_tier: payload.tts_tier,
  }
  if (payload.scheduled_start_at) body.scheduled_start_at = payload.scheduled_start_at
  return request<{ status: string; story_id: string }>(
    `/api/upload/${encodeURIComponent(runId)}`,
    { method: 'POST', ...json(body) },
  )
}

export function approveNextRunStage(
  runId: string,
  targetDryRunStage?: number,
): Promise<RunProgress> {
  const body: Record<string, unknown> = {}
  if (targetDryRunStage !== undefined) body.target_dry_run_stage = targetDryRunStage
  return request<RunProgress>(
    `/api/runs/${encodeURIComponent(runId)}/approve-next-stage`,
    { method: 'POST', ...json(body) },
  )
}

export function makeRunLive(runId: string): Promise<{ status: string; story_id: string }> {
  return request<{ status: string; story_id: string }>(
    `/api/runs/${encodeURIComponent(runId)}/make-live`,
    { method: 'POST' },
  )
}

export function rerunRun(
  runId: string,
  seedPrompt?: string | null,
  tags?: string[],
  allowedLanguages?: string[],
  options?: {
    staged_workflow?: boolean
    target_dry_run_stage?: number
    delivery_profile?: 'standard' | 'on_demand'
  },
): Promise<RunProgress> {
  const body: Record<string, unknown> = { use_original_seed: seedPrompt === undefined }
  if (seedPrompt !== undefined) body.seed_prompt = seedPrompt
  if (tags !== undefined) body.tags = tags
  if (allowedLanguages !== undefined) body.allowed_languages = allowedLanguages
  if (options?.staged_workflow !== undefined) body.staged_workflow = options.staged_workflow
  if (options?.target_dry_run_stage !== undefined) body.target_dry_run_stage = options.target_dry_run_stage
  if (options?.delivery_profile) body.delivery_profile = options.delivery_profile
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

export function listStories(): Promise<Story[]> {
  return request<Story[]>('/api/stories')
}

export function deleteStory(storyId: string): Promise<{ status: string; story_id: string }> {
  return request<{ status: string; story_id: string }>(
    `/api/stories/${encodeURIComponent(storyId)}`,
    { method: 'DELETE' },
  )
}
