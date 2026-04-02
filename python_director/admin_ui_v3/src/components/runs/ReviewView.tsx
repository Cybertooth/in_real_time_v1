import { useState } from 'react'
import * as api from '../../api'
import type { HookSimulationReport, RunResult, StoryQAReport } from '../../types'
import HookReadinessCard from './HookReadinessCard'
import QaReviewCard from './QaReviewCard'

interface ReviewViewProps {
  runId: string
  canGenerate: boolean
  hookSimulation?: HookSimulationReport | null
  qaReport?: StoryQAReport | null
  onUpdate: (patch: Partial<RunResult>) => void
  onToast: (message: string, isError?: boolean) => void
}

export default function ReviewView({
  runId,
  canGenerate,
  hookSimulation,
  qaReport,
  onUpdate,
  onToast,
}: ReviewViewProps) {
  const [generatingHook, setGeneratingHook] = useState(false)
  const [generatingQa, setGeneratingQa] = useState(false)

  const refreshRun = async () => {
    const run = await api.getRun(runId)
    onUpdate({
      hook_simulation: run.hook_simulation ?? null,
      qa_report: run.qa_report ?? null,
    })
  }

  const handleGenerateHook = async () => {
    setGeneratingHook(true)
    try {
      await api.generateHookSimulation(runId)
      await refreshRun()
      onToast('Hook readiness report updated.')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate hook report'
      onToast(message, true)
    } finally {
      setGeneratingHook(false)
    }
  }

  const handleGenerateQa = async () => {
    setGeneratingQa(true)
    try {
      await api.generateStoryQa(runId)
      await refreshRun()
      onToast('QA report updated.')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate QA report'
      onToast(message, true)
    } finally {
      setGeneratingQa(false)
    }
  }

  return (
    <div className="p-4 flex flex-col gap-4">
      <HookReadinessCard
        report={hookSimulation}
        generating={generatingHook}
        canGenerate={canGenerate}
        onGenerate={handleGenerateHook}
      />
      <QaReviewCard
        report={qaReport}
        generating={generatingQa}
        canGenerate={canGenerate}
        onGenerate={handleGenerateQa}
      />
    </div>
  )
}
