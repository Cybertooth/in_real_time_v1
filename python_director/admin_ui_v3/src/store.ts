import { create } from 'zustand'
import * as api from './api'
import { ApiError } from './api'
import type {
  PipelineDefinition,
  PipelineBlock,
  BlockConfig,
  BlockTemplate,
  PipelineCatalogItem,
  SettingsPayload,
  RunSummary,
  RunProgress,
  BlockType,
  StudioBootstrap,
} from './types'

interface Toast {
  message: string
  isError: boolean
}

export interface StudioData {
  pipeline: PipelineDefinition
  pipelineCatalog: PipelineCatalogItem[]
  settings: SettingsPayload
  runSummaries: RunSummary[]
  schemas: string[]
  blockTypes: BlockType[]
  blockTemplates: BlockTemplate[]
  providerModels: Record<string, string[]>
}

interface StudioState {
  // Data
  studio: StudioData | null
  pipeline: PipelineDefinition | null
  pipelineCatalog: PipelineCatalogItem[]
  settings: SettingsPayload | null
  runSummaries: RunSummary[]
  schemas: string[]
  blockTypes: BlockType[]
  blockTemplates: BlockTemplate[]
  providerModels: Record<string, string[]>

  // UI state
  selectedBlockId: string | null
  settingsOpen: boolean
  toast: Toast | null
  loading: boolean
  bootstrapError: boolean

  // Run state
  activeRunId: string | null
  liveRun: RunProgress | null
  pollTimer: ReturnType<typeof setTimeout> | null
  pollInterval: number

  // Actions
  loadStudio: () => Promise<void>
  savePipeline: () => Promise<void>
  selectBlock: (blockId: string | null) => void
  updateBlock: (blockId: string, updates: Partial<PipelineBlock>) => void
  updateBlockConfig: (blockId: string, updates: Partial<BlockConfig>) => void
  moveBlock: (blockId: string, direction: 'up' | 'down') => void
  duplicateBlock: (blockId: string) => void
  deleteBlock: (blockId: string) => void
  renameBlockId: (oldId: string, newId: string) => void
  addBlockFromTemplate: (template: BlockTemplate) => void
  showToast: (message: string, isError?: boolean) => void
  setSettingsOpen: (open: boolean) => void
  startRun: (seedPrompt?: string, tags?: string[]) => Promise<void>
  rerunFromRun: (runId: string, seedPrompt?: string | null, tags?: string[]) => Promise<void>
  retryBlock: (runId: string, blockId: string) => Promise<void>
  deleteRun: (runId: string) => Promise<void>
  stopPolling: () => void
  loadRunProgress: (runId: string) => Promise<void>
  setPipeline: (pipeline: PipelineDefinition) => void
  setPipelineCatalog: (catalog: PipelineCatalogItem[]) => void
  setSettings: (settings: SettingsPayload) => void
  updatePipelineMeta: (updates: Partial<PipelineDefinition>) => void
}

function progressToSummary(p: RunProgress): RunSummary {
  const raw = p as unknown as Record<string, unknown>
  return {
    run_id: p.run_id,
    timestamp: p.timestamp,
    pipeline_name: p.pipeline_name,
    status: p.status,
    final_title: p.final_title,
    block_count: p.block_count,
    provider_summary: (raw.provider_summary as Record<string, number>) ?? {},
    artifact_counts: (raw.artifact_counts as Record<string, number>) ?? {},
    final_metrics: p.final_metrics,
    mode: p.mode,
    error_message: p.error_message,
    seed_prompt: (raw.seed_prompt as string | null) ?? null,
    tags: (raw.tags as string[]) ?? [],
    story_id: p.story_id,
  }
}

