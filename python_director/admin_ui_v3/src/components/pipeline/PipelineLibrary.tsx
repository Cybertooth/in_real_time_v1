import { useState } from 'react'
import { useStore } from '../../store'
import * as api from '../../api'

export default function PipelineLibrary() {
  const pipeline = useStore((s) => s.pipeline)
  const pipelineCatalog = useStore((s) => s.pipelineCatalog)
  const setPipeline = useStore((s) => s.setPipeline)
  const setPipelineCatalog = useStore((s) => s.setPipelineCatalog)
  const showToast = useStore((s) => s.showToast)
  const loadStudio = useStore((s) => s.loadStudio)

  const [selectedKey, setSelectedKey] = useState('')

  const handleLoad = async () => {
    if (!selectedKey) return
    try {
      const result = await api.loadNamedPipeline(selectedKey, true)
      setPipeline(result.pipeline)
      setPipelineCatalog(result.pipeline_catalog)
      showToast('Pipeline loaded')
      loadStudio()
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load pipeline'
      showToast(msg, true)
    }
  }

  const handleSaveAs = async () => {
    if (!pipeline) return
    const name = window.prompt('Save pipeline as:')
    if (!name) return
    try {
      const result = await api.saveNamedPipeline(name, pipeline, true)
      setPipeline(result.pipeline)
      setPipelineCatalog(result.pipeline_catalog)
      showToast(`Pipeline saved as "${name}"`)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to save pipeline'
      showToast(msg, true)
    }
  }

  const handleDelete = async () => {
    if (!selectedKey) return
    if (!window.confirm(`Delete pipeline "${selectedKey}"? This cannot be undone.`)) return
    try {
      const result = await api.deleteNamedPipeline(selectedKey)
      setPipelineCatalog(result.pipeline_catalog)
      setSelectedKey('')
      showToast('Pipeline deleted')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to delete pipeline'
      showToast(msg, true)
    }
  }

  return (
    <div className="glass-panel p-4 flex flex-col gap-3">
      <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
        Saved Pipelines
      </span>

      <select
        value={selectedKey}
        onChange={(e) => setSelectedKey(e.target.value)}
        className="bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none"
      >
        {pipelineCatalog.length === 0 ? (
          <option value="">No saved pipelines</option>
        ) : (
          <>
            <option value="">-- select pipeline --</option>
            {pipelineCatalog.map((item) => (
              <option key={item.key} value={item.key}>
                {item.name} ({item.block_count} blocks)
              </option>
            ))}
          </>
        )}
      </select>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleLoad}
          disabled={!selectedKey}
          className="flex-1 px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Load
        </button>
        <button
          type="button"
          onClick={handleSaveAs}
          className="flex-1 px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
        >
          Save As
        </button>
        <button
          type="button"
          onClick={handleDelete}
          disabled={!selectedKey}
          className="flex-1 px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-danger-soft text-danger border border-danger/30 hover:brightness-110 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
