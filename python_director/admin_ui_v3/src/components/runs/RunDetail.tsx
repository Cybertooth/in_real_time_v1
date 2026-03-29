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
  const advanceRunStage = useStore((s) => s.advanceRunStage)
  const retryBlock = useStore((s) => s.retryBlock)
  const deleteRun = useStore((s) => s.deleteRun)

  const [runData, setRunData] = useState<(RunProgress & {
    final_output?: unknown
    headline_image_path?: string | null
    headline_image_prompt?: string | null
    seed_prompt?: string | null
    tags?: string[]
    allowed_languages?: string[]
    dry_run_stage?: number
    dry_run_stage_name?: string
    awaiting_stage_approval?: boolean
    deployment_stage?: string
  }) | null>(null)
  const [loading, setLoading] = useState(true)
  const [rerunDialogOpen, setRerunDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [retryTarget, setRetryTarget] = useState<{ id: string; name: string } | null>(null)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [approvingStage, setApprovingStage] = useState(false)
  const [publishing, setPublishing] = useState(false)

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
    setUploading(true)
    try {
      const result = await api.uploadRun(runId)
      if (!result.story_id) {
        throw new Error('Upload completed without a story ID. Check Firebase settings and server logs.')
      }
      const deployment = result.deployment_stage ?? 'uploaded'
      showToast(
        deployment === 'live'
          ? `Uploaded and published! Story ID: ${result.story_id}`
          : deployment === 'published'
            ? `Uploaded and published (not live yet). Story ID: ${result.story_id}`
          : `Uploaded! Story ID: ${result.story_id}`,
      )
      setRunData((prev) => (
        prev
          ? { ...prev, story_id: result.story_id, deployment_stage: result.deployment_stage ?? prev.deployment_stage }
          : null
      ))
      setUploadDialogOpen(false)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      showToast(msg, true)
    } finally {
      setUploading(false)
    }
  }

  const handleRerun = (
    seedPrompt: string,
    tags: string[],
    allowedLanguages: string[],
    options: {
      stagedWorkflow: boolean
      deliveryProfile: 'standard' | 'on_demand'
      storyMode: 'live' | 'scheduled' | 'subscription'
      storySubMode: 'default' | 'on_demand'
      scheduledStartAt: string | null
      ttsTier: 'premium' | 'cheap'
    },
  ) => {
    setRerunDialogOpen(false)
    if (!runId) return
    rerunFromRun(runId, seedPrompt || null, tags, allowedLanguages, options)
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

  const handleApproveNextStage = async () => {
    if (!runId) return
    setApprovingStage(true)
    try {
      const progress = await advanceRunStage(runId)
      if (!progress) {
        return
      }
      setRunData((prev) => (prev ? { ...prev, ...(progress as unknown as Record<string, unknown>) } as RunProgress & {
        final_output?: unknown
        headline_image_path?: string | null
        headline_image_prompt?: string | null
        seed_prompt?: string | null
        tags?: string[]
        allowed_languages?: string[]
        dry_run_stage?: number
        dry_run_stage_name?: string
        awaiting_stage_approval?: boolean
        deployment_stage?: string
      } : null))
      showToast('Stage approved. Continuing pipeline...')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to advance stage'
      showToast(msg, true)
    } finally {
      setApprovingStage(false)
    }
  }

  const handleMakeLive = async () => {
    if (!runId) return
    setPublishing(true)
    try {
      await api.makeRunLive(runId)
      showToast('Story is now live in the app.')
      setRunData((prev) => (prev ? { ...prev, deployment_stage: 'live' } : null))
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to make story live'
      showToast(msg, true)
    } finally {
      setPublishing(false)
    }
  }

  // Seed/tags from the stored run progress (present if set when run was created)
  const storedSeed = (runData as unknown as Record<string, unknown>).seed_prompt as string | null | undefined
  const storedTags = (runData as unknown as Record<string, unknown>).tags as string[] | undefined
  const storedAllowedLanguages = (runData as unknown as Record<string, unknown>).allowed_languages as string[] | undefined
  const storedStoryMode = ((runData as unknown as Record<string, unknown>).story_mode as 'live' | 'scheduled' | 'subscription' | undefined) ?? 'live'
  const storedStorySubMode = ((runData as unknown as Record<string, unknown>).story_sub_mode as 'default' | 'on_demand' | undefined) ?? 'default'
  const storedScheduledStartAt = (runData as unknown as Record<string, unknown>).scheduled_start_at as string | null | undefined
  const storedTtsTier = ((runData as unknown as Record<string, unknown>).tts_tier as 'premium' | 'cheap' | undefined) ?? 'premium'
  const runTitle = runData.final_title || runData.pipeline_name || 'Untitled Story'
  const runStage = (runData as unknown as Record<string, unknown>).dry_run_stage as number | undefined
  const runStageName = (runData as unknown as Record<string, unknown>).dry_run_stage_name as string | undefined
  const awaitingStageApproval = Boolean((runData as unknown as Record<string, unknown>).awaiting_stage_approval)
  const deploymentStage = ((runData as unknown as Record<string, unknown>).deployment_stage as string | undefined) ?? 'dry_run'
  const canUpload = runData.status === 'succeeded' && (runStage ?? 3) >= 3
  const themePreviewHex = deriveThemePreview(`${runId ?? ''}:${runTitle}`)
  const scheduleLabel =
    storedStoryMode === 'scheduled' && storedScheduledStartAt
      ? formatTime(storedScheduledStartAt)
      : 'N/A'

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
          <div className={`text-center py-1.5 text-xs font-bold uppercase tracking-widest border-b flex items-center justify-center gap-2 ${
            deploymentStage === 'live'
              ? 'bg-mint/10 text-mint border-mint/20'
              : deploymentStage === 'published'
                ? 'bg-blue-300/10 text-blue-300 border-blue-300/20'
              : 'bg-amber-300/10 text-amber-300 border-amber-300/20'
          }`}>
            <span
              className={`w-2 h-2 rounded-full ${
                deploymentStage === 'live'
                  ? 'bg-mint animate-pulse'
                  : deploymentStage === 'published'
                    ? 'bg-blue-300'
                    : 'bg-amber-300'
              }`}
            />
            {deploymentStage === 'live'
              ? `Live on Production (Story ID: ${runData.story_id})`
              : deploymentStage === 'published'
                ? `Published (Activation Based on Story Mode) — Story ID: ${runData.story_id}`
                : `Uploaded (Not Live Yet) — Story ID: ${runData.story_id}`}
          </div>
        )}
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-text">
              {runTitle}
            </h2>
            <Badge variant={statusVariant()}>{runData.status}</Badge>
            <Badge variant="default">
              Stage {runStage ?? 3}: {(runStageName ?? 'multimedia_artifact_generation').replaceAll('_', ' ')}
            </Badge>
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

            {runData.status === 'succeeded' && awaitingStageApproval && (
              <button
                type="button"
                onClick={handleApproveNextStage}
                disabled={approvingStage}
                className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-mint/40 text-mint hover:bg-mint/10 transition-colors"
              >
                {approvingStage ? 'Advancing...' : 'Approve + Continue Stage'}
              </button>
            )}

            {runData.status === 'succeeded' && (
              <button
                type="button"
                onClick={handleUpload}
                disabled={uploading || !canUpload}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
                  uploading || !canUpload
                    ? 'bg-surface text-text-dim border border-border cursor-not-allowed opacity-60'
                    : 'cursor-pointer bg-mint text-black hover:brightness-110'
                }`}
              >
                {canUpload ? 'Upload' : 'Complete Stage 3 First'}
              </button>
            )}

            {runData.story_id && deploymentStage === 'uploaded' && (
              <button
                type="button"
                onClick={handleMakeLive}
                disabled={publishing}
                className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-amber-300 text-black hover:brightness-110 transition-colors"
              >
                {publishing ? 'Publishing...' : 'Make Live'}
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
        initialStoryMode={storedStoryMode}
        initialStorySubMode={storedStorySubMode}
        initialScheduledStartAt={storedScheduledStartAt ?? null}
        initialTtsTier={storedTtsTier}
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
        description="Upload using lifecycle/audio settings already selected during dry-run."
        confirmLabel={uploading ? 'Uploading...' : 'Upload Story'}
        confirmVariant="primary"
        onConfirm={handleUploadConfirm}
        onCancel={() => !uploading && setUploadDialogOpen(false)}
      >
        <div className="flex flex-col gap-3 text-sm">
          <div className="grid grid-cols-[140px_1fr] gap-2 text-xs text-text-dim">
            <span className="uppercase tracking-wide">Story Mode</span>
            <span className="text-text">{storedStoryMode}</span>
            <span className="uppercase tracking-wide">Story Subtype</span>
            <span className="text-text">{storedStorySubMode}</span>
            <span className="uppercase tracking-wide">Scheduled Start</span>
            <span className="text-text">{scheduleLabel}</span>
            <span className="uppercase tracking-wide">TTS Tier</span>
            <span className="text-text">{storedTtsTier}</span>
          </div>

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
