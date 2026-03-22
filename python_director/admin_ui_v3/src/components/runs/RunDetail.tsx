import { useEffect, useState } from 'react'
import { useParams, NavLink, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useStore } from '../../store'
import * as api from '../../api'
import type { RunProgress } from '../../types'
import Badge from '../shared/Badge'
import RunDialog from '../shared/RunDialog'
import ConfirmDialog from '../shared/ConfirmDialog'
import BlockAccordion from './BlockAccordion'
import TimelineView from './TimelineView'
import ExperiencePreview from './ExperiencePreview'
import ImagesView from './ImagesView'

const THEME_PREVIEW = ['#00FF9C', '#FF8A65', '#90CAF9', '#A5D6A7', '#FFB74D', '#4DD0E1', '#CE93D8', '#F48FB1', '#81D4FA', '#AED581']

function deriveThemePreview(seed: string): string {
  let hash = 0
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0
  }
  return THEME_PREVIEW[hash % THEME_PREVIEW.length]
}

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const showToast = useStore((s) => s.showToast)
  // Selective selector — returns liveRun only when it's for THIS run.
  // Null for all other runs, so non-active RunDetail instances never re-render mid-poll.
  const liveRun = useStore((s) => s.liveRun?.run_id === runId ? s.liveRun : null)
  const rerunFromRun = useStore((s) => s.rerunFromRun)
  const retryBlock = useStore((s) => s.retryBlock)
  const deleteRun = useStore((s) => s.deleteRun)

  const [runData, setRunData] = useState<(RunProgress & {
    final_output?: unknown
    headline_image_path?: string | null
    headline_image_prompt?: string | null
    seed_prompt?: string | null
    tags?: string[]
    allowed_languages?: string[]
  }) | null>(null)
  const [loading, setLoading] = useState(true)
  const [rerunDialogOpen, setRerunDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [retryTarget, setRetryTarget] = useState<{ id: string; name: string } | null>(null)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [storyMode, setStoryMode] = useState<'live' | 'scheduled' | 'subscription'>('live')
  const [scheduledStartAt, setScheduledStartAt] = useState('')
  const [ttsTier, setTtsTier] = useState<'premium' | 'cheap'>('premium')
  const [uploading, setUploading] = useState(false)

  // Load run data on mount / when navigating to a different run
  useEffect(() => {
    if (!runId) return
    let cancelled = false
    setLoading(true)
    api.getRun(runId)
      .then((data) => {
        if (cancelled) return
        setRunData(data as unknown as RunProgress & {
          final_output?: unknown
          headline_image_path?: string | null
          headline_image_prompt?: string | null
          seed_prompt?: string | null
          tags?: string[]
          allowed_languages?: string[]
        })
        setLoading(false)
      })
      .catch(async () => {
        try {
          const status = await api.getRunStatus(runId)
          if (cancelled) return
          setRunData(status)
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Failed to load run'
          if (!cancelled) showToast(msg, true)
        } finally {
          if (!cancelled) setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [runId, showToast])

  // Sync live progress when this is the active run
  useEffect(() => {
    if (liveRun) {
      setRunData((prev) => ({
        ...(prev ?? {}),
        ...liveRun,
      } as RunProgress & {
        final_output?: unknown
        headline_image_path?: string | null
        headline_image_prompt?: string | null
        seed_prompt?: string | null
        tags?: string[]
        allowed_languages?: string[]
      }))
      setLoading(false)
      if (liveRun.status === 'succeeded' && runId) {
        api.getRun(runId).then((full) => {
          setRunData((prev) => ({ ...(prev ?? {}), ...(full as unknown as Record<string, unknown>) } as RunProgress & {
            final_output?: unknown
            headline_image_path?: string | null
            headline_image_prompt?: string | null
            seed_prompt?: string | null
            tags?: string[]
            allowed_languages?: string[]
          }))
        }).catch(() => {
          // no-op; status fallback still works
        })
      }
    }
  }, [liveRun, runId])

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-mint border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!runData) {
    return (
      <div className="h-full flex items-center justify-center text-text-dim text-sm">
        Run not found
      </div>
    )
  }

  const isActive = runData.status === 'running' || runData.status === 'queued'
  const isFinished = runData.status === 'succeeded' || runData.status === 'failed'

  const statusVariant = () => {
    switch (runData.status) {
      case 'succeeded': return 'success' as const
      case 'failed': return 'error' as const
      case 'running': return 'warning' as const
      default: return 'default' as const
    }
  }

  const formatTime = (ts: string | null) => {
    if (!ts) return '--'
    try { return new Date(ts).toLocaleString() } catch { return ts }
  }

  const handleUpload = () => {
    setUploadDialogOpen(true)
  }

  const handleUploadConfirm = async () => {
    if (!runId) return
    let scheduleIso: string | null = null
    if (storyMode === 'scheduled') {
      if (!scheduledStartAt) {
        showToast('Select a scheduled start datetime.', true)
        return
      }
      const localDate = new Date(scheduledStartAt)
      if (Number.isNaN(localDate.getTime())) {
        showToast('Invalid scheduled datetime.', true)
        return
      }
      scheduleIso = localDate.toISOString()
    }

    setUploading(true)
    try {
      const result = await api.uploadRun(runId, {
        story_mode: storyMode,
        scheduled_start_at: scheduleIso,
        tts_tier: ttsTier,
      })
      showToast(`Uploaded! Story ID: ${result.story_id}`)
      setRunData((prev) => (prev ? { ...prev, story_id: result.story_id } : null))
      setUploadDialogOpen(false)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      showToast(msg, true)
    } finally {
      setUploading(false)
    }
  }

  const handleRerun = (seedPrompt: string, tags: string[], allowedLanguages: string[]) => {
    setRerunDialogOpen(false)
    if (!runId) return
    rerunFromRun(runId, seedPrompt || null, tags, allowedLanguages)
    navigate('/runs')
  }

  const handleDelete = async () => {
    setDeleteDialogOpen(false)
    if (!runId) return
    await deleteRun(runId)
    navigate('/runs')
  }

  const handleRetryBlock = (blockId: string, blockName: string) => {
    setRetryTarget({ id: blockId, name: blockName })
  }

  const handleRetryConfirm = () => {
    if (!retryTarget || !runId) return
    setRetryTarget(null)
    retryBlock(runId, retryTarget.id)
  }

  // Seed/tags from the stored run progress (present if set when run was created)
  const storedSeed = (runData as unknown as Record<string, unknown>).seed_prompt as string | null | undefined
  const storedTags = (runData as unknown as Record<string, unknown>).tags as string[] | undefined
  const storedAllowedLanguages = (runData as unknown as Record<string, unknown>).allowed_languages as string[] | undefined
  const runTitle = runData.final_title || runData.pipeline_name || 'Untitled Story'
  const themePreviewHex = deriveThemePreview(`${runId ?? ''}:${runTitle}`)

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-1.5 text-sm font-medium transition-colors ${
      isActive
        ? 'text-mint border-b-2 border-mint'
        : 'text-text-dim hover:text-text border-b-2 border-transparent'
    }`

  return (
    <>
      <div className="flex flex-col h-full">
        {runData.story_id && (
          <div className="bg-mint/10 text-mint text-center py-1.5 text-xs font-bold uppercase tracking-widest border-b border-mint/20 flex items-center justify-center gap-2">
            <span className="w-2 h-2 rounded-full bg-mint animate-pulse" />
            Live on Production (Story ID: {runData.story_id})
          </div>
        )}
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-text">
              {runTitle}
            </h2>
            <Badge variant={statusVariant()}>{runData.status}</Badge>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-dim">{formatTime(runData.started_at)}</span>

            {isFinished && (
              <button
                type="button"
                onClick={() => setRerunDialogOpen(true)}
                className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
              >
                Re-run
              </button>
            )}

            {runData.status === 'succeeded' && (
              <button
                type="button"
                onClick={handleUpload}
                disabled={uploading}
                className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-mint text-black hover:brightness-110 transition-colors"
              >
                Upload
              </button>
            )}

            {!isActive && (
              <button
                type="button"
                onClick={() => setDeleteDialogOpen(true)}
                className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-danger-soft text-danger border border-danger/30 hover:brightness-110 transition-colors"
              >
                Delete
              </button>
            )}
          </div>
        </div>

        {/* Sub-tab navigation */}
        <nav className="flex items-center gap-1 px-4 border-b border-border">
          <NavLink to={`/runs/${runId}/blocks`} className={navLinkClass}>Blocks</NavLink>
          <NavLink to={`/runs/${runId}/timeline`} className={navLinkClass}>Timeline</NavLink>
          <NavLink to={`/runs/${runId}/experience`} className={navLinkClass}>Experience</NavLink>
          <NavLink to={`/runs/${runId}/images`} className={navLinkClass}>Images</NavLink>
        </nav>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <Routes>
            <Route
              path="blocks"
              element={
                <BlockAccordion
                  blockSequence={runData.block_sequence}
                  blockTraces={runData.block_traces}
                  onRetryBlock={!isActive ? handleRetryBlock : undefined}
                />
              }
            />
            <Route path="timeline" element={<TimelineView timeline={runData.timeline} />} />
            <Route path="experience" element={<ExperiencePreview runData={runData} />} />
            <Route
              path="images"
              element={
                <ImagesView
                  runId={runId!}
                  finalOutput={(runData as unknown as Record<string, unknown>).final_output as Record<string, unknown> | null}
                  headlineImagePath={(runData as unknown as Record<string, unknown>).headline_image_path as string | null}
                  headlineImagePrompt={(runData as unknown as Record<string, unknown>).headline_image_prompt as string | null}
                />
              }
            />
            <Route path="*" element={<Navigate to="blocks" replace />} />
          </Routes>
        </div>
      </div>

      {/* Re-run dialog — pre-populated with original seed/tags */}
      <RunDialog
        open={rerunDialogOpen}
        onClose={() => setRerunDialogOpen(false)}
        onStart={handleRerun}
        initialSeedPrompt={storedSeed ?? ''}
        initialTags={storedTags ?? []}
        initialAllowedLanguages={storedAllowedLanguages ?? []}
        initialMode="same"
        title="Re-run Pipeline"
        submitLabel="Start Re-run"
      />

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete this run?"
        description={`"${runData.final_title || runData.pipeline_name}" (${formatTime(runData.started_at)}) will be permanently deleted. All block outputs, artifacts, and timeline data will be lost.`}
        confirmLabel="Delete Run"
        confirmVariant="danger"
        onConfirm={handleDelete}
        onCancel={() => setDeleteDialogOpen(false)}
      />

      {/* Retry block confirmation dialog */}
      <ConfirmDialog
        open={retryTarget !== null}
        title="Retry from this block?"
        description={`"${retryTarget?.name}" and all downstream blocks that failed or didn't run will be re-executed. Already-succeeded blocks will be skipped.`}
        confirmLabel="Retry"
        confirmVariant="primary"
        onConfirm={handleRetryConfirm}
        onCancel={() => setRetryTarget(null)}
      />

      {/* Upload configuration modal */}
      <ConfirmDialog
        open={uploadDialogOpen}
        title="Upload Story"
        description="Choose story lifecycle and TTS profile for production upload."
        confirmLabel={uploading ? 'Uploading...' : 'Upload Story'}
        confirmVariant="primary"
        onConfirm={handleUploadConfirm}
        onCancel={() => !uploading && setUploadDialogOpen(false)}
      >
        <div className="flex flex-col gap-3 text-sm">
          <label className="flex flex-col gap-1">
            <span className="text-text-dim text-xs uppercase tracking-wide">Story Mode</span>
            <select
              value={storyMode}
              onChange={(e) => setStoryMode(e.target.value as 'live' | 'scheduled' | 'subscription')}
              className="bg-surface border border-border rounded-lg px-3 py-2 text-text"
              disabled={uploading}
            >
              <option value="live">Live (global start)</option>
              <option value="scheduled">Scheduled (future start)</option>
              <option value="subscription">Subscription (start on follow)</option>
            </select>
          </label>

          {storyMode === 'scheduled' && (
            <label className="flex flex-col gap-1">
              <span className="text-text-dim text-xs uppercase tracking-wide">Scheduled Start (Local Time)</span>
              <input
                type="datetime-local"
                value={scheduledStartAt}
                onChange={(e) => setScheduledStartAt(e.target.value)}
                className="bg-surface border border-border rounded-lg px-3 py-2 text-text"
                disabled={uploading}
              />
            </label>
          )}

          <label className="flex flex-col gap-1">
            <span className="text-text-dim text-xs uppercase tracking-wide">TTS Tier</span>
            <select
              value={ttsTier}
              onChange={(e) => setTtsTier(e.target.value as 'premium' | 'cheap')}
              className="bg-surface border border-border rounded-lg px-3 py-2 text-text"
              disabled={uploading}
            >
              <option value="premium">Premium</option>
              <option value="cheap">Cheap</option>
            </select>
          </label>

          <div className="flex items-center gap-2 text-xs text-text-dim">
            <span className="uppercase tracking-wide">Theme Preview</span>
            <span className="inline-block w-5 h-5 rounded-full border border-border" style={{ backgroundColor: themePreviewHex }} />
            <code>{themePreviewHex}</code>
          </div>
        </div>
      </ConfirmDialog>
    </>
  )
}
