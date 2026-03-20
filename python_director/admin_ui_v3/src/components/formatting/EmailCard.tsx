interface EmailCardProps {
  data: Record<string, unknown>
}

export default function EmailCard({ data }: EmailCardProps) {
  const from = (data.from || data.sender || '') as string
  const to = (data.to || data.recipient || '') as string
  const subject = (data.subject || '') as string
  const body = (data.body || data.content || data.text || '') as string

  return (
    <div className="rounded-xl border border-border overflow-hidden">
      {/* Header */}
      <div className="bg-surface-raised px-4 py-3 flex flex-col gap-1">
        {from && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-text-dim text-xs font-semibold w-14">From</span>
            <span className="text-text">{from}</span>
          </div>
        )}
        {to && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-text-dim text-xs font-semibold w-14">To</span>
            <span className="text-text">{to}</span>
          </div>
        )}
        {subject && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-text-dim text-xs font-semibold w-14">Subject</span>
            <span className="text-text font-medium">{subject}</span>
          </div>
        )}
      </div>

      {/* Body */}
      <div className="px-4 py-3 bg-surface">
        <p className="text-sm text-text leading-relaxed whitespace-pre-wrap">
          {String(body)}
        </p>
      </div>
    </div>
  )
}
