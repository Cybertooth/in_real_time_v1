import { useEffect, useState } from 'react'
import { useParams, NavLink, Routes, Route, Navigate } from 'react-router-dom'
import { useStore } from '../../store'
import * as api from '../../api'
import type { RunProgress } from '../../types'
import Badge from '../shared/Badge'
import BlockAccordion from './BlockAccordion'
import TimelineView from './TimelineView'
import ExperiencePreview from './ExperiencePreview'

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const showToast = useStore((s) => s.showToast)
  const activeRunProgress = useStore((s) => s.activeRunProgress)
  const activeRunId = useStore((s) => s.activeRunId)

  const [runData, setRunData] = useState<RunProgress | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!runId) return

    // If this is the active run, use the live progress
    if (runId === activeRunId && activeRunProgress) {
      setRunData(activeRunProgress)
      setLoading(false)
      return
    }

    setLoading(true)
    api
      .getRunStatus(runId)
      .then((data) => {
        setRunData(data)
        setLoading(false)
      })
      .catch((err) => {
        const msg = err instanceof Error ? err.message : 'Failed to load run'
        showToast(msg, true)
        setLoading(false)
      })
  }, [runId, activeRunId, activeRunProgress, showToast])

  // Keep syncing with active run progress
  useEffect(() => {
    if (runId === activeRunId && activeRunProgress) {
      setRunData(activeRunProgress)
    }
  }, [runId, activeRunId, activeRunProgress])

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-mint border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!runData) {
    return (
      <div className="h-full flex items-center justify-center text-text-dim text-sm">
        Run not found
      </div>
    )
  }

  const statusVariant = () => {
    switch (runData.status) {
      case 'succeeded':
        return 'success' as const
      case 'failed':
        return 'error' as const
      case 'running':
        return 'warning' as const
      default:
        return 'default' as const
    }
  }

  const formatTime = (ts: string | null) => {
    if (!ts) return '--'
    try {
      return new Date(ts).toLocaleString()
    } catch {
      return ts
    }
  }

  const handleUpload = async () => {
    if (!runId) return
    if (!window.confirm('Upload this run to the production system?')) return
    try {
      const result = await api.uploadRun(runId)
      showToast(`Uploaded! Story ID: ${result.story_id}`)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      showToast(msg, true)
    }
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-1.5 text-sm font-medium transition-colors ${
      isActive
        ? 'text-mint border-b-2 border-mint'
        : 'text-text-dim hover:text-text border-b-2 border-transparent'
    }`

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-text">
            {runData.final_title || runData.pipeline_name}
          </h2>
          <Badge variant={statusVariant()}>{runData.status}</Badge>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-text-dim">
            {formatTime(runData.started_at)}
          </span>
          {runData.status === 'succeeded' && (
            <button
              type="button"
              onClick={handleUpload}
              className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-mint text-black hover:brightness-110 transition-colors"
            >
              Upload
            </button>
          )}
        </div>
      </div>

      {/* Sub-tab navigation */}
      <nav className="flex items-center gap-1 px-4 border-b border-border">
        <NavLink to={`/runs/${runId}/blocks`} className={navLinkClass}>
          Blocks
        </NavLink>
        <NavLink to={`/runs/${runId}/timeline`} className={navLinkClass}>
          Timeline
        </NavLink>
        <NavLink to={`/runs/${runId}/experience`} className={navLinkClass}>
          Experience
        </NavLink>
      </nav>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <Routes>
          <Route
            path="blocks"
            element={
              <BlockAccordion
                blockSequence={runData.block_sequence}
                blockTraces={runData.block_traces}
              />
            }
          />
          <Route
            path="timeline"
            element={<TimelineView timeline={runData.timeline} />}
          />
          <Route
            path="experience"
            element={<ExperiencePreview timeline={runData.timeline} />}
          />
          <Route path="*" element={<Navigate to="blocks" replace />} />
        </Routes>
      </div>
    </div>
  )
}
