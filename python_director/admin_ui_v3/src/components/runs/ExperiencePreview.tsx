import type { RunTimelineEntry } from '../../types'
import JournalCard from '../formatting/JournalCard'
import ChatBubble from '../formatting/ChatBubble'
import EmailCard from '../formatting/EmailCard'
import ReceiptCard from '../formatting/ReceiptCard'
import VoiceNoteCard from '../formatting/VoiceNoteCard'

interface ExperiencePreviewProps {
  timeline: RunTimelineEntry[]
}

interface TimeGroup {
  storyDay: number
  storyTime: string
  entries: RunTimelineEntry[]
}

function groupByDayAndTime(timeline: RunTimelineEntry[]): TimeGroup[] {
  const groups: TimeGroup[] = []
  let currentGroup: TimeGroup | null = null

  for (const entry of timeline) {
    if (
      !currentGroup ||
      currentGroup.storyDay !== entry.story_day ||
      currentGroup.storyTime !== entry.story_time
    ) {
      currentGroup = {
        storyDay: entry.story_day,
        storyTime: entry.story_time,
        entries: [],
      }
      groups.push(currentGroup)
    }
    currentGroup.entries.push(entry)
  }

  return groups
}

function renderNotificationBanner(entry: RunTimelineEntry) {
  const typeIcons: Record<string, string> = {
    journal: 'Journal',
    chat: 'Message',
    email: 'Email',
    receipt: 'Receipt',
    voice_note: 'Voice Note',
  }
  const label = typeIcons[entry.event_type] || entry.event_type

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-raised text-xs text-text-dim mb-2">
      <span className="font-semibold uppercase">{label}</span>
      <span className="text-text">{entry.title}</span>
    </div>
  )
}

function renderArtifactCard(entry: RunTimelineEntry) {
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

export default function ExperiencePreview({ timeline }: ExperiencePreviewProps) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="p-6 text-text-dim text-sm">No experience data.</div>
    )
  }

  const groups = groupByDayAndTime(timeline)
  let lastDay = -1

  return (
    <div className="p-6 max-w-2xl mx-auto flex flex-col gap-4">
      {groups.map((group, gi) => {
        const showDaySeparator = group.storyDay !== lastDay
        lastDay = group.storyDay

        return (
          <div key={gi}>
            {showDaySeparator && (
              <div className="flex items-center gap-3 my-4">
                <div className="flex-1 h-px bg-border" />
                <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
                  Day {group.storyDay}
                </span>
                <div className="flex-1 h-px bg-border" />
              </div>
            )}

            <div className="mb-2">
              <span className="text-text-dim text-xs font-medium">
                {group.storyTime}
              </span>
            </div>

            <div className="flex flex-col gap-3">
              {group.entries.map((entry, ei) => (
                <div key={ei}>
                  {renderNotificationBanner(entry)}
                  {renderArtifactCard(entry)}
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
