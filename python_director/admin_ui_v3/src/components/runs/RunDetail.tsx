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

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const showToast = useStore((s) => s.showToast)
  const activeRunProgress = useStore((s) => s.activeRunProgress)
  const activeRunId = useStore((s) => s.activeRunId)
  const rerunFromRun = useStore((s) => s.rerunFromRun)
  const retryBlock = useStore((s) => s.retryBlock)
  const deleteRun = useStore((s) => s.deleteRun)

  const [runData, setRunData] = useState<RunProgress | null>(null)
  const [loading, setLoading] = useState(true)
  const [rerunDialogOpen, setRerunDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [retryTarget, setRetryTarget] = useState<{ id: string; name: string } | null>(null)

  useEffect(() => {
    if (!runId) return

    if (runId === activeRunId && activeRunProgress) {
      setRunData(activeRunProgress)
      setLoading(false)
      return
    }

    setLoading(true)
    api
      .getRunStatus(runId)
      .then((data) => {
        setRunData(data)
        setLoading(false)
      })
      .catch((err) => {
        const msg = err instanceof Error ? err.message : 'Failed to load run'
        showToast(msg, true)
        setLoading(false)
      })
  }, [runId, activeRunId, activeRunProgress, showToast])

  useEffect(() => {
    if (runId === activeRunId && activeRunProgress) {
      setRunData(activeRunProgress)
    }
  }, [runId, activeRunId, activeRunProgress])

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

  const isActive = runId === activeRunId
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

  const handleUpload = async () => {
    if (!runId) return
    if (!window.confirm('Upload this run to the production system?')) return
    try {
      const result = await api.uploadRun(runId)
      showToast(`Uploaded! Story ID: ${result.story_id}`)
      setRunData((prev) => (prev ? { ...prev, story_id: result.story_id } : null))
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      showToast(msg, true)
    }
  }

  const handleRerun = (seedPrompt: string, tags: string[]) => {
    setRerunDialogOpen(false)
    if (!runId) return
    rerunFromRun(runId, seedPrompt || null, tags)
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
              {runData.final_title || runData.pipeline_name}
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
    </>
  )
}
