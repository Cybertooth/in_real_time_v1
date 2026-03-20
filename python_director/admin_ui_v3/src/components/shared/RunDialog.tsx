import { useState, useEffect, useRef } from 'react'
import type { KeyboardEvent } from 'react'

interface RunDialogProps {
  open: boolean
  onClose: () => void
  onStart: (seedPrompt: string, tags: string[]) => void
}

export default function RunDialog({ open, onClose, onStart }: RunDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const [seedPrompt, setSeedPrompt] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')

  useEffect(() => {
    if (open) {
      dialogRef.current?.showModal()
    } else {
      dialogRef.current?.close()
    }
  }, [open])

  const addTag = () => {
    const trimmed = tagInput.trim()
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed])
    }
    setTagInput('')
  }

  const handleTagKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addTag()
    } else if (e.key === 'Backspace' && tagInput === '' && tags.length > 0) {
      setTags(tags.slice(0, -1))
    }
  }

  const handleStart = () => {
    onStart(seedPrompt.trim(), tags)
    setSeedPrompt('')
    setTags([])
    setTagInput('')
  }

  const handleClose = () => {
    onClose()
  }

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      className="bg-bg border border-border rounded-2xl p-0 max-w-lg w-full backdrop:bg-black/60 text-text"
    >
      <div className="p-6 flex flex-col gap-5">
        <div>
          <h2 className="text-lg font-semibold text-text">Start Dry Run</h2>
          <p className="text-xs text-text-dim mt-1">
            Optionally steer the story with a seed prompt and genre tags.
          </p>
        </div>

        <label className="flex flex-col gap-1.5">
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
            Seed Prompt
          </span>
          <textarea
            value={seedPrompt}
            onChange={(e) => setSeedPrompt(e.target.value)}
            placeholder="e.g. A missing detective whose own cold case resurfaces the night before her retirement…"
            rows={4}
            className="bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none resize-none"
          />
          <p className="text-text-dim text-xs">
            This will be injected into the creative brainstorm prompt to steer the story.
          </p>
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
            Category Tags
          </span>
          <div className="bg-[#111] border border-border rounded-lg px-3 py-2 flex flex-wrap gap-2 min-h-[42px] focus-within:border-mint">
            {tags.map((tag) => (
              <span
                key={tag}
                className="flex items-center gap-1 bg-mint/10 text-mint text-xs font-semibold px-2 py-0.5 rounded-full"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => setTags(tags.filter((t) => t !== tag))}
                  className="text-mint/60 hover:text-mint cursor-pointer bg-transparent border-none text-sm leading-none"
                >
                  ×
                </button>
              </span>
            ))}
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={handleTagKeyDown}
              onBlur={addTag}
              placeholder={tags.length === 0 ? 'Add tags (Enter to confirm)…' : ''}
              className="bg-transparent text-text text-sm outline-none flex-1 min-w-[120px]"
            />
          </div>
          <p className="text-text-dim text-xs">
            e.g. police-thriller, domestic-drama, workplace-intrigue
          </p>
        </label>

        <div className="flex items-center gap-2 mt-1">
          <button
            type="button"
            onClick={handleStart}
            className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-mint text-black hover:brightness-110 transition-colors"
          >
            Start Run
          </button>
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </dialog>
  )
}
