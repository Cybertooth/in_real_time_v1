import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useStore } from './store'
import TopBar from './components/layout/TopBar'
import Sidebar from './components/layout/Sidebar'
import Toast from './components/layout/Toast'
import SettingsDialog from './components/shared/SettingsDialog'
import EditorView from './views/EditorView'
import RunsView from './views/RunsView'
import CompareView from './views/CompareView'
import DeploymentsView from './views/DeploymentsView'

export default function App() {
  const loadStudio = useStore(s => s.loadStudio)
  const bootstrapError = useStore(s => s.bootstrapError)
  const studio = useStore(s => s.studio)

  useEffect(() => { loadStudio() }, [loadStudio])

  if (bootstrapError) {
    return (
      <div className="h-full flex items-center justify-center flex-col gap-4">
        <div className="bg-glow" />
        <p className="text-danger text-lg font-semibold">Cannot reach Director Studio backend.</p>
        <p className="text-text-dim">Is the server running on port 8001?</p>
        <button onClick={loadStudio} className="px-5 py-2 bg-surface border border-border rounded-xl text-text hover:bg-surface-raised transition-colors cursor-pointer">
          Retry
        </button>
      </div>
    )
  }

  if (!studio) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="bg-glow" />
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-mint border-t-transparent rounded-full animate-spin" />
          <p className="text-text-dim text-sm">Loading Director Studio...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="bg-glow" />
      <TopBar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/editor" element={<EditorView />} />
            <Route path="/runs/*" element={<RunsView />} />
            <Route path="/compare" element={<CompareView />} />
            <Route path="/deployments" element={<DeploymentsView />} />
            <Route path="*" element={<Navigate to="/editor" replace />} />
          </Routes>
        </main>
      </div>
      <Toast />
      <SettingsDialog />
    </div>
  )
}
