const PLATFORM_STYLES: Record<string, { label: string; color: string; icon: string }> = {
  instagram: { label: 'Instagram', color: 'text-[#E1306C]', icon: '📷' },
  twitter:   { label: 'Twitter / X', color: 'text-[#1DA1F2]', icon: '🐦' },
  facebook:  { label: 'Facebook', color: 'text-[#1877F2]', icon: '👥' },
  tiktok:    { label: 'TikTok', color: 'text-[#EE1D52]', icon: '🎵' },
}

interface SocialPostCardProps {
  data: Record<string, unknown>
}

export default function SocialPostCard({ data }: SocialPostCardProps) {
  const platform = String(data.platform || 'social').toLowerCase()
  const style = PLATFORM_STYLES[platform] ?? { label: platform, color: 'text-text-dim', icon: '📱' }
  const author = String(data.author || 'Unknown')
  const handle = String(data.handle || author)
  const content = String(data.content || '')
  const likes = data.likes != null ? Number(data.likes) : null
  const comments = data.comments != null ? Number(data.comments) : null

  return (
    <div className="glass-panel p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-base">{style.icon}</span>
          <span className={`text-xs font-bold uppercase tracking-wide ${style.color}`}>
            {style.label}
          </span>
        </div>
        <div className="text-right">
          <div className="text-sm font-semibold text-text">{author}</div>
          <div className="text-xs text-text-dim">@{handle}</div>
        </div>
      </div>
      <p className="text-sm text-text whitespace-pre-wrap leading-relaxed">{content}</p>
      {(likes !== null || comments !== null) && (
        <div className="flex items-center gap-4 text-xs text-text-dim border-t border-border pt-2">
          {likes !== null && <span>❤️ {likes.toLocaleString()}</span>}
          {comments !== null && <span>💬 {comments.toLocaleString()}</span>}
        </div>
      )}
    </div>
  )
}
