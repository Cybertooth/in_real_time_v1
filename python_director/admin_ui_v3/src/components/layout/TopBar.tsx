import { useState } from 'react'
import { NavLink, Link } from 'react-router-dom'
import { useStore } from '../../store'
import StatusDot from '../shared/StatusDot'
import RunDialog from '../shared/RunDialog'

export default function TopBar() {
  const activeRunId = useStore((s) => s.activeRunId)
  const setSettingsOpen = useStore((s) => s.setSettingsOpen)
  const startRun = useStore((s) => s.startRun)

  const [runDialogOpen, setRunDialogOpen] = useState(false)

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-1.5 text-sm font-medium transition-colors ${
      isActive
        ? 'text-mint border-b-2 border-mint'
        : 'text-text-dim hover:text-text border-b-2 border-transparent'
    }`

  const handleRunStart = (
    seedPrompt: string,
    tags: string[],
    allowedLanguages: string[],
    options: { stagedWorkflow: boolean; deliveryProfile: 'standard' | 'on_demand' },
  ) => {
    setRunDialogOpen(false)
    startRun(
      seedPrompt || undefined,
      tags.length > 0 ? tags : undefined,
      allowedLanguages.length > 0 ? allowedLanguages : undefined,
      options,
    )
  }

  return (
    <>
      <header className="flex items-center justify-between px-6 py-3 bg-[rgba(10,10,10,0.8)] backdrop-blur-xl border-b border-border z-40 relative">
        {/* Left: Brand */}
        <div className="flex items-center gap-2">
          <span className="text-xl font-semibold text-text">Director Studio</span>
        </div>

        {/* Center: Nav */}
        <nav className="flex items-center gap-1">
          <NavLink to="/editor" className={navLinkClass}>
            Editor
          </NavLink>
          <NavLink to="/runs" className={navLinkClass}>
            Runs
          </NavLink>
          <NavLink to="/compare" className={navLinkClass}>
            Compare
          </NavLink>
          <NavLink to="/deployments" className={navLinkClass}>
            Deployments
          </NavLink>
        </nav>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          {activeRunId && (
            <Link
              to="/runs"
              className="flex items-center gap-2 text-sm text-mint no-underline"
            >
              <StatusDot status="running" />
              <span>Running...</span>
            </Link>
          )}

          <button
            type="button"
            onClick={() => setSettingsOpen(true)}
            className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
          >
            Settings
          </button>

          <button
            type="button"
            onClick={() => setRunDialogOpen(true)}
            disabled={!!activeRunId}
            className={`px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer transition-colors ${
              activeRunId
                ? 'bg-surface text-text-dim border border-border cursor-not-allowed opacity-50'
                : 'bg-mint text-black hover:brightness-110'
            }`}
          >
            Dry Run
          </button>
        </div>
      </header>

      <RunDialog
        open={runDialogOpen}
        onClose={() => setRunDialogOpen(false)}
        onStart={handleRunStart}
      />
    </>
  )
}
