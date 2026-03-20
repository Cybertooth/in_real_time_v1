import { useStore } from '../../store'
import Badge from '../shared/Badge'

export default function TemplateRail() {
  const blockTemplates = useStore((s) => s.blockTemplates)
  const addBlockFromTemplate = useStore((s) => s.addBlockFromTemplate)

  if (blockTemplates.length === 0) return null

  return (
    <div className="glass-panel p-4">
      <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-2">
        Block Templates
      </span>
      <div className="flex flex-col gap-2">
        {blockTemplates.map((template) => (
          <div
            key={template.type + template.name}
            className="flex items-center gap-2 p-2 rounded-lg bg-surface border border-border"
          >
            <Badge variant="default">{template.type}</Badge>
            <span className="text-sm text-text flex-1 truncate">{template.name}</span>
            <button
              type="button"
              onClick={() => addBlockFromTemplate(template)}
              className="px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer bg-mint-soft text-mint border border-mint/30 hover:brightness-110 transition-colors"
            >
              + Add
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
