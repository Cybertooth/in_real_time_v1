import { useEffect, useRef } from 'react'

interface ConfirmDialogProps {
  open: boolean
  title: string
  description: string
  confirmLabel?: string
  confirmVariant?: 'danger' | 'primary'
  onConfirm: () => void
  onCancel: () => void
  children?: React.ReactNode
}

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  confirmVariant = 'primary',
  onConfirm,
  onCancel,
  children,
}: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    if (open) {
      dialogRef.current?.showModal()
    } else {
      dialogRef.current?.close()
    }
  }, [open])

  const confirmClass =
    confirmVariant === 'danger'
      ? 'px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-danger-soft text-danger border border-danger/30 hover:brightness-110 transition-colors'
      : 'px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer bg-mint text-black hover:brightness-110 transition-colors'

  return (
    <dialog
      ref={dialogRef}
      onClose={onCancel}
      className="bg-bg border border-border rounded-2xl p-0 max-w-sm w-full backdrop:bg-black/70 text-text"
    >
      <div className="p-6 flex flex-col gap-4">
        <h2 className="text-base font-semibold text-text">{title}</h2>
        <p className="text-sm text-text-dim leading-relaxed">{description}</p>
        {children}
        <div className="flex items-center gap-2 pt-1">
          <button type="button" onClick={onConfirm} className={confirmClass}>
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
