import { useState } from 'react'

interface RawJsonViewerProps {
  data: unknown
  label?: string
}

export default function RawJsonViewer({ data, label }: RawJsonViewerProps) {
  const [open, setOpen] = useState(false)

  let jsonStr: string
  try {
    jsonStr = JSON.stringify(data, null, 2)
  } catch {
    jsonStr = String(data)
  }

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="text-xs text-text-dim hover:text-text cursor-pointer bg-transparent border-none flex items-center gap-1"
      >
        <span>{open ? '\u25BC' : '\u25B6'}</span>
        <span>{label || 'Raw JSON'}</span>
      </button>
      {open && (
        <pre className="mt-1 text-xs text-text font-mono bg-[#111] border border-border rounded-lg p-3 overflow-x-auto max-h-[400px] overflow-y-auto whitespace-pre-wrap">
          {jsonStr}
        </pre>
      )}
    </div>
  )
}
