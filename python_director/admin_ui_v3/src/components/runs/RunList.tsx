import { useNavigate } from 'react-router-dom'
import { useStore } from '../../store'
import StatusDot from '../shared/StatusDot'
import Badge from '../shared/Badge'

export default function RunList() {
  const runSummaries = useStore((s) => s.runSummaries)
  const activeRunId = useStore((s) => s.activeRunId)
  const activeRunProgress = useStore((s) => s.activeRunProgress)
  const navigate = useNavigate()

  const statusVariant = (status: string) => {
    switch (status) {
      case 'succeeded':
        return 'success' as const
      case 'failed':
        return 'error' as const
      case 'running':
        return 'warning' as const
      default:
        return 'default' as const
    }
  }

  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts)
      return d.toLocaleString()
    } catch {
      return ts
    }
  }

  return (
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
          {/* Progress bar */}
          <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
            <div
              className="h-full bg-mint rounded-full transition-all duration-500"
              style={{
                width: `${
                  activeRunProgress.block_count > 0
                    ? (Object.values(activeRunProgress.block_traces).filter(
                        (t) =>
                          t.status === 'succeeded' || t.status === 'failed',
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

      {/* Historical runs */}
      {runSummaries.length === 0 && !activeRunId && (
        <p className="text-text-dim text-sm p-2">
          No runs yet. Start a dry run from the Pipeline Editor.
        </p>
      )}

      {runSummaries.map((run) => (
        <button
          key={run.run_id}
          type="button"
          onClick={() => navigate(`/runs/${run.run_id}/blocks`)}
          className="w-full text-left p-3 rounded-xl bg-surface border border-border cursor-pointer hover:bg-surface-raised transition-colors"
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-text-dim">{formatTime(run.timestamp)}</span>
            <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
          </div>
          <div className="text-sm font-medium text-text mb-1">
            {run.pipeline_name}
          </div>
          <div className="flex items-center gap-3 text-xs text-text-dim">
            {run.final_metrics?.quality_score !== undefined && (
              <span>
                Quality:{' '}
                <span className="text-mint">
                  {run.final_metrics.quality_score.toFixed(1)}
                </span>
              </span>
            )}
            {run.final_metrics?.total_words !== undefined && (
              <span>
                Words:{' '}
                <span className="text-text">
                  {run.final_metrics.total_words.toLocaleString()}
                </span>
              </span>
            )}
            <span>{run.block_count} blocks</span>
          </div>
        </button>
      ))}
    </div>
  )
}
