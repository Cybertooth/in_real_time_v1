interface VoiceNoteCardProps {
  data: Record<string, unknown>
}

export default function VoiceNoteCard({ data }: VoiceNoteCardProps) {
  const speaker = (data.speaker || data.from || data.sender || '') as string
  const transcript = (data.transcript || data.body || data.content || data.text || '') as string
  const duration = (data.duration || data.length || '') as string

  return (
    <div
      className="rounded-xl px-4 py-3 border"
      style={{
        background: 'rgba(244, 114, 182, 0.06)',
        borderColor: 'rgba(244, 114, 182, 0.2)',
      }}
    >
      {/* Speaker label + waveform decoration */}
      <div className="flex items-center gap-2 mb-2">
        {speaker && (
          <span className="text-sm font-semibold" style={{ color: '#f472b6' }}>
            {speaker}
          </span>
        )}
        {/* Waveform decoration */}
        <div className="flex items-center gap-0.5 flex-1">
          {Array.from({ length: 20 }, (_, i) => {
            const h = 4 + Math.sin(i * 0.8) * 6 + Math.random() * 4
            return (
              <div
                key={i}
                className="rounded-full"
                style={{
                  width: '2px',
                  height: `${h}px`,
                  backgroundColor: 'rgba(244, 114, 182, 0.4)',
                }}
              />
            )
          })}
        </div>
        {duration && (
          <span className="text-xs text-text-dim">{duration}</span>
        )}
      </div>

      {/* Transcript */}
      {transcript && (
        <p className="text-sm text-text leading-relaxed whitespace-pre-wrap">
          {String(transcript)}
        </p>
      )}
    </div>
  )
}
