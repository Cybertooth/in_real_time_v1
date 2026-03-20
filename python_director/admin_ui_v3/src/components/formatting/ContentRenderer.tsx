import { useState } from 'react'
import StoryPlanCard from './StoryPlanCard'
import CritiqueCard from './CritiqueCard'
import JournalCard from './JournalCard'
import ChatBubble from './ChatBubble'
import EmailCard from './EmailCard'
import ReceiptCard from './ReceiptCard'
import VoiceNoteCard from './VoiceNoteCard'
import SocialPostCard from './SocialPostCard'
import PhoneCallCard from './PhoneCallCard'
import GroupChatCard from './GroupChatCard'
import RawJsonViewer from './RawJsonViewer'
import Badge from '../shared/Badge'

interface ContentRendererProps {
  output: unknown
  schemaName: string | null
}

export default function ContentRenderer({
  output,
  schemaName,
}: ContentRendererProps) {
  const [showRaw, setShowRaw] = useState(false)

  const renderContent = () => {
    if (output === null || output === undefined) {
      return <p className="text-text-dim text-sm">No output</p>
    }

    const data =
      typeof output === 'object' && output !== null
        ? (output as Record<string, unknown>)
        : null

    switch (schemaName) {
      case 'StoryPlan':
        return data ? <StoryPlanCard data={data} /> : null

      case 'BrainstormCritique':
      case 'StoryCritique':
        return data ? <CritiqueCard data={data} /> : null

      case 'SceneList':
        return data ? <SceneListInline data={data} /> : null

      case 'ContinuityAudit':
        return data ? <ContinuityAuditInline data={data} /> : null

      case 'DropPlan':
        return data ? <DropPlanInline data={data} /> : null

      case 'StoryGenerated':
        return data ? <StoryGeneratedInline data={data} /> : null

      default:
        if (typeof output === 'string') {
          return (
            <div className="text-sm text-text bg-[#111] rounded-lg p-3 whitespace-pre-wrap">
              {output}
            </div>
          )
        }
        if (data) {
          return <RawJsonViewer data={data} label="Output" />
        }
        return (
          <div className="text-sm text-text bg-[#111] rounded-lg p-3 whitespace-pre-wrap">
            {String(output)}
          </div>
        )
    }
  }

  return (
    <div>
      {renderContent()}
      <div className="mt-2">
        <button
          type="button"
          onClick={() => setShowRaw(!showRaw)}
          className="text-xs text-text-dim hover:text-text cursor-pointer bg-transparent border-none"
        >
          {showRaw ? 'Hide Raw' : 'View Raw'}
        </button>
        {showRaw && <RawJsonViewer data={output} label="Raw Output" />}
      </div>
    </div>
  )
}

function SceneListInline({ data }: { data: Record<string, unknown> }) {
  const scenes = (data.scenes || data.scene_list || []) as Record<string, unknown>[]

  return (
    <div className="flex flex-col gap-2">
      {scenes.map((scene, i) => (
        <div key={i} className="glass-panel p-3">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="info">Scene {i + 1}</Badge>
            {scene.title != null && (
              <span className="text-sm font-medium text-text">
                {String(scene.title)}
              </span>
            )}
          </div>
          {scene.description != null && (
            <p className="text-sm text-text-dim">{String(scene.description)}</p>
          )}
          {scene.characters != null && (
            <p className="text-xs text-text-dim mt-1">
              Characters: {Array.isArray(scene.characters) ? (scene.characters as string[]).join(', ') : String(scene.characters)}
            </p>
          )}
        </div>
      ))}
      {scenes.length === 0 && (
        <p className="text-sm text-text-dim">No scenes</p>
      )}
    </div>
  )
}

function ContinuityAuditInline({ data }: { data: Record<string, unknown> }) {
  const issues = (data.issues || data.continuity_issues || []) as Record<string, unknown>[]
  const passed = data.passed ?? data.all_clear

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <Badge variant={passed ? 'success' : 'warning'}>
          {passed ? 'Passed' : 'Issues Found'}
        </Badge>
      </div>
      {issues.map((issue, i) => (
        <div key={i} className="glass-panel p-3">
          <span className="text-sm font-medium text-amber">
            {String(issue.type || issue.category || `Issue ${i + 1}`)}
          </span>
          <p className="text-sm text-text mt-1">
            {String(issue.description || issue.detail || '')}
          </p>
        </div>
      ))}
      {issues.length === 0 && !!passed && (
        <p className="text-sm text-mint">No continuity issues detected.</p>
      )}
    </div>
  )
}

