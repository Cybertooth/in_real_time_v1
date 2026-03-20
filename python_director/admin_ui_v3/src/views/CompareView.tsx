import { useState } from 'react'
import { useStore } from '../store'
import * as api from '../api'
import type { RunComparison } from '../types'
import MetricDeltas from '../components/compare/MetricDeltas'
import SideBySide from '../components/compare/SideBySide'

export default function CompareView() {
  const runSummaries = useStore((s) => s.runSummaries)
  const showToast = useStore((s) => s.showToast)

  const [baselineId, setBaselineId] = useState('')
  const [candidateId, setCandidateId] = useState('')
  const [comparison, setComparison] = useState<RunComparison | null>(null)
  const [loading, setLoading] = useState(false)

  const handleCompare = async () => {
    if (!baselineId || !candidateId) {
      showToast('Select both baseline and candidate runs', true)
      return
    }
    if (baselineId === candidateId) {
      showToast('Select two different runs', true)
      return
    }

    setLoading(true)
    try {
      const result = await api.compareRuns(baselineId, candidateId)
      setComparison(result)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Comparison failed'
      showToast(msg, true)
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    'bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none'

  return (
    <div className="p-6 flex flex-col gap-6">
      <h2 className="text-lg font-semibold text-text">Compare Runs</h2>

      <div className="flex items-end gap-4">
        <label className="flex flex-col gap-1 flex-1">
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
            Baseline Run
          </span>
          <select
            value={baselineId}
            onChange={(e) => setBaselineId(e.target.value)}
            className={inputClass}
          >
            <option value="">-- select baseline --</option>
            {runSummaries.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.pipeline_name} - {r.status} ({new Date(r.timestamp).toLocaleDateString()})
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 flex-1">
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
            Candidate Run
          </span>
          <select
            value={candidateId}
            onChange={(e) => setCandidateId(e.target.value)}
            className={inputClass}
          >
            <option value="">-- select candidate --</option>
            {runSummaries.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.pipeline_name} - {r.status} ({new Date(r.timestamp).toLocaleDateString()})
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          onClick={handleCompare}
          disabled={loading || !baselineId || !candidateId}
          className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-mint text-black hover:brightness-110 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Comparing...' : 'Compare'}
        </button>
      </div>

      {comparison && (
        <div className="flex flex-col gap-6">
          {/* Metric deltas */}
          {comparison.metrics.length > 0 && (
            <MetricDeltas metrics={comparison.metrics} />
          )}

          {/* Quality notes */}
          {comparison.quality_notes.length > 0 && (
            <div className="glass-panel p-4">
              <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-2">
                Quality Notes
              </span>
              <ul className="list-disc list-inside flex flex-col gap-1">
                {comparison.quality_notes.map((note, i) => (
                  <li key={i} className="text-sm text-text">
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Side by side */}
          <SideBySide
            baselineOutput={comparison.baseline_output}
            candidateOutput={comparison.candidate_output}
            baselineTitle={comparison.baseline_title || 'Baseline'}
            candidateTitle={comparison.candidate_title || 'Candidate'}
          />
        </div>
      )}

      {!comparison && runSummaries.length < 2 && (
        <div className="flex-1 flex items-center justify-center text-text-dim text-sm mt-12">
          You need at least two completed runs to compare.
        </div>
      )}
    </div>
  )
}
