interface JournalCardProps {
  data: Record<string, unknown>
}

export default function JournalCard({ data }: JournalCardProps) {
  const title = (data.title || data.heading || '') as string
  const body = (data.body || data.content || data.text || data.entry || '') as string

  // Format body into paragraphs
  const paragraphs = typeof body === 'string'
    ? body.split(/\n\n+/).filter(Boolean)
    : [String(body)]

  return (
    <div
      className="rounded-xl p-4 border"
      style={{
        background: 'rgba(255, 248, 230, 0.05)',
        borderColor: 'rgba(255, 248, 230, 0.15)',
      }}
    >
      {title && (
        <h4
          className="text-base font-semibold mb-3"
          style={{ color: '#ffe4a0' }}
        >
          {title}
        </h4>
      )}
      <div className="flex flex-col gap-2">
        {paragraphs.map((p, i) => (
          <p
            key={i}
            className="text-sm leading-relaxed"
            style={{ color: '#e8dcc8' }}
          >
            {p}
          </p>
        ))}
      </div>
    </div>
  )
}
