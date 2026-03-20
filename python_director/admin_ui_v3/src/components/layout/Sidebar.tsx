import { useState, useCallback, useRef, useEffect } from 'react'
import { useStore } from '../../store'
import * as api from '../../api'
import PipelineMeta from '../pipeline/PipelineMeta'
import PipelineLibrary from '../pipeline/PipelineLibrary'
import BlockList from '../pipeline/BlockList'
import TemplateRail from '../pipeline/TemplateRail'

const MIN_WIDTH = 260
const MAX_WIDTH = 800
const DEFAULT_WIDTH = 420

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const [width, setWidth] = useState(() => {
    const saved = localStorage.getItem('sidebar-width')
    const parsed = saved ? parseInt(saved, 10) : NaN
    return Number.isFinite(parsed) ? Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, parsed)) : DEFAULT_WIDTH
  })
  const dragging = useRef(false)
  const savePipeline = useStore((s) => s.savePipeline)
  const pipeline = useStore((s) => s.pipeline)
  const showToast = useStore((s) => s.showToast)
  const loadStudio = useStore((s) => s.loadStudio)

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    dragging.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [])

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return
      const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, e.clientX))
      setWidth(newWidth)
    }
    const onMouseUp = () => {
      if (!dragging.current) return
      dragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      setWidth((w) => {
        localStorage.setItem('sidebar-width', String(w))
        return w
      })
    }
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
    }
  }, [])

  const handleSnapshot = async () => {
    if (!pipeline) return
    try {
      const label = window.prompt('Snapshot label (optional):')
      await api.snapshotPipeline(pipeline, label || undefined)
      showToast('Snapshot saved')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to snapshot'
      showToast(msg, true)
    }
  }

  const handleReset = async () => {
    if (!window.confirm('Reset pipeline to defaults? This cannot be undone.')) return
    try {
      const p = await api.resetPipeline()
      useStore.getState().setPipeline(p)
      showToast('Pipeline reset to defaults')
      loadStudio()
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to reset'
      showToast(msg, true)
    }
  }

  if (collapsed) {
    return (
      <div className="w-[50px] border-r border-border bg-[rgba(255,255,255,0.02)] flex flex-col items-center pt-3 flex-shrink-0">
        <button
          type="button"
          onClick={() => setCollapsed(false)}
          className="w-8 h-8 rounded-lg bg-surface border border-border text-text-dim text-xs cursor-pointer hover:bg-surface-raised flex items-center justify-center"
          title="Expand sidebar"
        >
          &#9654;
        </button>
      </div>
    )
  }

  return (
    <div className="relative flex flex-shrink-0" style={{ width }}>
      {/* Main sidebar content */}
      <div className="flex-1 border-r border-border bg-[rgba(255,255,255,0.02)] flex flex-col min-w-0">
        {/* Collapse toggle */}
        <div className="flex items-center justify-end px-3 pt-3 pb-1">
          <button
            type="button"
            onClick={() => setCollapsed(true)}
            className="w-8 h-8 rounded-lg bg-surface border border-border text-text-dim text-xs cursor-pointer hover:bg-surface-raised flex items-center justify-center"
            title="Collapse sidebar"
          >
            &#9664;
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-3 pb-3 flex flex-col gap-3">
          <PipelineMeta />
          <PipelineLibrary />
          <BlockList />
          <TemplateRail />
        </div>

        {/* Action buttons */}
        <div className="flex flex-col gap-2 p-3 border-t border-border">
          <button
            type="button"
            onClick={() => savePipeline()}
            className="w-full px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-mint text-black hover:brightness-110 transition-colors"
          >
            Save Design
          </button>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleSnapshot}
              className="flex-1 px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
            >
              Snapshot
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="flex-1 px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-danger-soft text-danger border border-danger/30 hover:brightness-110 transition-colors"
            >
              Reset Default
            </button>
          </div>
        </div>
      </div>

      {/* Drag handle */}
      <div
        onMouseDown={onMouseDown}
        className="absolute top-0 right-0 w-[5px] h-full cursor-col-resize z-10 group"
      >
        <div className="w-[1px] h-full mx-auto bg-transparent group-hover:bg-mint/40 transition-colors" />
      </div>
    </div>
  )
}