export const useStore = create<StudioState>((set, get) => {
  const _startPolling = (
    runId: string,
    successMsg: string,
    failureMsgPrefix: string,
  ) => {
    let interval = 1500

    const poll = async () => {
      if (get().activeRunId !== runId) return // stopped externally
      try {
        const p = await api.getRunStatus(runId)
        set({ liveRun: p, pollInterval: 1500 })
        interval = 1500

        if (p.status === 'succeeded' || p.status === 'failed') {
          const isSuccess = p.status === 'succeeded'

          // Patch runSummaries in place (no loadStudio())
          const { runSummaries } = get()
          const summary = progressToSummary(p)
          const idx = runSummaries.findIndex((r) => r.run_id === runId)
          const updatedSummaries =
            idx >= 0
              ? runSummaries.map((r) => (r.run_id === runId ? summary : r))
              : [summary, ...runSummaries]

          set({ runSummaries: updatedSummaries, activeRunId: null, pollTimer: null })

          // Keep liveRun briefly so RunDetail can see final state, then clear
          setTimeout(() => {
            if (get().liveRun?.run_id === runId) set({ liveRun: null })
          }, 3000)

          get().showToast(
            isSuccess
              ? successMsg
              : `${failureMsgPrefix}: ${p.error_message ?? 'Unknown error'}`,
            !isSuccess,
          )
          return
        }

        const timer = setTimeout(poll, interval)
        set({ pollTimer: timer })
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          set({ activeRunId: null, liveRun: null, pollTimer: null })
          get().showToast('Run no longer available', true)
          return
        }
        interval = Math.min(interval * 2, 10000)
        set({ pollInterval: interval })
        const timer = setTimeout(poll, interval)
        set({ pollTimer: timer })
      }
    }

    const timer = setTimeout(poll, 1500)
    set({ pollTimer: timer })
  }

  return {
    // Data
    studio: null,
    pipeline: null,
    pipelineCatalog: [],
    settings: null,
    runSummaries: [],
    schemas: [],
    blockTypes: [],
    blockTemplates: [],
    providerModels: {},

    // UI state
    selectedBlockId: null,
    settingsOpen: false,
    toast: null,
    loading: false,
    bootstrapError: false,

    // Run state
    activeRunId: null,
    liveRun: null,
    pollTimer: null,
    pollInterval: 1500,

    loadStudio: async () => {
      set({ loading: true, bootstrapError: false })
      try {
        const data: StudioBootstrap = await api.getStudio()
        const studioData: StudioData = {
          pipeline: data.pipeline,
          pipelineCatalog: data.pipeline_catalog,
          settings: data.settings,
          runSummaries: data.run_summaries,
          schemas: data.schemas,
          blockTypes: data.block_types,
          blockTemplates: data.block_templates,
          providerModels: data.provider_models,
        }
        set({
          studio: studioData,
          pipeline: data.pipeline,
          pipelineCatalog: data.pipeline_catalog,
          settings: data.settings,
          runSummaries: data.run_summaries,
          schemas: data.schemas,
          blockTypes: data.block_types,
          blockTemplates: data.block_templates,
          providerModels: data.provider_models,
          loading: false,
          bootstrapError: false,
        })
      } catch {
        set({ loading: false, bootstrapError: true })
      }
    },

    savePipeline: async () => {
      const { pipeline } = get()
      if (!pipeline) return
      try {
        const saved = await api.savePipeline(pipeline)
        set({ pipeline: saved })
        get().showToast('Pipeline saved')
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to save pipeline'
        get().showToast(msg, true)
      }
    },

    selectBlock: (blockId) => {
      set({ selectedBlockId: blockId })
    },

    setSettingsOpen: (open) => {
      set({ settingsOpen: open })
    },

    setPipeline: (pipeline) => {
      set({ pipeline })
    },

    setPipelineCatalog: (catalog) => {
      set({ pipelineCatalog: catalog })
    },

    setSettings: (settings) => {
      set({ settings })
    },

    updatePipelineMeta: (updates) => {
      const { pipeline } = get()
      if (!pipeline) return
      set({ pipeline: { ...pipeline, ...updates } })
    },

    updateBlock: (blockId, updates) => {
      const { pipeline } = get()
      if (!pipeline) return
      set({
        pipeline: {
          ...pipeline,
          blocks: pipeline.blocks.map((b) =>
            b.id === blockId ? { ...b, ...updates } : b,
          ),
        },
      })
    },

    updateBlockConfig: (blockId, updates) => {
      const { pipeline } = get()
      if (!pipeline) return
      set({
        pipeline: {
          ...pipeline,
          blocks: pipeline.blocks.map((b) =>
            b.id === blockId ? { ...b, config: { ...b.config, ...updates } } : b,
          ),
        },
      })
    },

    moveBlock: (blockId, direction) => {
      const { pipeline } = get()
      if (!pipeline) return
      const blocks = [...pipeline.blocks]
      const idx = blocks.findIndex((b) => b.id === blockId)
      if (idx < 0) return
      const targetIdx = direction === 'up' ? idx - 1 : idx + 1
      if (targetIdx < 0 || targetIdx >= blocks.length) return
      ;[blocks[idx], blocks[targetIdx]] = [blocks[targetIdx], blocks[idx]]
      set({ pipeline: { ...pipeline, blocks } })
    },

    duplicateBlock: (blockId) => {
      const { pipeline } = get()
      if (!pipeline) return
      const idx = pipeline.blocks.findIndex((b) => b.id === blockId)
      if (idx < 0) return
      const source = pipeline.blocks[idx]
      const newId = `${source.id}_copy`
      const duplicate: PipelineBlock = {
        ...source,
        id: newId,
        name: `${source.name} (Copy)`,
        config: { ...source.config },
        input_blocks: [...source.input_blocks],
      }
      const blocks = [...pipeline.blocks]
      blocks.splice(idx + 1, 0, duplicate)
      set({ pipeline: { ...pipeline, blocks }, selectedBlockId: newId })
    },

    deleteBlock: (blockId) => {
      const { pipeline, selectedBlockId } = get()
      if (!pipeline) return
      const blocks = pipeline.blocks
        .filter((b) => b.id !== blockId)
        .map((b) => ({
          ...b,
          input_blocks: b.input_blocks.filter((id) => id !== blockId),
        }))
      set({
        pipeline: { ...pipeline, blocks },
        selectedBlockId: selectedBlockId === blockId ? null : selectedBlockId,
      })
    },

    renameBlockId: (oldId, newId) => {
      const { pipeline } = get()
      if (!pipeline) return
      const blocks = pipeline.blocks.map((b) => {
        const updated = { ...b }
        if (updated.id === oldId) {
          updated.id = newId
        }
        updated.input_blocks = updated.input_blocks.map((id) =>
          id === oldId ? newId : id,
        )
        updated.config = {
          ...updated.config,
          prompt_template: updated.config.prompt_template.replaceAll(
            `{{${oldId}}}`,
            `{{${newId}}}`,
          ),
        }
        return updated
      })
      set({
        pipeline: { ...pipeline, blocks },
        selectedBlockId:
          get().selectedBlockId === oldId ? newId : get().selectedBlockId,
      })
    },

    addBlockFromTemplate: (template) => {
      const { pipeline, selectedBlockId } = get()
      if (!pipeline) return
      const baseId = template.type
      const existingIds = new Set(pipeline.blocks.map((b) => b.id))
      let newId = baseId
      let counter = 1
      while (existingIds.has(newId)) {
        newId = `${baseId}_${counter}` as BlockType
        counter++
      }
      const newBlock: PipelineBlock = {
        id: newId,
        name: template.name,
        description: template.description,
        type: template.type,
        enabled: true,
        config: { ...template.config },
        input_blocks: [],
      }
      const blocks = [...pipeline.blocks]
      if (selectedBlockId) {
        const idx = blocks.findIndex((b) => b.id === selectedBlockId)
        if (idx >= 0) {
          blocks.splice(idx + 1, 0, newBlock)
        } else {
          blocks.push(newBlock)
        }
      } else {
        blocks.push(newBlock)
      }
      set({ pipeline: { ...pipeline, blocks }, selectedBlockId: newId })
    },

    showToast: (message, isError = false) => {
      set({ toast: { message, isError } })
      setTimeout(() => {
        set({ toast: null })
      }, 3000)
    },

    startRun: async (seedPrompt?: string, tags?: string[]) => {
      const { pipeline } = get()
      if (!pipeline) return
      get().stopPolling()
      try {
        const progress = await api.startRun(pipeline, seedPrompt, tags)
        set({ activeRunId: progress.run_id, liveRun: progress, pollInterval: 1500 })
        _startPolling(progress.run_id, 'Run completed successfully', 'Run failed')
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to start run'
        get().showToast(msg, true)
      }
    },

    rerunFromRun: async (runId, seedPrompt, tags) => {
      get().stopPolling()
      try {
        const progress = await api.rerunRun(runId, seedPrompt, tags)
        set({ activeRunId: progress.run_id, liveRun: progress, pollInterval: 1500 })
        _startPolling(progress.run_id, 'Re-run completed successfully', 'Re-run failed')
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to start re-run'
        get().showToast(msg, true)
      }
    },

    retryBlock: async (runId, blockId) => {
      get().stopPolling()
      try {
        const progress = await api.retryBlock(runId, blockId)
        set({ activeRunId: runId, liveRun: progress, pollInterval: 1500 })
        _startPolling(runId, 'Block retry completed successfully', 'Block retry failed')
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to retry block'
        get().showToast(msg, true)
      }
    },

    deleteRun: async (runId) => {
      try {
        await api.deleteRun(runId)
        set({ runSummaries: get().runSummaries.filter((r) => r.run_id !== runId) })
        get().showToast('Run deleted')
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to delete run'
        get().showToast(msg, true)
      }
    },

    stopPolling: () => {
      const { pollTimer } = get()
      if (pollTimer) {
        clearTimeout(pollTimer)
        set({ pollTimer: null })
      }
      set({ activeRunId: null, liveRun: null })
    },

    loadRunProgress: async (runId) => {
      try {
        const progress = await api.getRunStatus(runId)
        set({ activeRunId: runId, liveRun: progress })
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load run progress'
        get().showToast(msg, true)
      }
    },
  }
})

// Backward compatibility alias
export const useStudioStore = useStore
