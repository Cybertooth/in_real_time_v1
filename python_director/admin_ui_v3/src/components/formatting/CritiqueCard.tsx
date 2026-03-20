interface CritiqueCardProps {
  data: Record<string, unknown>
}

export default function CritiqueCard({ data }: CritiqueCardProps) {
  const strengths = (data.strengths || []) as string[]
  const weaknesses = (data.weaknesses || []) as string[]
  const actionable = (data.actionable_items ||
    data.actionable ||
    data.suggestions ||
    data.recommendations ||
    []) as string[]

  return (
    <div className="glass-panel p-4 flex flex-col gap-4">
      {/* Strengths */}
      {strengths.length > 0 && (
        <div>
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-2">
            Strengths
          </span>
          <ul className="flex flex-col gap-1">
            {strengths.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="text-mint flex-shrink-0 mt-0.5">&#9679;</span>
                <span className="text-text">{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Weaknesses */}
      {weaknesses.length > 0 && (
        <div>
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-2">
            Weaknesses
          </span>
          <ul className="flex flex-col gap-1">
            {weaknesses.map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="text-danger flex-shrink-0 mt-0.5">&#9679;</span>
                <span className="text-text">{w}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Actionable items */}
      {actionable.length > 0 && (
        <div>
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-2">
            Actionable Items
          </span>
          <ul className="flex flex-col gap-1">
            {actionable.map((a, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="text-amber flex-shrink-0 mt-0.5">&#9679;</span>
                <span className="text-text">{a}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {strengths.length === 0 &&
        weaknesses.length === 0 &&
        actionable.length === 0 && (
          <p className="text-sm text-text-dim">No critique data available.</p>
        )}
    </div>
  )
}
