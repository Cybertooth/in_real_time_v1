const PLATFORM_ICONS: Record<string, string> = {
  whatsapp: '💬',
  telegram: '✈️',
  imessage: '💭',
}

interface GroupChatCardProps {
  data: Record<string, unknown>
}

export default function GroupChatCard({ data }: GroupChatCardProps) {
  const platform = String(data.platform || 'chat').toLowerCase()
  const groupName = String(data.group_name || 'Group Chat')
  const members = (data.members || []) as string[]
  const messages = (data.messages || []) as Record<string, unknown>[]
  const icon = PLATFORM_ICONS[platform] ?? '💬'

  // Generate a stable color per sender
  const senderColors = ['text-mint', 'text-amber', 'text-[#a78bfa]', 'text-[#f87171]', 'text-[#38bdf8]']
  const colorMap: Record<string, string> = {}
  const allSenders = [...new Set(messages.map((m) => String(m.sender || '?')))]
  allSenders.forEach((s, i) => {
    colorMap[s] = senderColors[i % senderColors.length]
  })

  return (
    <div className="glass-panel p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-base">{icon}</span>
          <span className="text-xs font-bold text-text-dim uppercase tracking-wide">
            {platform === 'imessage' ? 'iMessage' : platform.charAt(0).toUpperCase() + platform.slice(1)} Group
          </span>
        </div>
        <div className="text-xs text-text-dim">
          {messages.length} messages
        </div>
      </div>

      <div>
        <div className="text-sm font-semibold text-text">{groupName}</div>
        {members.length > 0 && (
          <div className="text-xs text-text-dim mt-0.5">
            {members.join(', ')}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2 border-t border-border pt-3">
        {messages.map((msg, i) => {
          const sender = String(msg.sender || '?')
          const text = String(msg.text || '')
          const color = colorMap[sender] ?? 'text-text-dim'
          return (
            <div key={i} className="flex flex-col gap-0.5">
              <span className={`text-xs font-semibold ${color}`}>{sender}</span>
              <div className="bg-surface rounded-lg px-3 py-2 text-sm text-text max-w-[85%]">
                {text}
              </div>
            </div>
          )
        })}
        {messages.length === 0 && (
          <p className="text-sm text-text-dim">No messages.</p>
        )}
      </div>
    </div>
  )
}
