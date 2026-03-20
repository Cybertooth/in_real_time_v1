import type { MetricDelta } from '../../types'

interface MetricDeltasProps {
  metrics: MetricDelta[]
}

export default function MetricDeltas({ metrics }: MetricDeltasProps) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {metrics.map((m) => {
        const isPositive = m.delta > 0
        const isNeutral = m.delta === 0
        const deltaColor = isNeutral
          ? 'text-text-dim'
          : isPositive
            ? 'text-mint'
            : 'text-danger'
        const deltaPrefix = isPositive ? '+' : ''

        return (
          <div
            key={m.label}
            className="glass-panel p-4 flex flex-col gap-1"
          >
            <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
              {m.label}
            </span>
            <span className="text-2xl font-semibold text-mint">
              {typeof m.candidate === 'number'
                ? m.candidate % 1 === 0
                  ? m.candidate.toLocaleString()
                  : m.candidate.toFixed(2)
                : m.candidate}
            </span>
            <span className={`text-xs ${deltaColor}`}>
              vs {typeof m.baseline === 'number'
                ? m.baseline % 1 === 0
                  ? m.baseline.toLocaleString()
                  : m.baseline.toFixed(2)
                : m.baseline}{' '}
              ({deltaPrefix}
              {typeof m.delta === 'number'
                ? m.delta % 1 === 0
                  ? m.delta.toLocaleString()
                  : m.delta.toFixed(2)
                : m.delta}
              )
            </span>
          </div>
        )
      })}
    </div>
  )
}
