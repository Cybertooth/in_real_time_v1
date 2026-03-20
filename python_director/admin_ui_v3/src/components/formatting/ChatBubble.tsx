interface ChatBubbleProps {
  data: Record<string, unknown>
}

export default function ChatBubble({ data }: ChatBubbleProps) {
  const sender = (data.sender || data.from || data.name || 'Unknown') as string
  const body = (data.body || data.message || data.content || data.text || '') as string
  const isProtagonist = !!(data.isProtagonist ?? data.is_protagonist ?? data.is_user)

  return (
    <div className={`flex ${isProtagonist ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isProtagonist
            ? 'bg-mint-soft border border-mint/20 rounded-br-sm'
            : 'bg-surface border border-border rounded-bl-sm'
        }`}
      >
        <span
          className={`text-xs font-semibold block mb-1 ${
            isProtagonist ? 'text-mint' : 'text-text-dim'
          }`}
        >
          {sender}
        </span>
        <p className="text-sm text-text leading-relaxed">{String(body)}</p>
      </div>
    </div>
  )
}
