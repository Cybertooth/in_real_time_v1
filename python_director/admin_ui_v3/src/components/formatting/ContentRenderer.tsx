import { useState } from 'react'
import StoryPlanCard from './StoryPlanCard'
import CritiqueCard from './CritiqueCard'
import JournalCard from './JournalCard'
import ChatBubble from './ChatBubble'
import EmailCard from './EmailCard'
import ReceiptCard from './ReceiptCard'
import VoiceNoteCard from './VoiceNoteCard'
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

function StoryGeneratedInline({ data }: { data: Record<string, unknown> }) {
  const events = (data.events || data.timeline || []) as Record<string, unknown>[]

  if (events.length === 0) {
    // Fallback: render as formatted text
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
      {events.map((event, i) => {
        const eventData = (event.content || event) as Record<string, unknown>
        const eventType = String(event.event_type || event.type || 'journal')

        switch (eventType) {
          case 'journal':
            return <JournalCard key={i} data={eventData} />
          case 'chat':
            return <ChatBubble key={i} data={eventData} />
          case 'email':
            return <EmailCard key={i} data={eventData} />
          case 'receipt':
            return <ReceiptCard key={i} data={eventData} />
          case 'voice_note':
            return <VoiceNoteCard key={i} data={eventData} />
          default:
            return (
              <div key={i} className="glass-panel p-3">
                <span className="text-xs text-text-dim uppercase font-semibold">
                  {eventType}
                </span>
                <p className="text-sm text-text mt-1">
                  {String(eventData.body || eventData.content || JSON.stringify(eventData))}
                </p>
              </div>
            )
        }
      })}
    </div>
  )
}
