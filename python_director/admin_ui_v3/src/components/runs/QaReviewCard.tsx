import Badge from '../shared/Badge'
import type { StoryQAFinding, StoryQAReport } from '../../types'

interface QaReviewCardProps {
  report: StoryQAReport | null | undefined
  generating: boolean
  canGenerate: boolean
  onGenerate: () => void
}

function statusVariant(status: StoryQAReport['status']) {
  if (status === 'strong') return 'success' as const
  if (status === 'warning') return 'warning' as const
  return 'error' as const
}

function passVariant(status: 'pass' | 'warning' | 'fail') {
  if (status === 'pass') return 'success' as const
  if (status === 'warning') return 'warning' as const
  return 'error' as const
}

function severityVariant(severity: StoryQAFinding['severity']) {
  if (severity === 'critical' || severity === 'high') return 'error' as const
  if (severity === 'medium') return 'warning' as const
  return 'default' as const
}

export default function QaReviewCard({
  report,
  generating,
  canGenerate,
  onGenerate,
}: QaReviewCardProps) {
  return (
    <section className="glass-panel p-4 flex flex-col gap-4">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-text-dim">QA Review</div>
          <h3 className="text-lg font-semibold text-text mt-1">Narrative quality passes</h3>
          <p className="text-sm text-text-dim mt-1 max-w-2xl">
            Aggregates structured findings for opening hook, continuity, character voice, redundancy, diversity, and schema correctness.
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
          {generating ? 'Running...' : report ? 'Re-run QA' : 'Run QA Review'}
        </button>
      </div>

      {!report && (
        <div className="rounded-2xl border border-border bg-surface px-4 py-5 text-sm text-text-dim">
          Generate QA to surface structured pass/fail findings before reviewers upload or publish the story.
        </div>
      )}

      {report && (
        <>
          <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
            <div className="rounded-2xl border border-border bg-surface p-4">
              <div className="text-xs uppercase tracking-[0.2em] text-text-dim">Overall Score</div>
              <div className="mt-2 flex items-end gap-3">
                <div className="text-5xl font-semibold text-text">{report.score}</div>
                <div className="text-sm text-text-dim pb-1">/ 100</div>
              </div>
              <div className="mt-3 flex items-center gap-2">
                <Badge variant={statusVariant(report.status)}>{report.status}</Badge>
                <span className="text-xs text-text-dim">{report.evaluation_mode}</span>
              </div>
              {report.blockers.length > 0 && (
                <div className="mt-4 flex flex-col gap-2">
                  {report.blockers.map((blocker) => (
                    <div key={blocker} className="rounded-xl border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-text">
                      {blocker}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-border bg-surface p-4">
              <div className="text-sm font-semibold text-text">Pass Breakdown</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {report.passes.map((pass) => (
                  <div key={pass.pass_name} className="rounded-2xl border border-border px-3 py-2 bg-black/20">
                    <div className="flex items-center gap-2">
                      <Badge variant={passVariant(pass.status)}>{pass.status}</Badge>
                      <span className="text-sm font-medium text-text">{pass.label}</span>
                    </div>
                    <div className="mt-2 text-xs text-text-dim">{pass.score} / 100</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <div className="rounded-2xl border border-border bg-surface p-4">
              <div className="text-sm font-semibold text-text">Top Findings</div>
              <div className="mt-3 flex flex-col gap-3">
                {report.findings.length > 0 ? report.findings.slice(0, 8).map((finding, index) => (
                  <div key={`${finding.category}-${index}`} className="rounded-xl border border-border bg-black/20 p-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant={severityVariant(finding.severity)}>{finding.severity}</Badge>
                      <span className="text-xs uppercase tracking-wide text-text-dim">{finding.pass_name || finding.category}</span>
                    </div>
                    <div className="mt-2 text-sm text-text">{finding.message}</div>
                    {finding.recommendation && (
                      <div className="mt-2 text-sm text-text-dim">{finding.recommendation}</div>
                    )}
                    {finding.artifact_refs.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {finding.artifact_refs.slice(0, 3).map((artifact) => (
                          <span key={artifact.artifact_id} className="rounded-full border border-border px-2 py-1 text-[11px] text-text-dim">
                            {artifact.title}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )) : (
                  <div className="text-sm text-text-dim">No QA findings were generated.</div>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-4">
              <div className="text-sm font-semibold text-text">Recommended Fixes</div>
              <div className="mt-3 flex flex-col gap-2">
                {report.recommended_fixes.length > 0 ? report.recommended_fixes.map((fix) => (
                  <div key={fix} className="rounded-xl border border-mint/20 bg-mint-soft px-3 py-2 text-sm text-text">
                    {fix}
                  </div>
                )) : (
                  <div className="text-sm text-text-dim">No additional fixes suggested.</div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  )
}
