export type ProviderType = 'GEMINI' | 'OPENAI'
export type RunStatus = 'queued' | 'running' | 'succeeded' | 'failed'
export type BlockExecutionStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'skipped'
export type BlockType =
  | 'creative_outliner' | 'brainstorm_critic' | 'brainstorm_rewriter'
  | 'planner' | 'critic' | 'reviser' | 'continuity_auditor'
  | 'decomposer' | 'drop_director' | 'generator'

export interface BlockConfig {
  provider: ProviderType
  model_name: string | null
  use_pipeline_default_model: boolean
  temperature: number
  system_instruction: string
  prompt_template: string
  response_mime_type: string | null
  response_schema_name: string | null
}

export interface PipelineBlock {
  id: string
  name: string
  description: string
  type: BlockType
  enabled: boolean
  config: BlockConfig
  input_blocks: string[]
}

export interface PipelineDefinition {
  name: string
  description: string
  updated_at: string | null
  default_models: Record<string, string>
  blocks: PipelineBlock[]
}

export interface PipelineCatalogItem {
  key: string
  name: string
  description: string
  updated_at: string | null
  block_count: number
}

export interface AppSettings {
  gemini_api_key: string | null
  openai_api_key: string | null
  google_application_credentials: string | null
}

export interface SettingsStatus {
  gemini_configured: boolean
  openai_configured: boolean
  google_credentials_configured: boolean
}

export interface SettingsPayload {
  settings: AppSettings
  status: SettingsStatus
}

export interface BlockTrace {
  block_id: string
  block_name: string
  block_type: BlockType
  provider: ProviderType
  model_name: string
  status: BlockExecutionStatus
  response_schema_name: string | null
  temperature: number
  input_blocks: string[]
  resolved_prompt: string
  resolved_inputs: Record<string, unknown>
  output: unknown
  error_message: string | null
  error_traceback: string | null
  started_at: string | null
  completed_at: string | null
  elapsed_ms: number | null
}

export interface RunTimelineEntry {
  block_id: string
  event_type: string
  story_day: number
  story_time: string
  title: string
  content: Record<string, unknown> | null
}

export interface RunStats {
  total_words: number
  total_tokens: number
  estimated_cost_usd: number
  block_count: number
  success_rate: number
  average_tension_score: number | null
  character_mentions: Record<string, number>
}

export interface RunSummary {
  run_id: string
  timestamp: string
  pipeline_name: string
  status: RunStatus
  final_title: string | null
  block_count: number
  provider_summary: Record<string, number>
  artifact_counts: Record<string, number>
  final_metrics: Record<string, number>
  mode: string
  error_message: string | null
}

export interface RunProgress {
  run_id: string
  timestamp: string
  pipeline_name: string
  status: RunStatus
  mode: string
  block_count: number
  current_block_id: string | null
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  final_title: string | null
  final_metrics: Record<string, number>
  block_sequence: string[]
  block_traces: Record<string, BlockTrace>
  timeline: RunTimelineEntry[]
  stats: RunStats
}

export interface RunResult extends RunSummary {
  current_block_id: string | null
  outputs: Record<string, unknown>
  final_output: unknown
  block_sequence: string[]
  block_traces: Record<string, BlockTrace>
  artifacts: { name: string; relative_path: string; size_bytes: number; content_type: string }[]
  timeline: RunTimelineEntry[]
  stats: RunStats
}

export interface MetricDelta {
  label: string
  baseline: number
  candidate: number
  delta: number
}

export interface RunComparison {
  baseline_run_id: string
  candidate_run_id: string
  baseline_title: string | null
  candidate_title: string | null
  metrics: MetricDelta[]
  quality_notes: string[]
  baseline_output: unknown
  candidate_output: unknown
}

export interface BlockTemplate {
  type: BlockType
  name: string
  description: string
  config: BlockConfig
}

export interface StudioBootstrap {
  pipeline: PipelineDefinition
  pipeline_catalog: PipelineCatalogItem[]
  settings: SettingsPayload
  run_summaries: RunSummary[]
  schemas: string[]
  block_types: BlockType[]
  block_templates: BlockTemplate[]
  provider_models: Record<string, string[]>
}
