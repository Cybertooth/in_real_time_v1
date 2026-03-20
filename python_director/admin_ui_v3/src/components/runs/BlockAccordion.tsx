import { useState } from 'react'
import type { BlockTrace } from '../../types'
import StatusDot from '../shared/StatusDot'
import Badge from '../shared/Badge'
import ContentRenderer from '../formatting/ContentRenderer'

interface BlockAccordionProps {
  blockSequence: string[]
  blockTraces: Record<string, BlockTrace>
}

export default function BlockAccordion({
  blockSequence,
  blockTraces,
}: BlockAccordionProps) {
  const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set())

  const toggle = (blockId: string) => {
    setExpandedBlocks((prev) => {
      const next = new Set(prev)
      if (next.has(blockId)) {
        next.delete(blockId)
      } else {
        next.add(blockId)
      }
      return next
    })
  }

  if (blockSequence.length === 0) {
    return (
      <div className="p-6 text-text-dim text-sm">No blocks in this run.</div>
    )
  }

  return (
    <div className="p-4 flex flex-col gap-2">
      {blockSequence.map((blockId) => {
        const trace = blockTraces[blockId]
        if (!trace) {
          return (
            <div
              key={blockId}
              className="p-3 rounded-xl bg-surface border border-border opacity-50"
            >
              <div className="flex items-center gap-2">
                <StatusDot status="pending" />
                <span className="text-sm text-text-dim">{blockId}</span>
              </div>
            </div>
          )
        }

        const isExpanded = expandedBlocks.has(blockId)
        const isPending = trace.status === 'pending'
        const isRunning = trace.status === 'running'
        const canExpand = !isPending

        const elapsed = trace.elapsed_ms
          ? `${(trace.elapsed_ms / 1000).toFixed(1)}s`
          : null

        return (
          <div
            key={blockId}
            className="rounded-xl bg-surface border border-border overflow-hidden"
          >
            {/* Header */}
            <button
              type="button"
              onClick={() => canExpand && toggle(blockId)}
              disabled={!canExpand}
              className={`w-full text-left p-3 flex items-center gap-2 ${
                canExpand
                  ? 'cursor-pointer hover:bg-surface-raised'
                  : 'cursor-default opacity-60'
              } transition-colors bg-transparent border-none`}
            >
              <StatusDot status={trace.status} />
              <span className="font-medium text-sm text-text flex-1">
                {trace.block_name}
              </span>
              <Badge variant="default">{trace.block_type}</Badge>
              <span className="text-xs text-text-dim bg-surface-raised rounded px-1.5 py-0.5">
                {trace.provider}
              </span>
              {elapsed && (
                <span className="text-xs text-text-dim">{elapsed}</span>
              )}
              {isRunning && (
                <div className="w-4 h-4 border-2 border-amber border-t-transparent rounded-full animate-spin" />
              )}
              {canExpand && (
                <span className="text-text-dim text-xs">
                  {isExpanded ? '\u25BC' : '\u25B6'}
                </span>
              )}
            </button>

            {/* Expanded content */}
            {isExpanded && (
              <div className="border-t border-border p-4 flex flex-col gap-4">
                {/* Input: resolved prompt */}
                {trace.resolved_prompt && (
                  <div>
                    <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-1">
                      Resolved Prompt
                    </span>
                    <pre className="text-sm text-text bg-[#111] rounded-lg p-3 whitespace-pre-wrap overflow-x-auto max-h-[300px] overflow-y-auto">
                      {trace.resolved_prompt}
                    </pre>
                  </div>
                )}

                {/* Input: resolved inputs */}
                {trace.resolved_inputs &&
                  Object.keys(trace.resolved_inputs).length > 0 && (
                    <div>
                      <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-1">
                        Resolved Inputs
                      </span>
                      <div className="flex flex-col gap-2">
                        {Object.entries(trace.resolved_inputs).map(
                          ([key, value]) => (
                            <div
                              key={key}
                              className="bg-[#111] rounded-lg p-3"
                            >
                              <span className="text-xs text-mint font-mono block mb-1">
                                {key}
                              </span>
                              <pre className="text-sm text-text whitespace-pre-wrap overflow-x-auto max-h-[200px] overflow-y-auto">
                                {typeof value === 'string'
                                  ? value
                                  : JSON.stringify(value, null, 2)}
                              </pre>
                            </div>
                          ),
                        )}
                      </div>
                    </div>
                  )}

                {/* Output */}
                {trace.output !== null && trace.output !== undefined && (
                  <div>
                    <span className="text-text-dim text-xs font-semibold uppercase tracking-wide block mb-1">
                      Output
                    </span>
                    <ContentRenderer
                      output={trace.output}
                      schemaName={trace.response_schema_name}
                    />
                  </div>
                )}

                {/* Error */}
                {trace.status === 'failed' && trace.error_message && (
                  <div>
                    <div className="bg-danger-soft border border-danger/30 rounded-lg p-3">
                      <span className="text-danger font-semibold text-sm block mb-1">
                        Error
                      </span>
                      <p className="text-danger text-sm">
                        {trace.error_message}
                      </p>
                      {trace.error_traceback && (
                        <ErrorTraceback traceback={trace.error_traceback} />
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function ErrorTraceback({ traceback }: { traceback: string }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="text-xs text-danger/70 cursor-pointer bg-transparent border-none hover:text-danger"
      >
        {open ? 'Hide traceback' : 'Show traceback'}
      </button>
      {open && (
        <pre className="mt-1 text-xs text-danger/80 bg-[#111] rounded p-2 overflow-x-auto whitespace-pre-wrap max-h-[300px] overflow-y-auto">
          {traceback}
        </pre>
      )}
    </div>
  )
}
