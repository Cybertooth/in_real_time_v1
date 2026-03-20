interface PhoneCallCardProps {
  data: Record<string, unknown>
}

export default function PhoneCallCard({ data }: PhoneCallCardProps) {
  const caller = String(data.caller || 'Unknown')
  const receiver = String(data.receiver || 'Unknown')
  const duration = data.duration_seconds != null ? Number(data.duration_seconds) : null
  const lines = (data.lines || []) as Record<string, unknown>[]

  const formatDuration = (secs: number) => {
    const m = Math.floor(secs / 60)
    const s = secs % 60
    return m > 0 ? `${m}m ${s}s` : `${s}s`
  }

  return (
    <div className="glass-panel p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-base">📞</span>
          <span className="text-xs font-bold text-text-dim uppercase tracking-wide">
            Phone Call
          </span>
        </div>
        <div className="text-xs text-text-dim">
          {duration != null && formatDuration(duration)}
        </div>
      </div>

      <div className="flex items-center gap-2 text-sm">
        <span className="font-semibold text-mint">{caller}</span>
        <span className="text-text-dim">→</span>
        <span className="font-semibold text-text">{receiver}</span>
      </div>

      <div className="flex flex-col gap-1.5 border-t border-border pt-3">
        {lines.map((line, i) => {
          const speaker = String(line.speaker || '?')
          const text = String(line.text || '')
          const isCaller = speaker === caller
          return (
            <div key={i} className={`flex gap-2 ${isCaller ? '' : 'flex-row-reverse'}`}>
              <span
                className={`text-xs font-semibold shrink-0 pt-0.5 w-20 ${
                  isCaller ? 'text-mint text-left' : 'text-text-dim text-right'
                }`}
              >
                {speaker}
              </span>
              <span
                className={`text-sm text-text px-3 py-1.5 rounded-xl max-w-[75%] ${
                  isCaller ? 'bg-mint/10' : 'bg-surface'
                }`}
              >
                {text}
              </span>
            </div>
          )
        })}
        {lines.length === 0 && (
          <p className="text-sm text-text-dim">No transcript available.</p>
        )}
      </div>
    </div>
  )
}
