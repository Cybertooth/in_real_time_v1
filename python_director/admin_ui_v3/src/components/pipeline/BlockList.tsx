import { useStore } from '../../store'
import StatusDot from '../shared/StatusDot'

export default function BlockList() {
  const pipeline = useStore((s) => s.pipeline)
  const selectedBlockId = useStore((s) => s.selectedBlockId)
  const selectBlock = useStore((s) => s.selectBlock)
  const activeRunProgress = useStore((s) => s.liveRun)

  if (!pipeline) return null

  const blocks = pipeline.blocks

  if (blocks.length === 0) {
    return (
      <div className="glass-panel p-4">
        <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-2">
          Blocks
        </span>
        <p className="text-text-dim text-sm">Add blocks using the template rail below</p>
      </div>
    )
  }

  return (
    <div className="glass-panel p-4">
      <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-2">
        Blocks
      </span>
      <div className="flex flex-col">
        {blocks.map((block, idx) => {
          const isActive = selectedBlockId === block.id
          const trace = activeRunProgress?.block_traces?.[block.id]
          const status = trace
            ? trace.status
            : block.enabled
              ? 'pending'
              : 'skipped'

          return (
            <div key={block.id}>
              <button
                type="button"
                onClick={() => selectBlock(block.id)}
                className={`w-full text-left px-3 py-2 rounded-lg flex items-center gap-2 transition-colors cursor-pointer border ${
                  isActive
                    ? 'border-mint bg-surface-raised'
                    : 'border-transparent hover:bg-surface'
                } ${!block.enabled ? 'opacity-50' : ''}`}
              >
                <StatusDot status={status} />
                <span className="font-medium text-sm text-text truncate flex-1">
                  {block.name}
                </span>
                <span className="text-[10px] bg-surface-raised text-text-dim rounded px-1.5 py-0.5 uppercase font-semibold">
                  {block.type}
                </span>
                <span className="text-xs bg-surface-raised text-text-dim rounded px-1.5 py-0.5">
                  {block.config.provider}
                </span>
              </button>
              {idx < blocks.length - 1 && (
                <div className="flex justify-center py-0.5 text-text-dim text-xs">
                  &#8595;
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
