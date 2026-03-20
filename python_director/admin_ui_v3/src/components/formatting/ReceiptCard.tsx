interface ReceiptCardProps {
  data: Record<string, unknown>
}

export default function ReceiptCard({ data }: ReceiptCardProps) {
  const merchant = (data.merchant || data.merchant_name || data.vendor || '') as string
  const amount = data.amount as number | string | undefined
  const description = (data.description || data.memo || data.note || '') as string
  const date = (data.date || data.timestamp || '') as string

  const formatAmount = (val: number | string | undefined): string => {
    if (val === undefined || val === null) return '--'
    const num = typeof val === 'string' ? parseFloat(val) : val
    if (isNaN(num)) return String(val)
    return `$${num.toFixed(2)}`
  }

  return (
    <div
      className="rounded-xl px-4 py-3 border"
      style={{
        background: 'rgba(167, 139, 250, 0.06)',
        borderColor: 'rgba(167, 139, 250, 0.2)',
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold" style={{ color: '#a78bfa' }}>
          {merchant || 'Transaction'}
        </span>
        <span className="text-lg font-bold text-text">
          {formatAmount(amount)}
        </span>
      </div>
      {description && (
        <p className="text-sm text-text-dim">{description}</p>
      )}
      {date && (
        <p className="text-xs text-text-dim mt-1">{date}</p>
      )}
    </div>
  )
}
