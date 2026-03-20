import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useStore } from '../../store'
import type { RunSummary } from '../../types'
import StatusDot from '../shared/StatusDot'
import Badge from '../shared/Badge'
import RunDialog from '../shared/RunDialog'
import ConfirmDialog from '../shared/ConfirmDialog'

export default function RunList() {
  const runSummaries = useStore((s) => s.runSummaries)
  const activeRunId = useStore((s) => s.activeRunId)
  const activeRunProgress = useStore((s) => s.activeRunProgress)
  const rerunFromRun = useStore((s) => s.rerunFromRun)
  const deleteRun = useStore((s) => s.deleteRun)
  const navigate = useNavigate()

  const [rerunTarget, setRerunTarget] = useState<RunSummary | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<RunSummary | null>(null)

  const statusVariant = (status: string) => {
    switch (status) {
      case 'succeeded': return 'success' as const
      case 'failed': return 'error' as const
      case 'running': return 'warning' as const
      default: return 'default' as const
    }
  }

  const formatTime = (ts: string) => {
    try { return new Date(ts).toLocaleString() } catch { return ts }
  }

  const handleRerun = (seedPrompt: string, tags: string[]) => {
    if (!rerunTarget) return
    setRerunTarget(null)
    rerunFromRun(rerunTarget.run_id, seedPrompt || null, tags)
    navigate(`/runs/${activeRunId ?? ''}`)
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    const id = deleteTarget.run_id
    setDeleteTarget(null)
    await deleteRun(id)
  }

  return (
    <>
      <div className="p-3 flex flex-col gap-2">
        <span className="text-text-dim text-xs font-semibold uppercase tracking-wide px-1">
          Runs
        </span>

        {/* Active run */}
        {activeRunId && activeRunProgress && (
          <button
            type="button"
            onClick={() => navigate(`/runs/${activeRunId}/blocks`)}
            className="w-full text-left p-3 rounded-xl bg-mint-soft border border-mint/30 cursor-pointer transition-colors hover:brightness-110"
          >
            <div className="flex items-center gap-2 mb-2">
              <StatusDot status="running" />
              <span className="text-sm font-medium text-mint">Active Run</span>
            </div>
            <div className="text-xs text-text-dim mb-1">
              {activeRunProgress.pipeline_name}
            </div>
            <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
              <div
                className="h-full bg-mint rounded-full transition-all duration-500"
                style={{
                  width: `${
                    activeRunProgress.block_count > 0
                      ? (Object.values(activeRunProgress.block_traces).filter(
                          (t) => t.status === 'succeeded' || t.status === 'failed',
                        ).length /
                          activeRunProgress.block_count) *
                        100
                      : 0
                  }%`,
                }}
              />
            </div>
          </button>
        )}

        {runSummaries.length === 0 && !activeRunId && (
          <p className="text-text-dim text-sm p-2">
            No runs yet. Start a dry run from the Pipeline Editor.
          </p>
        )}

        {runSummaries.map((run) => (
          <div key={run.run_id} className="group relative">
            <button
              type="button"
              onClick={() => navigate(`/runs/${run.run_id}/blocks`)}
              className="w-full text-left p-3 rounded-xl bg-surface border border-border cursor-pointer hover:bg-surface-raised transition-colors"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-text-dim">{formatTime(run.timestamp)}</span>
                <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
              </div>
              <div className="text-sm font-medium text-text mb-1 truncate pr-16">
                {run.final_title || run.pipeline_name}
              </div>
              <div className="flex items-center gap-3 text-xs text-text-dim flex-wrap">
                {run.final_metrics?.total_words !== undefined && (
                  <span>
                    Words:{' '}
                    <span className="text-text">
                      {Number(run.final_metrics.total_words).toLocaleString()}
                    </span>
                  </span>
                )}
                {run.final_metrics?.quality_proxy_score !== undefined && (
                  <span>
                    Quality:{' '}
                    <span className="text-mint">
                      {Number(run.final_metrics.quality_proxy_score).toFixed(1)}
                    </span>
                  </span>
                )}
                <span>{run.block_count} blocks</span>
                {run.tags && run.tags.length > 0 && (
                  <span className="text-mint/70">{run.tags.join(', ')}</span>
                )}
              </div>
            </button>

            {/* Action buttons — visible on hover */}
            <div className="absolute top-2 right-2 hidden group-hover:flex items-center gap-1">
              <button
                type="button"
                title="Re-run with same or new seed"
                onClick={(e) => { e.stopPropagation(); setRerunTarget(run) }}
                className="px-2 py-1 rounded-lg text-xs font-semibold cursor-pointer bg-surface-raised border border-border text-text hover:border-mint hover:text-mint transition-colors"
              >
                ↺
              </button>
              <button
                type="button"
                title="Delete this run"
                onClick={(e) => { e.stopPropagation(); setDeleteTarget(run) }}
                className="px-2 py-1 rounded-lg text-xs font-semibold cursor-pointer bg-surface-raised border border-border text-danger hover:border-danger hover:brightness-110 transition-colors"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Re-run dialog */}
      <RunDialog
        open={rerunTarget !== null}
        onClose={() => setRerunTarget(null)}
        onStart={handleRerun}
        initialSeedPrompt={rerunTarget?.seed_prompt ?? ''}
        initialTags={rerunTarget?.tags ?? []}
        title="Re-run Pipeline"
        submitLabel="Start Re-run"
      />

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete this run?"
        description={`"${deleteTarget?.final_title || deleteTarget?.pipeline_name}" (${deleteTarget ? formatTime(deleteTarget.timestamp) : ''}) will be permanently deleted. All block outputs, artifacts, and timeline data will be lost.`}
        confirmLabel="Delete Run"
        confirmVariant="danger"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </>
  )
}
