import type { RunTimelineEntry } from '../../types'
import ExperiencePreview from '../runs/ExperiencePreview'

interface SideBySideProps {
  baselineOutput: unknown
  candidateOutput: unknown
  baselineTitle: string
  candidateTitle: string
}

function parseOutputToTimeline(output: unknown): RunTimelineEntry[] {
  if (!output) return []

  // If it's already an array of timeline entries
  if (Array.isArray(output)) {
    return output.map((item) => ({
      block_id: item.block_id || '',
      event_type: item.event_type || 'journal',
      story_day: item.story_day || 1,
      story_time: item.story_time || '',
      title: item.title || '',
      content: item.content || null,
    }))
  }

  // If it's an object with a timeline property
  if (typeof output === 'object' && output !== null) {
    const obj = output as Record<string, unknown>
    if (Array.isArray(obj.timeline)) {
      return parseOutputToTimeline(obj.timeline)
    }
    if (Array.isArray(obj.events)) {
      return parseOutputToTimeline(obj.events)
    }
    // If it's a flat story output, wrap it
    if (obj.title || obj.body || obj.content) {
      return [
        {
          block_id: '',
          event_type: 'journal',
          story_day: 1,
          story_time: '',
          title: (obj.title as string) || 'Output',
          content: obj as Record<string, unknown>,
        },
      ]
    }
  }

  // If it's a string, wrap it
  if (typeof output === 'string') {
    return [
      {
        block_id: '',
        event_type: 'journal',
        story_day: 1,
        story_time: '',
        title: 'Output',
        content: { body: output },
      },
    ]
  }

  return []
}

export default function SideBySide({
  baselineOutput,
  candidateOutput,
  baselineTitle,
  candidateTitle,
}: SideBySideProps) {
  const baselineTimeline = parseOutputToTimeline(baselineOutput)
  const candidateTimeline = parseOutputToTimeline(candidateOutput)

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="flex flex-col">
        <div className="px-4 py-2 bg-surface border border-border rounded-t-xl">
          <span className="text-sm font-semibold text-text">{baselineTitle}</span>
        </div>
        <div className="border border-t-0 border-border rounded-b-xl overflow-hidden">
          <ExperiencePreview timeline={baselineTimeline} finalOutput={baselineOutput} />
        </div>
      </div>

      <div className="flex flex-col">
        <div className="px-4 py-2 bg-surface border border-border rounded-t-xl">
          <span className="text-sm font-semibold text-mint">{candidateTitle}</span>
        </div>
        <div className="border border-t-0 border-border rounded-b-xl overflow-hidden">
          <ExperiencePreview timeline={candidateTimeline} finalOutput={candidateOutput} />
        </div>
      </div>
    </div>
  )
}
