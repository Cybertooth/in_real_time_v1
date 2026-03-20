import { useState, type ReactNode } from 'react'

interface CollapsibleSectionProps {
  title: string
  defaultOpen?: boolean
  children: ReactNode
}

export default function CollapsibleSection({
  title,
  defaultOpen = false,
  children,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="mb-3">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full text-left py-2 cursor-pointer bg-transparent border-none"
      >
        <span
          className="text-text-dim text-xs transition-transform duration-200 inline-block"
          style={{ transform: open ? 'rotate(90deg)' : 'rotate(0deg)' }}
        >
          &#9654;
        </span>
        <span className="text-text-dim uppercase text-xs font-semibold tracking-wide">
          {title}
        </span>
      </button>
      {open && <div className="pl-4 pt-1">{children}</div>}
    </div>
  )
}
