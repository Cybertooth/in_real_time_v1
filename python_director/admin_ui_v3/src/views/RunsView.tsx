import { Routes, Route } from 'react-router-dom'
import RunList from '../components/runs/RunList'
import RunDetail from '../components/runs/RunDetail'

export default function RunsView() {
  return (
    <div className="h-full flex">
      {/* Left panel: Run list */}
      <div className="w-[280px] border-r border-border overflow-y-auto flex-shrink-0">
        <RunList />
      </div>

      {/* Right panel: Run detail or empty state */}
      <div className="flex-1 overflow-y-auto">
        <Routes>
          <Route path=":runId/*" element={<RunDetail />} />
          <Route
            path="*"
            element={
              <div className="h-full flex items-center justify-center text-text-dim text-sm">
                Select a run to view details
              </div>
            }
          />
        </Routes>
      </div>
    </div>
  )
}