function DropPlanInline({ data }: { data: Record<string, unknown> }) {
  const events = (data.events || data.drops || data.plan || []) as Record<string, unknown>[]

  return (
    <div className="flex flex-col gap-2">
      {events.map((event, i) => (
        <div key={i} className="glass-panel p-3">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="default">
              {String(event.event_type || event.type || 'event')}
            </Badge>
            <span className="text-sm font-medium text-text">
              {String(event.title || event.name || `Event ${i + 1}`)}
            </span>
            {event.story_day !== undefined && (
              <span className="text-xs text-text-dim">
                Day {String(event.story_day)}, {String(event.story_time || '')}
              </span>
            )}
          </div>
          {event.description != null && (
            <p className="text-sm text-text-dim">{String(event.description)}</p>
          )}
        </div>
      ))}
      {events.length === 0 && (
        <p className="text-sm text-text-dim">No events planned</p>
      )}
    </div>
  )
}

function SectionHeader({ label, count }: { label: string; count: number }) {
  if (count === 0) return null
  return (
    <div className="flex items-center gap-2 mt-4 mb-1">
      <span className="text-xs font-bold text-text-dim uppercase tracking-widest">{label}</span>
      <span className="text-xs text-text-dim bg-surface px-1.5 py-0.5 rounded-full">{count}</span>
    </div>
  )
}

function StoryGeneratedInline({ data }: { data: Record<string, unknown> }) {
  const journals = (data.journals || []) as Record<string, unknown>[]
  const chats = (data.chats || []) as Record<string, unknown>[]
  const emails = (data.emails || []) as Record<string, unknown>[]
  const receipts = (data.receipts || []) as Record<string, unknown>[]
  const voiceNotes = (data.voice_notes || []) as Record<string, unknown>[]
  const socialPosts = (data.social_posts || []) as Record<string, unknown>[]
  const phoneCalls = (data.phone_calls || []) as Record<string, unknown>[]
  const groupChats = (data.group_chats || []) as Record<string, unknown>[]

  const total = journals.length + chats.length + emails.length + receipts.length
    + voiceNotes.length + socialPosts.length + phoneCalls.length + groupChats.length

  if (total === 0) {
    if (data.content || data.text || data.body) {
      return (
        <div className="text-sm text-text bg-[#111] rounded-lg p-3 whitespace-pre-wrap">
          {String(data.content || data.text || data.body)}
        </div>
      )
    }
    return <RawJsonViewer data={data} label="Story Output" />
  }

  return (
    <div className="flex flex-col gap-3">
      {data.story_title != null && (
        <div className="text-base font-semibold text-mint mb-1">
          {String(data.story_title)}
        </div>
      )}

      <SectionHeader label="Journals" count={journals.length} />
      {journals.map((j, i) => <JournalCard key={`j${i}`} data={j} />)}

      <SectionHeader label="Chats" count={chats.length} />
      {chats.map((c, i) => <ChatBubble key={`c${i}`} data={c} />)}

      <SectionHeader label="Emails" count={emails.length} />
      {emails.map((e, i) => <EmailCard key={`e${i}`} data={e} />)}

      <SectionHeader label="Receipts" count={receipts.length} />
      {receipts.map((r, i) => <ReceiptCard key={`r${i}`} data={r} />)}

      <SectionHeader label="Voice Notes" count={voiceNotes.length} />
      {voiceNotes.map((v, i) => <VoiceNoteCard key={`v${i}`} data={v} />)}

      <SectionHeader label="Social Posts" count={socialPosts.length} />
      {socialPosts.map((sp, i) => <SocialPostCard key={`sp${i}`} data={sp} />)}

      <SectionHeader label="Phone Calls" count={phoneCalls.length} />
      {phoneCalls.map((pc, i) => <PhoneCallCard key={`pc${i}`} data={pc} />)}

      <SectionHeader label="Group Chats" count={groupChats.length} />
      {groupChats.map((gc, i) => <GroupChatCard key={`gc${i}`} data={gc} />)}
    </div>
  )
}
