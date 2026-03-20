import { useState, useRef } from 'react'
import { useStore } from '../../store'
import CollapsibleSection from '../shared/CollapsibleSection'
import Badge from '../shared/Badge'

export default function BlockInspector() {
  const pipeline = useStore((s) => s.pipeline)
  const selectedBlockId = useStore((s) => s.selectedBlockId)
  const updateBlock = useStore((s) => s.updateBlock)
  const updateBlockConfig = useStore((s) => s.updateBlockConfig)
  const renameBlockId = useStore((s) => s.renameBlockId)
  const moveBlock = useStore((s) => s.moveBlock)
  const duplicateBlock = useStore((s) => s.duplicateBlock)
  const deleteBlock = useStore((s) => s.deleteBlock)
  const schemas = useStore((s) => s.schemas)
  const providerModels = useStore((s) => s.providerModels)

  const [editingId, setEditingId] = useState('')
  const idInputRef = useRef<HTMLInputElement>(null)

  if (!pipeline || !selectedBlockId) return null
  const block = pipeline.blocks.find((b) => b.id === selectedBlockId)
  if (!block) return null

  const provider = block.config.provider
  const models = providerModels[provider] || []
  const usePipelineDefault = block.config.use_pipeline_default_model
  const defaultModel = pipeline.default_models[provider] || ''

  const handleIdBlur = () => {
    const newId = editingId.trim()
    if (newId && newId !== block.id) {
      const exists = pipeline.blocks.some((b) => b.id === newId && b.id !== block.id)
      if (!exists) {
        renameBlockId(block.id, newId)
      }
    }
    setEditingId('')
  }

  const inputClass =
    'bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none'
  const selectClass = inputClass

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-text">Block Inspector</h2>
        <button
          type="button"
          onClick={() => useStore.getState().selectBlock(null)}
          className="text-text-dim text-sm hover:text-text cursor-pointer bg-transparent border-none"
        >
          Close
        </button>
      </div>

      {/* Identity */}
      <CollapsibleSection title="Identity" defaultOpen>
        <div className="flex flex-col gap-3">
          <label className="flex flex-col gap-1">
            <span className="text-text-dim text-xs">Block ID</span>
            <input
              ref={idInputRef}
              type="text"
              defaultValue={block.id}
              onFocus={() => setEditingId(block.id)}
              onChange={(e) => setEditingId(e.target.value)}
              onBlur={handleIdBlur}
              className={inputClass}
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-text-dim text-xs">Block Name</span>
            <input
              type="text"
              value={block.name}
              onChange={(e) => updateBlock(block.id, { name: e.target.value })}
              className={inputClass}
            />
          </label>

          <div className="flex items-center gap-2">
            <span className="text-text-dim text-xs">Type:</span>
            <Badge variant="default">{block.type}</Badge>
          </div>
        </div>
      </CollapsibleSection>

      {/* Execution Config */}
      <CollapsibleSection title="Execution Config" defaultOpen>
        <div className="flex flex-col gap-3">
          <label className="flex flex-col gap-1">
            <span className="text-text-dim text-xs">Enabled</span>
            <select
              value={block.enabled ? 'true' : 'false'}
              onChange={(e) =>
                updateBlock(block.id, { enabled: e.target.value === 'true' })
              }
              className={selectClass}
            >
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-text-dim text-xs">Provider</span>
            <select
              value={provider}
              onChange={(e) =>
                updateBlockConfig(block.id, {
                  provider: e.target.value as 'GEMINI' | 'OPENAI' | 'ANTHROPIC' | 'OPENROUTER',
                  model_name: null,
                })
              }
              className={selectClass}
            >
              {Object.keys(providerModels).map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-text-dim text-xs">Model Source</span>
            <select
              value={usePipelineDefault ? 'default' : 'custom'}
              onChange={(e) =>
                updateBlockConfig(block.id, {
                  use_pipeline_default_model: e.target.value === 'default',
                })
              }
              className={selectClass}
            >
              <option value="default">Pipeline Default</option>
              <option value="custom">Custom Override</option>
            </select>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-text-dim text-xs">Model</span>
            <input
              type="text"
              list={`models-${block.id}`}
              value={usePipelineDefault ? defaultModel : block.config.model_name || ''}
              disabled={usePipelineDefault}
              onChange={(e) =>
                updateBlockConfig(block.id, { model_name: e.target.value })
              }
              className={`${inputClass} ${usePipelineDefault ? 'opacity-50 cursor-not-allowed' : ''}`}
            />
            <datalist id={`models-${block.id}`}>
              {models.map((m) => (
                <option key={m} value={m} />
              ))}
            </datalist>
            {usePipelineDefault && (
              <span className="text-text-dim text-xs mt-0.5">
                Using pipeline default: {defaultModel || '(not set)'}
              </span>
            )}
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-text-dim text-xs">Temperature</span>
            <input
              type="number"
              min={0}
              max={2}
              step={0.1}
              value={block.config.temperature}
              onChange={(e) =>
                updateBlockConfig(block.id, {
                  temperature: parseFloat(e.target.value) || 0,
                })
              }
              className={inputClass}
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-text-dim text-xs">Response Schema</span>
            <select
              value={block.config.response_schema_name || ''}
              onChange={(e) =>
                updateBlockConfig(block.id, {
                  response_schema_name: e.target.value || null,
                })
              }
              className={selectClass}
            >
              <option value="">None</option>
              {schemas.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
        </div>
      </CollapsibleSection>

      {/* System Instruction */}
      <CollapsibleSection title="System Instruction">
        <textarea
          value={block.config.system_instruction}
          onChange={(e) =>
            updateBlockConfig(block.id, { system_instruction: e.target.value })
          }
          className={`${inputClass} font-mono min-h-[100px] resize-y`}
        />
      </CollapsibleSection>

      {/* Prompt Template */}
      <CollapsibleSection title="Prompt Template" defaultOpen>
        <textarea
          value={block.config.prompt_template}
          onChange={(e) =>
            updateBlockConfig(block.id, { prompt_template: e.target.value })
          }
          className={`${inputClass} font-mono min-h-[200px] resize-y`}
        />
      </CollapsibleSection>

      {/* Dependencies */}
      <CollapsibleSection title="Dependencies">
        <div className="flex flex-col gap-1">
          {pipeline.blocks
            .filter((b) => b.id !== block.id)
            .map((b) => (
              <label key={b.id} className="flex items-center gap-2 text-sm text-text">
                <input
                  type="checkbox"
                  checked={block.input_blocks.includes(b.id)}
                  onChange={(e) => {
                    const newDeps = e.target.checked
                      ? [...block.input_blocks, b.id]
                      : block.input_blocks.filter((id) => id !== b.id)
                    updateBlock(block.id, { input_blocks: newDeps })
                  }}
                  className="accent-mint"
                />
                <span>{b.name}</span>
                <span className="text-text-dim text-xs">({b.id})</span>
              </label>
            ))}
          {pipeline.blocks.length <= 1 && (
            <p className="text-text-dim text-sm">No other blocks available</p>
          )}
        </div>
      </CollapsibleSection>

      {/* Actions */}
      <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border">
        <button
          type="button"
          onClick={() => moveBlock(block.id, 'up')}
          className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
        >
          Move Up
        </button>
        <button
          type="button"
          onClick={() => moveBlock(block.id, 'down')}
          className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
        >
          Move Down
        </button>
        <button
          type="button"
          onClick={() => duplicateBlock(block.id)}
          className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
        >
          Duplicate
        </button>
        <button
          type="button"
          onClick={() => {
            if (window.confirm(`Delete block "${block.name}"?`)) {
              deleteBlock(block.id)
            }
          }}
          className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-danger-soft text-danger border border-danger/30 hover:brightness-110 transition-colors"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
