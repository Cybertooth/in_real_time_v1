import { useStore } from '../../store'

export default function PipelineMeta() {
  const pipeline = useStore((s) => s.pipeline)
  const updatePipelineMeta = useStore((s) => s.updatePipelineMeta)
  const providerModels = useStore((s) => s.providerModels)

  if (!pipeline) return null

  const geminiModels = providerModels['GEMINI'] || []
  const openaiModels = providerModels['OPENAI'] || []
  const anthropicModels = providerModels['ANTHROPIC'] || []

  return (
    <div className="glass-panel p-4 flex flex-col gap-3">
      <label className="flex flex-col gap-1">
        <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
          Pipeline Name
        </span>
        <input
          type="text"
          value={pipeline.name}
          onChange={(e) => updatePipelineMeta({ name: e.target.value })}
          className="bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none"
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
          Description
        </span>
        <input
          type="text"
          value={pipeline.description}
          onChange={(e) => updatePipelineMeta({ description: e.target.value })}
          className="bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none"
        />
      </label>

      <div className="mt-1">
        <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-2">
          Pipeline Defaults
        </span>

        <label className="flex flex-col gap-1 mb-2">
          <span className="text-text-dim text-xs">Gemini Default Model</span>
          <select
            value={pipeline.default_models['GEMINI'] || ''}
            onChange={(e) =>
              updatePipelineMeta({
                default_models: { ...pipeline.default_models, GEMINI: e.target.value },
              })
            }
            className="bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none"
          >
            <option value="">-- select --</option>
            {geminiModels.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 mb-2">
          <span className="text-text-dim text-xs">OpenAI Default Model</span>
          <select
            value={pipeline.default_models['OPENAI'] || ''}
            onChange={(e) =>
              updatePipelineMeta({
                default_models: { ...pipeline.default_models, OPENAI: e.target.value },
              })
            }
            className="bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none"
          >
            <option value="">-- select --</option>
            {openaiModels.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-text-dim text-xs">Anthropic Default Model</span>
          <select
            value={pipeline.default_models['ANTHROPIC'] || ''}
            onChange={(e) =>
              updatePipelineMeta({
                default_models: { ...pipeline.default_models, ANTHROPIC: e.target.value },
              })
            }
            className="bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none"
          >
            <option value="">-- select --</option>
            {anthropicModels.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  )
}
