import { useStore } from '../store'
import BlockInspector from '../components/pipeline/BlockInspector'

export default function EditorView() {
  const pipeline = useStore((s) => s.pipeline)
  const selectedBlockId = useStore((s) => s.selectedBlockId)
  const settings = useStore((s) => s.settings)

  const block = pipeline?.blocks.find((b) => b.id === selectedBlockId)

  const noApiKeys =
    settings &&
    !settings.status.gemini_configured &&
    !settings.status.openai_configured

  return (
    <div className="h-full flex flex-col">
      {/* API key warning */}
      {noApiKeys && (
        <div className="mx-6 mt-4 px-4 py-3 rounded-xl bg-amber-soft border border-amber/30 text-amber text-sm">
          No API keys configured. Open Settings to add your Gemini or OpenAI API key before running.
        </div>
      )}

      {selectedBlockId && block ? (
        <BlockInspector />
      ) : (
        <WelcomeState />
      )}
    </div>
  )
}

function WelcomeState() {
  const pipeline = useStore((s) => s.pipeline)

  if (!pipeline) {
    return (
      <div className="flex-1 flex items-center justify-center text-text-dim">
        Loading pipeline...
      </div>
    )
  }

  const totalBlocks = pipeline.blocks.length
  const enabledBlocks = pipeline.blocks.filter((b) => b.enabled).length
  const providers = new Set(pipeline.blocks.map((b) => b.config.provider))
  const types = new Set(pipeline.blocks.map((b) => b.type))

  // Build dependency summary
  const depsMap: Record<string, string[]> = {}
  for (const b of pipeline.blocks) {
    if (b.input_blocks.length > 0) {
      depsMap[b.id] = b.input_blocks
    }
  }
  const depEntries = Object.entries(depsMap)

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="max-w-md text-center flex flex-col gap-6">
        <div>
          <h2 className="text-2xl font-semibold text-text mb-2">
            {pipeline.name}
          </h2>
          <p className="text-text-dim text-sm">{pipeline.description}</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <StatCard label="Total Blocks" value={totalBlocks} />
          <StatCard label="Enabled" value={enabledBlocks} />
          <StatCard label="Providers" value={providers.size} />
          <StatCard label="Block Types" value={types.size} />
        </div>

        {depEntries.length > 0 && (
          <div className="glass-panel p-4 text-left">
            <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-2">
              Dependencies
            </span>
            <div className="flex flex-col gap-1">
              {depEntries.map(([blockId, deps]) => (
                <div key={blockId} className="text-sm text-text">
                  <span className="text-mint font-mono">{blockId}</span>
                  <span className="text-text-dim mx-1">&larr;</span>
                  <span className="text-text-dim">
                    {deps.join(', ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <p className="text-text-dim text-sm">
          Select a block from the sidebar to edit its configuration.
        </p>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="glass-panel p-3 flex flex-col items-center">
      <span className="text-2xl font-semibold text-mint">{value}</span>
      <span className="text-text-dim text-xs uppercase tracking-wide">{label}</span>
    </div>
  )
}
