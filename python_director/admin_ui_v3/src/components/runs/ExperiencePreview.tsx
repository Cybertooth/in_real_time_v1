import type { RunTimelineEntry, RunProgress } from '../../types'
import JournalCard from '../formatting/JournalCard'
import ChatBubble from '../formatting/ChatBubble'
import EmailCard from '../formatting/EmailCard'
import ReceiptCard from '../formatting/ReceiptCard'
import VoiceNoteCard from '../formatting/VoiceNoteCard'
import SocialPostCard from '../formatting/SocialPostCard'
import PhoneCallCard from '../formatting/PhoneCallCard'
import GroupChatCard from '../formatting/GroupChatCard'
import InlineImageEditor from '../formatting/InlineImageEditor'

interface ExperiencePreviewProps {
  runData?: RunProgress
  timeline?: RunTimelineEntry[]
  runId?: string
  finalOutput?: any
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
    social_post: 'Social Post',
    phone_call: 'Phone Call',
    group_chat: 'Group Chat',
  }
  const label = typeIcons[entry.event_type] || entry.event_type

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-raised text-xs text-text-dim mb-2">
      <span className="font-semibold uppercase">{label}</span>
      <span className="text-text">{entry.title}</span>
    </div>
  )
}

function renderArtifactCard(entry: RunTimelineEntry, runId: string) {
  const data = (entry.content || {}) as Record<string, unknown>
  const parts = entry.block_id.split('_')
  const index = parseInt(parts[parts.length - 1], 10) || 0

  const Editor = () => (
    <InlineImageEditor
      runId={runId}
      eventType={entry.event_type}
      index={index}
      initialPrompt={data.image_prompt as string}
      initialImageUrl={data.local_image_path as string}
      onImageUpdated={(newPath, newPrompt) => {
        data.local_image_path = newPath
        data.image_prompt = newPrompt
      }}
    />
  )

  switch (entry.event_type) {
    case 'journal':
      return <><JournalCard data={data} /><Editor /></>
    case 'chat':
      return <><ChatBubble data={data} /><Editor /></>
    case 'email':
      return <><EmailCard data={data} /><Editor /></>
    case 'receipt':
      return <><ReceiptCard data={data} /><Editor /></>
    case 'voice_note':
      return <VoiceNoteCard data={data} />
    case 'social_post':
      return <><SocialPostCard data={data} /><Editor /></>
    case 'phone_call':
      return <PhoneCallCard data={data} />
    case 'group_chat':
      return <GroupChatCard data={data} />
    default:
      return (
        <div className="text-sm text-text bg-[#111] rounded-lg p-3 whitespace-pre-wrap">
          {JSON.stringify(data, null, 2)}
        </div>
      )
  }
}

export default function ExperiencePreview({
  runData,
  timeline: directTimeline,
  runId: directRunId,
  finalOutput: directFinalOutput,
}: ExperiencePreviewProps) {
  const timeline = directTimeline || runData?.timeline
  const runId = directRunId || runData?.run_id
  const finalOutput = directFinalOutput || (runData as any)?.final_output || {}

  if (!timeline || timeline.length === 0) {
    return (
      <div className="p-6 text-text-dim text-sm">No experience data.</div>
    )
  }

  const groups = groupByDayAndTime(timeline)
  let lastDay = -1

  // Extract headline data from final_output if available
  const headlinePrompt = finalOutput.headline_image_prompt
  const headlineImageUrl = finalOutput.headline_image_path

  return (
    <div className="p-6 max-w-2xl mx-auto flex flex-col gap-4">
      {/* Global Headline Image Editor */}
      {headlinePrompt && (
        <div className="glass-panel p-4 mb-8 border border-mint/20 shadow-xl">
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-border">
            <span className="text-mint font-bold uppercase tracking-wider text-xs">Story Headline Image</span>
          </div>
          <InlineImageEditor
            runId={runId || ''}
            eventType="headline"
            index={0}
            initialPrompt={headlinePrompt}
            initialImageUrl={headlineImageUrl}
          />
        </div>
      )}

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
                <div key={ei} className="relative z-0">
                  {renderNotificationBanner(entry)}
                  <div className="glass-panel p-4">
                    {renderArtifactCard(entry, runId || '')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
