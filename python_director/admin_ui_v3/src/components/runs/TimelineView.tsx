import { useState } from 'react'
import type { RunTimelineEntry } from '../../types'
import Badge from '../shared/Badge'
import JournalCard from '../formatting/JournalCard'
import ChatBubble from '../formatting/ChatBubble'
import EmailCard from '../formatting/EmailCard'
import ReceiptCard from '../formatting/ReceiptCard'
import VoiceNoteCard from '../formatting/VoiceNoteCard'

interface TimelineViewProps {
  timeline: RunTimelineEntry[]
}

const eventColors: Record<string, string> = {
  journal: '#0fe6b0',
  chat: '#60a5fa',
  email: '#ffb74d',
  receipt: '#a78bfa',
  voice_note: '#f472b6',
}

function getEventColor(eventType: string): string {
  return eventColors[eventType] || '#999'
}

function renderArtifact(entry: RunTimelineEntry) {
  const data = (entry.content || {}) as Record<string, unknown>
  switch (entry.event_type) {
    case 'journal':
      return <JournalCard data={data} />
    case 'chat':
      return <ChatBubble data={data} />
    case 'email':
      return <EmailCard data={data} />
    case 'receipt':
      return <ReceiptCard data={data} />
    case 'voice_note':
      return <VoiceNoteCard data={data} />
    default:
      return (
        <div className="text-sm text-text bg-[#111] rounded-lg p-3 whitespace-pre-wrap">
          {JSON.stringify(data, null, 2)}
        </div>
      )
  }
}

export default function TimelineView({ timeline }: TimelineViewProps) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)

  if (!timeline || timeline.length === 0) {
    return (
      <div className="p-6 text-text-dim text-sm">No narrative events yet.</div>
    )
  }

  return (
    <div className="p-6 relative">
      {/* Connecting line */}
      <div className="absolute left-[38px] top-8 bottom-8 w-px bg-border" />

      <div className="flex flex-col gap-4">
        {timeline.map((entry, idx) => {
          const color = getEventColor(entry.event_type)
          const isExpanded = expandedIdx === idx

          return (
            <div key={idx} className="flex gap-4 relative">
              {/* Left: time label */}
              <div className="w-[50px] flex-shrink-0 text-right pt-1">
                <span className="text-[10px] text-text-dim block leading-tight">
                  Day {entry.story_day}
                </span>
                <span className="text-[10px] text-text-dim block leading-tight">
                  {entry.story_time}
                </span>
              </div>

              {/* Dot */}
              <div className="flex-shrink-0 pt-2 relative z-10">
                <span
                  className="w-3 h-3 rounded-full block"
                  style={{
                    backgroundColor: color,
                    boxShadow: `0 0 6px ${color}60`,
                  }}
                />
              </div>

              {/* Right: card */}
              <div className="flex-1 min-w-0">
                <button
                  type="button"
                  onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                  className="w-full text-left p-3 rounded-xl bg-surface border border-border hover:bg-surface-raised transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-text">
                      {entry.title}
                    </span>
                    <Badge variant="default">{entry.event_type}</Badge>
                  </div>
                  {!isExpanded && entry.content && (
                    <p className="text-xs text-text-dim truncate">
                      {typeof entry.content === 'object'
                        ? (entry.content as Record<string, unknown>).body as string ||
                          (entry.content as Record<string, unknown>).transcript as string ||
                          (entry.content as Record<string, unknown>).subject as string ||
                          JSON.stringify(entry.content).slice(0, 80)
                        : String(entry.content).slice(0, 80)}
                    </p>
                  )}
                </button>

                {isExpanded && (
                  <div className="mt-2">{renderArtifact(entry)}</div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
