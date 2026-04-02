import { useEffect, useRef, useState } from 'react'

interface TextPromptDialogProps {
  open: boolean
  title: string
  description?: string
  label: string
  placeholder?: string
  confirmLabel?: string
  initialValue?: string
  submitOnEmpty?: boolean
  onConfirm: (value: string) => void
  onCancel: () => void
}

export default function TextPromptDialog({
  open,
  title,
  description,
  label,
  placeholder,
  confirmLabel = 'Save',
  initialValue = '',
  submitOnEmpty = false,
  onConfirm,
  onCancel,
}: TextPromptDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const [value, setValue] = useState(initialValue)

  useEffect(() => {
    if (open) {
      setValue(initialValue)
      dialogRef.current?.showModal()
      window.setTimeout(() => inputRef.current?.focus(), 50)
      return
    }
    dialogRef.current?.close()
  }, [initialValue, open])

  const trimmedValue = value.trim()
  const canSubmit = submitOnEmpty || trimmedValue.length > 0

  const handleConfirm = () => {
    if (!canSubmit) return
    onConfirm(trimmedValue)
  }

  return (
    <dialog
      ref={dialogRef}
      onClose={onCancel}
      className="bg-bg border border-border rounded-2xl p-0 max-w-md w-full backdrop:bg-black/70 text-text"
    >
      <div className="p-6 flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-base font-semibold text-text">{title}</h2>
          {description && (
            <p className="text-sm text-text-dim leading-relaxed">{description}</p>
          )}
        </div>

        <label className="flex flex-col gap-1.5">
          <span className="text-text-dim text-xs font-semibold uppercase tracking-wide">
            {label}
          </span>
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                handleConfirm()
              }
            }}
            placeholder={placeholder}
            className="bg-[#111] border border-border rounded-lg px-3 py-2 text-text text-sm w-full focus:border-mint outline-none"
          />
        </label>

        <div className="flex items-center gap-2 pt-1">
          <button
            type="button"
            onClick={handleConfirm}
            disabled={!canSubmit}
            className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-mint text-black hover:brightness-110 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {confirmLabel}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-surface border border-border text-text hover:bg-surface-raised transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </dialog>
  )
}
