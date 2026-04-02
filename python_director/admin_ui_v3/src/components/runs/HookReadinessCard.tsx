import Badge from '../shared/Badge'
import type { HookSimulationReport } from '../../types'

interface HookReadinessCardProps {
  report: HookSimulationReport | null | undefined
  generating: boolean
  canGenerate: boolean
  onGenerate: () => void
}

function statusVariant(status: HookSimulationReport['status']) {
  if (status === 'ready') return 'success' as const
  if (status === 'caution') return 'warning' as const
  return 'error' as const
}

function metricLabel(key: keyof HookSimulationReport['scores']) {
  return key.replaceAll('_', ' ')
}

export default function HookReadinessCard({
  report,
  generating,
  canGenerate,
  onGenerate,
}: HookReadinessCardProps) {
  return (
    <section className="glass-panel p-4 flex flex-col gap-4">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-text-dim">Hook Readiness</div>
          <h3 className="text-lg font-semibold text-text mt-1">First-session tension simulator</h3>
          <p className="text-sm text-text-dim mt-1 max-w-2xl">
            Predicts whether the first 24 hours and first 10 artifacts are strong enough to hook a new user.
          </p>
        </div>
        <button
          type="button"
          onClick={onGenerate}
          disabled={!canGenerate || generating}
          className={`px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
            !canGenerate || generating
              ? 'bg-surface text-text-dim border border-border cursor-not-allowed opacity-60'
              : 'bg-mint text-black hover:brightness-110 cursor-pointer'
          }`}
        >
          {generating ? 'Running...' : report ? 'Re-run Hook Review' : 'Run Hook Review'}
        </button>
      </div>

      {!report && (
        <div className="rounded-2xl border border-border bg-surface px-4 py-5 text-sm text-text-dim">
          Generate the hook simulation after a completed run to get opening warnings, dead-zone detection, and concrete pacing fixes.
        </div>
      )}

      {report && (
        <>
          <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
            <div className="rounded-2xl border border-border bg-surface p-4">
              <div className="text-xs uppercase tracking-[0.2em] text-text-dim">Overall Score</div>
              <div className="mt-2 flex items-end gap-3">
                <div className="text-5xl font-semibold text-text">{report.overall_hook_score.toFixed(1)}</div>
                <div className="text-sm text-text-dim pb-1">/ 10</div>
              </div>
              <div className="mt-3 flex items-center gap-2">
                <Badge variant={statusVariant(report.status)}>{report.status.replaceAll('_', ' ')}</Badge>
                <span className="text-xs text-text-dim">{report.evaluation_mode}</span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl bg-black/20 p-3">
                  <div className="text-xs uppercase tracking-wide text-text-dim">Artifacts / 24h</div>
                  <div className="mt-1 text-xl font-semibold">{report.deterministic_signals.artifact_count_first_24h}</div>
                </div>
                <div className="rounded-xl bg-black/20 p-3">
                  <div className="text-xs uppercase tracking-wide text-text-dim">Max Gap</div>
                  <div className="mt-1 text-xl font-semibold">{report.deterministic_signals.max_gap_minutes_first_24h}m</div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-4">
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {(Object.entries(report.scores) as [keyof HookSimulationReport['scores'], number][]).map(([key, value]) => (
                  <div key={key} className="rounded-xl bg-black/20 px-3 py-2">
                    <div className="text-[11px] uppercase tracking-wide text-text-dim">{metricLabel(key)}</div>
                    <div className="mt-1 text-xl font-semibold text-text">{value.toFixed(1)}</div>
                  </div>
                ))}
              </div>
              {report.llm_summary && (
                <p className="mt-4 text-sm text-text-dim">{report.llm_summary}</p>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-surface p-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div>
                <div className="text-sm font-semibold text-text">Opening Beat Timeline</div>
                <div className="text-xs text-text-dim">Dead zones are shaded red, stronger beats sit higher and brighter.</div>
              </div>
              <div className="text-xs text-text-dim">
                Evidence types: {report.deterministic_signals.evidence_artifact_types.length > 0 ? report.deterministic_signals.evidence_artifact_types.join(', ') : 'none'}
              </div>
            </div>
            <div className="relative mt-6 h-20 rounded-2xl border border-border bg-black/20 overflow-hidden">
              {report.deterministic_signals.dead_zones.map((zone) => (
                <div
                  key={`${zone.start_offset_minutes}-${zone.end_offset_minutes}`}
                  className="absolute inset-y-0 bg-danger/20 border-x border-danger/20"
                  style={{
                    left: `${(zone.start_offset_minutes / 1440) * 100}%`,
                    width: `${((zone.end_offset_minutes - zone.start_offset_minutes) / 1440) * 100}%`,
                  }}
                  title={zone.label}
                />
              ))}
              <div className="absolute inset-x-0 top-1/2 border-t border-border/80" />
              {report.timeline_beats.map((beat) => (
                <div
                  key={beat.artifact_id}
                  className="absolute -translate-x-1/2"
                  style={{
                    left: `${(beat.time_offset_minutes / 1440) * 100}%`,
                    top: `${Math.max(6, 60 - beat.tension_score * 4)}px`,
                  }}
                  title={`${beat.title} • ${beat.tension_score.toFixed(1)} • ${beat.note}`}
                >
                  <div className="h-3 w-3 rounded-full bg-mint shadow-[0_0_14px_rgba(15,230,176,0.6)]" />
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <div className="rounded-2xl border border-border bg-surface p-4">
              <div className="text-sm font-semibold text-text">Warnings</div>
              <div className="mt-3 flex flex-col gap-2">
                {report.warnings.length > 0 ? report.warnings.map((warning) => (
                  <div key={warning} className="rounded-xl border border-amber/30 bg-amber-soft px-3 py-2 text-sm text-text">
                    {warning}
                  </div>
                )) : (
                  <div className="text-sm text-text-dim">No major hook warnings surfaced.</div>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-4">
              <div className="text-sm font-semibold text-text">Recommended Actions</div>
              <div className="mt-3 flex flex-col gap-2">
                {report.recommended_actions.length > 0 ? report.recommended_actions.map((action) => (
                  <div key={action} className="rounded-xl border border-mint/20 bg-mint-soft px-3 py-2 text-sm text-text">
                    {action}
                  </div>
                )) : (
                  <div className="text-sm text-text-dim">No concrete action items were generated.</div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  )
}
